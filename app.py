from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, BonusProgram, Shop, ShopProgramRate, ScrapeLog, User, Proposal, ProposalVote, ProposalAuditTrail, ContributorRequest, Coupon
from datetime import datetime
from job_queue import job_queue
import bonus_programs.miles_and_more as mam
import bonus_programs.payback as pb
import bonus_programs.shoop as sh
import shops.example_shop as exs
import scrapers.example_scraper as exs_scraper
import scrapers.payback_scraper_js as pb_scraper
import os

app = Flask(__name__)

# Configuration from environment variables
# Ensure absolute path for DATABASE_URL
default_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'shopping_points.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{default_db_path}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'

# Debug: Print database path
print(f"📂 Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize database tables on startup (safe for multiple workers)
def init_db():
    """Initialize database tables if they don't exist"""
    try:
        with app.app_context():
            # Create tables if they don't exist
            # Note: db.create_all() with SQLite can have race conditions with multiple workers
            # We catch the exception if tables already exist
            try:
                db.create_all()
                print("✅ Database tables initialized")
            except Exception as e:
                # Tables might already exist from another worker - this is OK
                if "already exists" in str(e):
                    print("ℹ️  Database tables already exist")
                else:
                    raise
            
            # Check if we have any bonus programs (indicator of first run)
            try:
                bonus_count = BonusProgram.query.count()
                if bonus_count == 0:
                    # Fresh database - register initial data
                    print("📦 Seeding initial bonus programs...")
                    import bonus_programs.miles_and_more as mam
                    import bonus_programs.payback as pb
                    import bonus_programs.shoop as sh
                    import shops.example_shop as exs
                    mam.register()
                    pb.register()
                    sh.register()
                    exs.register()
                    print("✅ Initial bonus programs seeded successfully")
                else:
                    print(f"ℹ️  Database already has {bonus_count} bonus programs")
            except Exception as e:
                print(f"⚠️  Could not seed initial data: {e}")
            
            # Create admin user if it doesn't exist
            admin_password = os.environ.get('ADMIN_PASSWORD')
            if admin_password:
                try:
                    admin = User.query.filter_by(username='admin').first()
                    if not admin:
                        print("👤 Creating admin user...")
                        admin = User(
                            username='admin',
                            email='admin@localhost',
                            role='admin'  # lowercase!
                        )
                        admin.set_password(admin_password)
                        db.session.add(admin)
                        db.session.commit()
                        print("✅ Admin user created successfully (username: admin)")
                    else:
                        print("ℹ️  Admin user already exists")
                except Exception as e:
                    # Might fail if another worker already created it
                    db.session.rollback()
                    if "UNIQUE constraint failed" in str(e):
                        print("ℹ️  Admin user already created by another worker")
                    else:
                        print(f"⚠️  Admin user creation skipped: {e}")
            else:
                print("⚠️  ADMIN_PASSWORD not set in environment - skipping admin user creation")
    except Exception as e:
        # Only fail critically if it's not a "table exists" error
        if "already exists" not in str(e):
            print(f"❌ CRITICAL: Database initialization failed: {e}")
            import traceback
            traceback.print_exc()
            raise
        else:
            print("ℹ️  Database initialization handled by another worker")

# Initialize on import
init_db()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def ensure_seed():
    with app.app_context():
        db.create_all()
        mam.register()
        pb.register()
        sh.register()
        exs.register()


# ============ JOB QUEUE SCRAPER FUNCTIONS ============

def scrape_example(job):
    """Background job for example scraper"""
    with app.app_context():
        job.add_message('Starte Example-Scraper...')
        job.set_progress(10, 100)
        
        ScrapeLogEntry = ScrapeLog
        start = datetime.utcnow()
        db.session.add(ScrapeLogEntry(message='Example scraper started'))
        db.session.commit()
        
        job.add_message('Fetche Daten...')
        job.set_progress(30, 100)
        
        before_shops = Shop.query.count()
        scraper = exs_scraper.ExampleScraper()
        data = scraper.fetch()
        
        job.add_message('Registriere Daten in Datenbank...')
        job.set_progress(60, 100)
        
        scraper.register_to_db(data)
        after_shops = Shop.query.count()
        added = after_shops - before_shops
        
        end = datetime.utcnow()
        job.add_message(f'Fertig: {added} Shops hinzugefügt')
        db.session.add(ScrapeLogEntry(message=f'Example scraper finished, added {added} shops'))
        db.session.commit()
        
        job.set_progress(100, 100)
        return {'added': added}


def scrape_payback(job):
    """Background job for Payback scraper"""
    with app.app_context():
        job.add_message('Starte Payback-Scraper...')
        job.set_progress(10, 100)
        
        db.session.add(ScrapeLog(message='Payback scraper started'))
        db.session.commit()
        
        job.add_message('Fetche Partner von Payback...')
        job.set_progress(30, 100)
        
        s = pb_scraper.PaybackScraperJS()
        try:
            partners, debug = s.fetch()
        except Exception as e:
            job.add_message(f'Fehler beim Fetchen: {e}')
            db.session.add(ScrapeLog(message=f'Payback scraper error: {e}'))
            db.session.commit()
            raise
        
        # log debug info
        job.add_message(f"Gefunden: {debug.get('partners_found')} Partner")
        db.session.add(ScrapeLog(message=f"Payback fetch: status={debug.get('status_code')}, partners={debug.get('partners_found')}"))
        db.session.commit()
        
        job.add_message('Registriere Daten...')
        job.set_progress(50, 100)
        
        before_shops = set([sh.name for sh in Shop.query.all()])
        added_names = []
        notes = []
        zero_rate_count = 0
        
        if partners:
            for idx, p in enumerate(partners):
                job.set_progress(50 + int((idx / len(partners)) * 40), 100)
                
                rate = p['rate']
                
                # If rate has 0 points, use fallback
                if rate.get('points_per_eur', 0) == 0 and rate.get('cashback_pct', 0) == 0:
                    # Check if there's an incentive text
                    if 'incentive_text' in rate and rate['incentive_text']:
                        # Use a neutral fallback rate so shop is visible
                        rate['points_per_eur'] = 1.0  # Default fallback
                        zero_rate_count += 1
                    else:
                        # Skip rates with no data at all
                        continue
                
                data = {
                    'name': p['name'],
                    'rates': [rate]
                }
                
                # record note if per-completion points present
                if 'per_completion_points' in rate:
                    note = f"{p['name']}: {rate['per_completion_points']} Punkte pro Abschluss"
                    notes.append(note)
                
                s.register_to_db(data)
                added_names.append(p['name'])
        
        after_shops = set([sh.name for sh in Shop.query.all()])
        new_shops = sorted(list(after_shops - before_shops))
        added = len(new_shops)
        
        # log summary
        summary = f'Payback scraper finished, added {added} shops'
        job.add_message(f'Fertig: {added} neue Shops' + (f', {zero_rate_count} mit Fallback-Rate' if zero_rate_count > 0 else ''))
        db.session.add(ScrapeLog(message=summary))
        db.session.commit()
        
        # add detailed log of first 20 added shops
        if new_shops:
            detail = ', '.join(new_shops[:20]) + (', ...' if len(new_shops) > 20 else '')
            db.session.add(ScrapeLog(message=f'Added shops: {detail}'))
        db.session.commit()
        
        # log any notes (per-completion incentives)
        for n in notes[:50]:
            db.session.add(ScrapeLog(message=f'Note: {n}'))
        db.session.commit()
        
        job.set_progress(100, 100)
        return {'added': added, 'notes': len(notes)}


def scrape_miles_and_more(job):
    """Background job for Miles & More scraper"""
    with app.app_context():
        job.add_message('Starte Miles & More-Scraper...')
        job.set_progress(10, 100)
        
        start = datetime.utcnow()
        db.session.add(ScrapeLog(message='Miles & More scraper started'))
        db.session.commit()
        
        from scrapers.miles_and_more_scraper import MilesAndMoreScraper
        
        try:
            job.add_message('Öffne Miles & More Website...')
            job.set_progress(20, 100)
            
            scraper = MilesAndMoreScraper()
            job.add_message('Scrape Daten...')
            job.set_progress(40, 100)
            
            added, updated, errors = scraper.scrape()
            
            job.add_message(f'Verarbeitet: {added} neue, {updated} aktualisiert')
            job.set_progress(80, 100)
        except Exception as e:
            job.add_message(f'Fehler: {e}')
            db.session.rollback()
            db.session.add(ScrapeLog(message=f'Miles & More scraper error: {e}'))
            db.session.commit()
            raise
        
        end = datetime.utcnow()
        summary = f'Miles & More scraper finished, added {added} shops, updated {updated}, errors {len(errors)}'
        db.session.add(ScrapeLog(message=summary))
        db.session.commit()
        
        # Log errors
        for error in errors[:50]:
            db.session.add(ScrapeLog(message=f'Error: {error}'))
        db.session.commit()
        
        job.add_message('Fertig!')
        job.set_progress(100, 100)
        return {'added': added, 'updated': updated, 'errors': len(errors)}


@app.route('/', methods=['GET'])
def index():
    shops = Shop.query.all()
    
    # Für jeden Shop berechnen, welche Modi er unterstützt
    shops_data = []
    for shop in shops:
        rates = ShopProgramRate.query.filter_by(shop_id=shop.id, valid_to=None).all()
        # Ein Shop unterstützt "shopping" und "voucher", wenn er Raten mit points_per_eur > 0 hat
        supports_shopping_voucher = any(r.points_per_eur > 0 for r in rates)
        # Für "contract" Modus: aktuell alle Shops (könnte man später spezifizieren)
        supports_contract = True  # Alle Shops können Vertragsabschlüsse haben
        
        shops_data.append({
            'id': shop.id,
            'name': shop.name,
            'supports_shopping': supports_shopping_voucher,
            'supports_voucher': supports_shopping_voucher,
            'supports_contract': supports_contract
        })
    
    return render_template('index.html', shops_data=shops_data)


@app.route('/evaluate', methods=['POST'])
def evaluate():
    mode = request.form.get('mode')
    shop_id = int(request.form.get('shop'))
    shop = Shop.query.get(shop_id)

    # Get active coupons for this shop
    now = datetime.utcnow()
    shop_coupons = Coupon.query.filter(
        db.or_(Coupon.shop_id == shop_id, Coupon.shop_id.is_(None)),
        Coupon.status == 'active',
        Coupon.valid_from <= now,
        Coupon.valid_to >= now
    ).all()

    if mode == 'shopping':
        amount = float(request.form.get('amount') or 0)
        results = []
        # Only get currently valid rates (valid_to is NULL)
        rates = ShopProgramRate.query.filter_by(shop_id=shop.id, valid_to=None).all()
        
        for rate in rates:
            program = BonusProgram.query.get(rate.program_id)
            
            # Base calculation (without coupons)
            base_points = amount * rate.points_per_eur
            base_euros = base_points * program.point_value_eur + (amount * rate.cashback_pct/100.0)
            
            # Check for applicable coupons
            applicable_multipliers = []
            applicable_discounts = []
            has_unknown_combinability = False
            
            for coupon in shop_coupons:
                # Check if coupon applies to this program
                if coupon.program_id is None or coupon.program_id == program.id:
                    if coupon.coupon_type == 'multiplier':
                        applicable_multipliers.append(coupon)
                    elif coupon.coupon_type == 'discount':
                        applicable_discounts.append(coupon)
                    
                    if coupon.combinable is None:
                        has_unknown_combinability = True
            
            # Calculate with coupons
            coupon_info = None
            if applicable_multipliers or applicable_discounts:
                # Start with base values
                final_points = base_points
                final_amount = amount
                multiplier_names = []
                discount_names = []
                
                # Apply multipliers to points (multiply base_points)
                if applicable_multipliers:
                    for mult in applicable_multipliers:
                        if mult.combinable is False and len(applicable_multipliers) > 1:
                            continue  # Skip if not combinable and multiple exist
                        final_points = base_points * mult.value
                        multiplier_names.append(f"{mult.name} ({mult.value}x)")
                        break  # Use only first multiplier (most common case)
                
                # Apply discounts to amount (reduce spent amount)
                if applicable_discounts:
                    for disc in applicable_discounts:
                        if disc.combinable is False and len(applicable_discounts) > 1:
                            continue  # Skip if not combinable
                        final_amount = amount * (1 - disc.value / 100)
                        discount_names.append(f"{disc.name} ({disc.value}%)")
                        break  # Use only first discount
                
                # Recalculate points and euros with coupon adjustments
                # If multiplier: use multiplied points + cashback on original amount
                # If discount: use original points_per_eur on discounted amount + cashback on discounted amount
                if applicable_multipliers:
                    # Multiplier case: points are multiplied, cashback on original amount
                    coupon_euros = final_points * program.point_value_eur + (amount * rate.cashback_pct/100.0)
                else:
                    # Discount case: points based on discounted amount, cashback on discounted amount
                    final_points = final_amount * rate.points_per_eur
                    coupon_euros = final_points * program.point_value_eur + (final_amount * rate.cashback_pct/100.0)
                
                coupon_info = {
                    'euros': round(coupon_euros, 2),
                    'points': round(final_points, 2),
                    'multipliers': multiplier_names,
                    'discounts': discount_names,
                    'unknown_combinability': has_unknown_combinability
                }
            
            results.append({
                'program': program.name,
                'euros': round(base_euros, 2),
                'points': round(base_points, 2),
                'coupon_info': coupon_info
            })
        
        # Default: sort by base value (without coupon)
        results.sort(key=lambda r: r['euros'], reverse=True)
        
        # Pass both results and coupons info to template
        return render_template('result.html', mode='shopping', shop=shop, amount=amount, results=results, 
                             has_coupons=bool(shop_coupons), active_coupons=shop_coupons, sort_by='base')

    elif mode == 'voucher':
        voucher = float(request.form.get('voucher') or 0)
        results = []
        # Only get currently valid rates
        rates = ShopProgramRate.query.filter_by(shop_id=shop.id, valid_to=None).all()
        for rate in rates:
            program = BonusProgram.query.get(rate.program_id)
            req_points = voucher / program.point_value_eur if program.point_value_eur > 0 else float('inf')
            spend = req_points / rate.points_per_eur if rate.points_per_eur > 0 else float('inf')
            results.append({'program': program.name, 'spend': round(spend, 2), 'req_points': round(req_points, 2)})
        results.sort(key=lambda r: r['spend'])
        return render_template('result.html', mode='voucher', shop=shop, voucher=voucher, results=results)
    
    else:  # contract mode
        # Show per-completion points available for this shop
        results = []
        # Only get currently valid rates
        rates = ShopProgramRate.query.filter_by(shop_id=shop.id, valid_to=None).all()
        
        # We need to get the raw rate data which may include per_completion_points
        # For now, we'll show from the DB what we have
        for rate in rates:
            program = BonusProgram.query.get(rate.program_id)
            incentive_text = request.form.get(f'incentive_{rate.id}', '')  # not used, placeholder
            # In a real scenario, we'd fetch the per_completion_points from the database
            # For now, calculate an estimate based on point_value
            results.append({
                'program': program.name,
                'note': 'Vertragsabschluss - siehe Admin für genaue Angaben'
            })
        
        return render_template('result.html', mode='contract', shop=shop, results=results)


@app.route('/admin', methods=['GET'])
@login_required
def admin():
    # Only admins can access
    if current_user.role != 'admin':
        flash('Sie haben keine Berechtigung für diese Seite.', 'error')
        return redirect(url_for('index'))
    
    # Use admin UI
    return render_template('admin.html')


@app.route('/admin/add_program', methods=['POST'])
@login_required
def admin_add_program():
    if current_user.role != 'admin':
        flash('Sie haben keine Berechtigung für diese Aktion.', 'error')
        return redirect(url_for('index'))
    
    name = request.form.get('name', '').strip()
    try:
        point_value_eur = float(request.form.get('point_value_eur', 0.01))
    except ValueError:
        point_value_eur = 0.01
    
    if name:
        # Check if program already exists
        existing = BonusProgram.query.filter_by(name=name).first()
        if not existing:
            new_program = BonusProgram(name=name, point_value_eur=point_value_eur)
            db.session.add(new_program)
            db.session.commit()
            db.session.add(ScrapeLog(message=f'Program added: {name} (€{point_value_eur} per point)'))
            db.session.commit()
    
    return redirect('/admin')


@app.route('/admin/run_scraper', methods=['POST'])
@login_required
def admin_run_scraper():
    if current_user.role != 'admin':
        flash('Sie haben keine Berechtigung für diese Aktion.', 'error')
        return redirect(url_for('index'))
    
    # Queue the scraper job instead of running it synchronously
    job_id = job_queue.enqueue(scrape_example)
    
    # Return JSON if AJAX request, otherwise render template
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'job_id': job_id, 'status': 'queued'})
    
    flash(f'Example-Scraper gestartet. Job ID: {job_id[:8]}...', 'success')
    shops = Shop.query.all()
    programs = BonusProgram.query.all()
    logs = ScrapeLog.query.order_by(ScrapeLog.timestamp.desc()).limit(50).all()
    return render_template('admin.html', shops=shops, programs=programs, logs=logs, job_id=job_id)


@app.route('/admin/run_payback', methods=['POST'])
@login_required
def admin_run_payback():
    if current_user.role != 'admin':
        flash('Sie haben keine Berechtigung für diese Aktion.', 'error')
        return redirect(url_for('index'))
    
    # Queue the scraper job instead of running it synchronously
    job_id = job_queue.enqueue(scrape_payback)
    
    # Return JSON if AJAX request, otherwise render template
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'job_id': job_id, 'status': 'queued'})
    
    flash(f'Payback-Scraper gestartet. Job ID: {job_id[:8]}...', 'success')
    shops = Shop.query.all()
    programs = BonusProgram.query.all()
    logs = ScrapeLog.query.order_by(ScrapeLog.timestamp.desc()).limit(200).all()
    return render_template('admin.html', shops=shops, programs=programs, logs=logs, job_id=job_id)


@app.route('/admin/run_miles_and_more', methods=['POST'])
@login_required
def admin_run_miles_and_more():
    if current_user.role != 'admin':
        flash('Sie haben keine Berechtigung für diese Aktion.', 'error')
        return redirect(url_for('index'))
    
    # Queue the scraper job instead of running it synchronously
    job_id = job_queue.enqueue(scrape_miles_and_more)
    
    # Return JSON if AJAX request, otherwise render template
    if request.headers.get('Accept') == 'application/json':
        return jsonify({'job_id': job_id, 'status': 'queued'})
    
    flash(f'Miles & More-Scraper gestartet. Job ID: {job_id[:8]}...', 'success')
    shops = Shop.query.all()
    programs = BonusProgram.query.all()
    logs = ScrapeLog.query.order_by(ScrapeLog.timestamp.desc()).limit(200).all()
    return render_template('admin.html', shops=shops, programs=programs, logs=logs, job_id=job_id)


# ============ JOB STATUS ROUTES ============

@app.route('/admin/job_status/<job_id>', methods=['GET'])
@login_required
def job_status(job_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    job = job_queue.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job.to_dict())


@app.route('/admin/jobs', methods=['GET'])
@login_required
def list_jobs():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    all_jobs = job_queue.get_all_jobs()
    # Sort by created_at descending
    all_jobs.sort(key=lambda j: j.created_at, reverse=True)
    # Return last 20 jobs
    return jsonify([j.to_dict() for j in all_jobs[:20]])


# ============ RATE REVIEW ROUTES ============

@app.route('/admin/rate/<int:rate_id>/comment', methods=['POST'])
@login_required
def add_rate_comment(rate_id):
    """Add a review comment to a rate (admin/contributor only)"""
    if current_user.role not in ['admin', 'contributor']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    from models import ShopProgramRate, RateComment
    from notifications import notify_rate_comment
    
    rate = ShopProgramRate.query.get_or_404(rate_id)
    comment_text = request.json.get('comment')
    comment_type = request.json.get('type', 'FEEDBACK')  # FEEDBACK, REJECTION_REASON, SUGGESTION
    
    if not comment_text:
        return jsonify({'error': 'Comment text required'}), 400
    
    comment = RateComment(
        rate_id=rate.id,
        reviewer_id=current_user.id,
        comment_type=comment_type,
        comment_text=comment_text
    )
    db.session.add(comment)
    db.session.commit()
    
    # Send notification
    notify_rate_comment(rate, comment, current_user.username)
    
    return jsonify({
        'success': True,
        'comment': {
            'id': comment.id,
            'type': comment.comment_type,
            'text': comment.comment_text,
            'created_at': comment.created_at.isoformat()
        }
    })


@app.route('/admin/rate/<int:rate_id>/comments', methods=['GET'])
@login_required
def get_rate_comments(rate_id):
    """Get all comments for a rate"""
    from models import ShopProgramRate, RateComment, User
    
    rate = ShopProgramRate.query.get_or_404(rate_id)
    comments = RateComment.query.filter_by(rate_id=rate.id).order_by(RateComment.created_at.desc()).all()
    
    return jsonify({
        'comments': [{
            'id': c.id,
            'type': c.comment_type,
            'text': c.comment_text,
            'reviewer': c.reviewer.username,
            'created_at': c.created_at.isoformat()
        } for c in comments]
    })


# ============ SHOP MERGE ROUTES ============

@app.route('/admin/shops/merge_proposals', methods=['GET'])
@login_required
def list_merge_proposals():
    """List all pending shop merge proposals"""
    if current_user.role not in ['admin', 'contributor']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    from models import ShopMergeProposal, ShopVariant, ShopMain, User
    
    proposals = ShopMergeProposal.query.filter_by(status='PENDING').all()
    
    return jsonify({
        'proposals': [{
            'id': p.id,
            'variant_a': {
                'id': p.variant_a_id,
                'name': ShopVariant.query.get(p.variant_a_id).source_name,
                'source': ShopVariant.query.get(p.variant_a_id).source
            },
            'variant_b': {
                'id': p.variant_b_id,
                'name': ShopVariant.query.get(p.variant_b_id).source_name,
                'source': ShopVariant.query.get(p.variant_b_id).source
            },
            'reason': p.reason,
            'proposed_by': User.query.get(p.proposed_by_user_id).username,
            'created_at': p.created_at.isoformat()
        } for p in proposals]
    })


@app.route('/admin/shops/merge_proposal', methods=['POST'])
@login_required
def create_merge_proposal():
    """Create a shop merge proposal"""
    if current_user.role not in ['admin', 'contributor']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    from models import ShopMergeProposal
    
    variant_a_id = request.json.get('variant_a_id')
    variant_b_id = request.json.get('variant_b_id')
    reason = request.json.get('reason')
    
    if not all([variant_a_id, variant_b_id]):
        return jsonify({'error': 'Both variant IDs required'}), 400
    
    proposal = ShopMergeProposal(
        variant_a_id=variant_a_id,
        variant_b_id=variant_b_id,
        proposed_by_user_id=current_user.id,
        reason=reason,
        status='PENDING'
    )
    db.session.add(proposal)
    db.session.commit()
    
    return jsonify({'success': True, 'proposal_id': proposal.id})


@app.route('/admin/shops/merge_proposal/<int:proposal_id>/approve', methods=['POST'])
@login_required
def approve_merge_proposal(proposal_id):
    """Approve and execute a shop merge proposal (admin only)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    from models import ShopMergeProposal, ShopVariant
    from shop_dedup import merge_shops
    from notifications import notify_merge_approved
    
    proposal = ShopMergeProposal.query.get_or_404(proposal_id)
    
    if proposal.status != 'PENDING':
        return jsonify({'error': 'Proposal already decided'}), 400
    
    # Get the ShopMain IDs from variants
    variant_a = ShopVariant.query.get(proposal.variant_a_id)
    variant_b = ShopVariant.query.get(proposal.variant_b_id)
    
    # Merge shops
    try:
        merge_shops(
            main_from_id=variant_a.shop_main_id,
            main_to_id=variant_b.shop_main_id,
            user_id=current_user.id
        )
        
        proposal.status = 'APPROVED'
        proposal.decided_at = datetime.utcnow()
        proposal.decided_by_user_id = current_user.id
        db.session.commit()
        
        # Send notification
        notify_merge_approved(proposal)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/shops/merge_proposal/<int:proposal_id>/reject', methods=['POST'])
@login_required
def reject_merge_proposal(proposal_id):
    """Reject a shop merge proposal (admin only)"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    from models import ShopMergeProposal
    from notifications import notify_merge_rejected
    
    proposal = ShopMergeProposal.query.get_or_404(proposal_id)
    
    if proposal.status != 'PENDING':
        return jsonify({'error': 'Proposal already decided'}), 400
    
    reason = request.json.get('reason', 'Rejected by admin')
    proposal.status = 'REJECTED'
    proposal.decided_at = datetime.utcnow()
    proposal.decided_by_user_id = current_user.id
    proposal.decided_reason = reason
    db.session.commit()
    
    # Send notification
    notify_merge_rejected(proposal, reason)
    
    return jsonify({'success': True})


# ============ NOTIFICATION ROUTES ============

@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get all notifications for current user"""
    from models import Notification
    
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(50).all()
    
    return jsonify({
        'notifications': [{
            'id': n.id,
            'type': n.notification_type,
            'title': n.title,
            'message': n.message,
            'link_type': n.link_type,
            'link_id': n.link_id,
            'is_read': n.is_read,
            'created_at': n.created_at.isoformat()
        } for n in notifications],
        'unread_count': Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    })


@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    from notifications import mark_as_read
    
    if mark_as_read(notification_id, current_user.id):
        return jsonify({'success': True})
    return jsonify({'error': 'Notification not found'}), 404


@app.route('/api/notifications/read_all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    from notifications import mark_all_as_read
    
    mark_all_as_read(current_user.id)
    return jsonify({'success': True})


@app.route('/api/notifications/unread_count', methods=['GET'])
@login_required
def get_unread_count():
    """Get unread notification count"""
    from notifications import get_unread_count
    
    count = get_unread_count(current_user.id)
    return jsonify({'unread_count': count})


# ============ AUTH ROUTES ============

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not username or not email or not password:
            flash('Alle Felder sind erforderlich.', 'error')
            return redirect(url_for('register'))
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Benutzername bereits vorhanden.', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email bereits registriert.', 'error')
            return redirect(url_for('register'))
        
        # Create new user (starts as 'viewer')
        user = User(username=username, email=email, role='viewer')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Registrierung erfolgreich! Bitte melden Sie sich an.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if user.status == 'banned':
                flash('Ihr Konto wurde gesperrt.', 'error')
                return redirect(url_for('login'))
            
            login_user(user)
            flash(f'Willkommen, {user.username}!', 'success')
            return redirect(url_for('index'))
        
        flash('Ungültiger Benutzername oder Passwort.', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sie wurden abgemeldet.', 'success')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    contributor_request = ContributorRequest.query.filter_by(user_id=current_user.id).first()
    proposals = Proposal.query.filter_by(user_id=current_user.id).all()
    return render_template('profile.html', contributor_request=contributor_request, proposals=proposals)


@app.route('/request-contributor', methods=['POST'])
@login_required
def request_contributor():
    if current_user.role == 'contributor':
        flash('Sie sind bereits Contributor.', 'info')
        return redirect(url_for('profile'))
    
    # Check if already requested
    existing = ContributorRequest.query.filter_by(user_id=current_user.id, status='pending').first()
    if existing:
        flash('Sie haben bereits eine ausstehende Anfrage.', 'info')
        return redirect(url_for('profile'))
    
    request_obj = ContributorRequest(user_id=current_user.id)
    db.session.add(request_obj)
    db.session.commit()
    
    flash('Contributor-Anfrage eingereicht. Warten Sie auf Admin-Bestätigung.', 'success')
    return redirect(url_for('profile'))


@app.route('/proposals')
@login_required
def proposals():
    if current_user.role not in ['user', 'contributor', 'admin']:
        flash('Sie müssen registriert sein, um Beiträge zu sehen.', 'error')
        return redirect(url_for('index'))
    
    # Get all pending proposals
    all_proposals = Proposal.query.filter_by(status='pending').order_by(Proposal.created_at.desc()).all()
    
    # For each proposal, get vote counts and user's vote if any
    proposals_data = []
    for proposal in all_proposals:
        votes = ProposalVote.query.filter_by(proposal_id=proposal.id).all()
        # Count votes with weights (Admin votes = 3x)
        upvotes = sum(v.vote_weight for v in votes if v.vote == 1)
        downvotes = sum(1 for v in votes if v.vote == -1)
        user_vote = None
        if current_user.role in ['contributor', 'admin']:
            user_vote_obj = ProposalVote.query.filter_by(proposal_id=proposal.id, voter_id=current_user.id).first()
            if user_vote_obj:
                user_vote = user_vote_obj.vote
        
        # Get submitter info
        submitter = User.query.get(proposal.user_id)
        
        proposals_data.append({
            'proposal': proposal,
            'upvotes': upvotes,
            'downvotes': downvotes,
            'user_vote': user_vote,
            'submitter': submitter
        })
    
    return render_template('proposals.html', proposals_data=proposals_data)


@app.route('/vote/<int:proposal_id>', methods=['POST'])
@login_required
def vote_proposal(proposal_id):
    if current_user.role not in ['contributor', 'admin']:
        flash('Sie müssen Contributor sein zum Abstimmen.', 'error')
        return redirect(url_for('proposals'))
    
    proposal = Proposal.query.get_or_404(proposal_id)
    vote = int(request.form.get('vote', 0))
    
    if vote not in [-1, 1]:
        flash('Ungültige Abstimmung.', 'error')
        return redirect(url_for('proposals'))
    
    # Admin-Votes zählen 3x
    vote_weight = 3 if current_user.role == 'admin' else 1
    
    # Check if user already voted
    existing_vote = ProposalVote.query.filter_by(proposal_id=proposal_id, voter_id=current_user.id).first()
    
    if existing_vote:
        # Update existing vote
        existing_vote.vote = vote
        existing_vote.vote_weight = vote_weight
    else:
        # Create new vote
        new_vote = ProposalVote(
            proposal_id=proposal_id,
            voter_id=current_user.id,
            vote=vote,
            vote_weight=vote_weight
        )
        db.session.add(new_vote)
    
    db.session.commit()
    
    # Check if should auto-approve (3+ upvotes)
    all_votes = ProposalVote.query.filter_by(proposal_id=proposal_id).all()
    upvote_weight = sum(v.vote_weight for v in all_votes if v.vote == 1)
    
    if upvote_weight >= 3 and proposal.status == 'pending':
        proposal.status = 'approved'
        proposal.approved_at = datetime.utcnow()
        proposal.approved_by_system = True
        db.session.commit()
        flash('✓ Proposal wurde mit 3+ gewichteten Upvotes automatisch genehmigt!', 'success')
    
    return redirect(url_for('proposals'))


@app.route('/approve/<int:proposal_id>', methods=['POST'])
@login_required
def approve_proposal(proposal_id):
    if current_user.role != 'admin':
        flash('Nur Admins können Proposals direkt genehmigen.', 'error')
        return redirect(url_for('proposals'))
    
    proposal = Proposal.query.get_or_404(proposal_id)
    
    if proposal.status != 'pending':
        flash('Dieser Proposal ist nicht mehr ausstehend.', 'error')
        return redirect(url_for('proposals'))
    
    proposal.status = 'approved'
    proposal.approved_at = datetime.utcnow()
    proposal.approved_by_system = False
    db.session.commit()
    
    flash(f'✓ Proposal {proposal_id} wurde genehmigt!', 'success')
    return redirect(url_for('proposals'))


@app.route('/proposals/new', methods=['GET', 'POST'])
@login_required
def create_proposal():
    if current_user.role not in ['user', 'contributor', 'admin']:
        flash('Sie müssen registriert sein, um Beiträge zu erstellen.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        proposal_type = request.form.get('proposal_type')
        reason = request.form.get('reason', '').strip()
        source_url = request.form.get('source_url', '').strip()
        
        proposal = Proposal(
            proposal_type=proposal_type,
            user_id=current_user.id,
            reason=reason,
            source_url=source_url if source_url else None
        )
        
        if proposal_type == 'rate_change':
            shop_id = request.form.get('shop_id')
            program_id = request.form.get('program_id')
            points_per_eur = request.form.get('points_per_eur')
            cashback_pct = request.form.get('cashback_pct')
            
            if not shop_id or not program_id:
                flash('Shop und Programm müssen ausgewählt werden.', 'error')
                return redirect(url_for('create_proposal'))
            
            proposal.shop_id = int(shop_id)
            proposal.program_id = int(program_id)
            proposal.proposed_points_per_eur = float(points_per_eur) if points_per_eur else 0.0
            proposal.proposed_cashback_pct = float(cashback_pct) if cashback_pct else 0.0
        
        elif proposal_type == 'shop_add':
            shop_name = request.form.get('shop_name', '').strip()
            if not shop_name:
                flash('Shop-Name ist erforderlich.', 'error')
                return redirect(url_for('create_proposal'))
            proposal.proposed_name = shop_name
        
        elif proposal_type == 'program_add':
            program_name = request.form.get('program_name', '').strip()
            point_value = request.form.get('point_value_eur')
            if not program_name or not point_value:
                flash('Programmname und Punktwert sind erforderlich.', 'error')
                return redirect(url_for('create_proposal'))
            proposal.proposed_name = program_name
            proposal.proposed_point_value_eur = float(point_value)
        
        elif proposal_type == 'coupon_add':
            coupon_type = request.form.get('coupon_type')
            coupon_value = request.form.get('coupon_value')
            coupon_description = request.form.get('coupon_description', '').strip()
            coupon_shop_id = request.form.get('coupon_shop_id')
            coupon_program_id = request.form.get('coupon_program_id')
            coupon_combinable = request.form.get('coupon_combinable')
            coupon_valid_to = request.form.get('coupon_valid_to')
            
            if not coupon_type or not coupon_value or not coupon_description:
                flash('Coupon-Typ, Wert und Beschreibung sind erforderlich.', 'error')
                return redirect(url_for('create_proposal'))
            
            proposal.proposed_coupon_type = coupon_type
            proposal.proposed_coupon_value = float(coupon_value)
            proposal.proposed_coupon_description = coupon_description
            proposal.shop_id = int(coupon_shop_id) if coupon_shop_id else None
            proposal.program_id = int(coupon_program_id) if coupon_program_id else None
            
            # Convert combinable value
            if coupon_combinable == 'yes':
                proposal.proposed_coupon_combinable = True
            elif coupon_combinable == 'no':
                proposal.proposed_coupon_combinable = False
            else:
                proposal.proposed_coupon_combinable = None  # Unknown
            
            # Parse date
            if coupon_valid_to:
                from datetime import datetime as dt
                proposal.proposed_coupon_valid_to = dt.strptime(coupon_valid_to, '%Y-%m-%d')
        
        db.session.add(proposal)
        db.session.commit()
        
        # Add audit trail entry
        audit = ProposalAuditTrail(
            proposal_id=proposal.id,
            action='created',
            actor_id=current_user.id
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Vorschlag erfolgreich eingereicht!', 'success')
        return redirect(url_for('proposals'))
    
    # GET request - show form
    shops = Shop.query.all()
    programs = BonusProgram.query.all()
    return render_template('create_proposal.html', shops=shops, programs=programs)


@app.route('/review-scraper-proposal/<int:proposal_id>', methods=['GET', 'POST'])
@login_required
def review_scraper_proposal(proposal_id):
    """Review and create a user proposal from a scraper proposal"""
    scraper_proposal = Proposal.query.get_or_404(proposal_id)
    
    # Only the scraper can create these proposals
    if scraper_proposal.source != 'scraper':
        flash('Dies ist kein Scraper-Vorschlag.', 'error')
        return redirect(url_for('proposals'))
    
    if request.method == 'POST':
        # Create a new user proposal based on the scraper proposal
        proposal_type = scraper_proposal.proposal_type
        
        user_proposal = Proposal(
            proposal_type=proposal_type,
            status='pending',
            source='user',  # Mark as from user
            user_id=current_user.id,
            shop_id=scraper_proposal.shop_id,
            program_id=scraper_proposal.program_id,
            reason=f"User review of scraper proposal #{scraper_proposal.id}: {request.form.get('reason', '')}"
        )
        
        # Copy proposal-specific data
        if proposal_type == 'rate_change':
            user_proposal.proposed_points_per_eur = request.form.get('points_per_eur', scraper_proposal.proposed_points_per_eur)
            user_proposal.proposed_cashback_pct = request.form.get('cashback_pct', scraper_proposal.proposed_cashback_pct)
        elif proposal_type == 'shop_add':
            user_proposal.proposed_name = request.form.get('name', scraper_proposal.proposed_name)
        elif proposal_type == 'program_add':
            user_proposal.proposed_name = request.form.get('name', scraper_proposal.proposed_name)
            user_proposal.proposed_point_value_eur = request.form.get('point_value_eur', scraper_proposal.proposed_point_value_eur)
        elif proposal_type == 'coupon_add':
            user_proposal.proposed_coupon_type = request.form.get('coupon_type', scraper_proposal.proposed_coupon_type)
            user_proposal.proposed_coupon_value = request.form.get('coupon_value', scraper_proposal.proposed_coupon_value)
            user_proposal.proposed_coupon_description = request.form.get('coupon_description', scraper_proposal.proposed_coupon_description)
            user_proposal.proposed_coupon_combinable = request.form.get('coupon_combinable', scraper_proposal.proposed_coupon_combinable)
            user_proposal.proposed_coupon_valid_to = request.form.get('coupon_valid_to', scraper_proposal.proposed_coupon_valid_to)
        
        db.session.add(user_proposal)
        
        # Mark scraper proposal as reviewed
        scraper_proposal.status = 'approved'
        
        db.session.commit()
        
        flash('✓ Ihr Vorschlag wurde eingereicht!', 'success')
        return redirect(url_for('proposals'))
    
    # GET request - show review form
    return render_template('review_scraper_proposal.html', proposal=scraper_proposal)


if __name__ == '__main__':
    ensure_seed()
    # Start job queue worker
    job_queue.start()
    try:
        app.run(debug=True)
    finally:
        job_queue.stop()
