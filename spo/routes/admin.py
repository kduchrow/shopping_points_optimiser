from datetime import UTC, datetime

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from job_queue import job_queue
from spo.extensions import db
from spo.models import (
    BonusProgram,
    RateComment,
    ScrapeLog,
    Shop,
    ShopMain,
    ShopMergeProposal,
    ShopMetadataProposal,
    ShopProgramRate,
    ShopVariant,
    User,
)
from spo.services.dedup import merge_shops
from spo.services.notifications import (
    notify_merge_approved,
    notify_merge_rejected,
    notify_rate_comment,
)
from spo.services.scrapers import scrape_example, scrape_miles_and_more, scrape_payback


def register_admin(app):
    @app.route("/admin/shops_overview", methods=["GET"])
    @login_required
    def admin_shops_overview():
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        query = request.args.get("q", "").strip().lower()
        mains_query = db.session.query(ShopMain).order_by(ShopMain.canonical_name).limit(300)
        mains = mains_query.all()

        result = []
        for main in mains:
            if query and query not in (main.canonical_name_lower or "").lower():
                continue

            variants = [
                {
                    "source": variant.source,
                    "name": variant.source_name,
                    "source_id": variant.source_id,
                    "confidence": variant.confidence_score,
                }
                for variant in main.variants
            ]

            linked_shops = Shop.query.filter_by(shop_main_id=main.id).all()
            rates_data = []
            for shop in linked_shops:
                rates = ShopProgramRate.query.filter_by(shop_id=shop.id, valid_to=None).all()
                for rate in rates:
                    program = BonusProgram.query.get(rate.program_id)
                    rates_data.append(
                        {
                            "shop_name": shop.name,
                            "program": program.name if program else "unknown",
                            "points_per_eur": rate.points_per_eur,
                            "cashback_pct": rate.cashback_pct,
                        }
                    )

            result.append(
                {
                    "id": main.id,
                    "name": main.canonical_name,
                    "website": main.website,
                    "status": main.status,
                    "variants": variants,
                    "rates": rates_data,
                }
            )

            if len(result) >= 200:
                break

        return jsonify({"shops": result})

    @app.route("/admin", methods=["GET"])
    @login_required
    def admin():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Seite.", "error")
            return redirect(url_for("index"))
        return render_template("admin.html")

    @app.route("/admin/add_program", methods=["POST"])
    @login_required
    def admin_add_program():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return redirect(url_for("index"))

        name = request.form.get("name", "").strip()
        try:
            point_value_eur = float(request.form.get("point_value_eur", 0.01))
        except ValueError:
            point_value_eur = 0.01

        if name:
            existing = BonusProgram.query.filter_by(name=name).first()
            if not existing:
                new_program = BonusProgram(name=name, point_value_eur=point_value_eur)
                db.session.add(new_program)
                db.session.commit()
                db.session.add(
                    ScrapeLog(message=f"Program added: {name} (€{point_value_eur} per point)")
                )
                db.session.commit()

        return redirect("/admin")

    def _run_scraper_job(scraper_func, success_message):
        job_id = job_queue.enqueue(scraper_func)
        if request.headers.get("Accept") == "application/json":
            return jsonify({"job_id": job_id, "status": "queued"})

        flash(success_message.format(job_id[:8]), "success")
        shops = Shop.query.all()
        programs = BonusProgram.query.all()
        logs = ScrapeLog.query.order_by(ScrapeLog.timestamp.desc()).limit(200).all()
        return render_template(
            "admin.html", shops=shops, programs=programs, logs=logs, job_id=job_id
        )

    @app.route("/admin/run_scraper", methods=["POST"])
    @login_required
    def admin_run_scraper():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return redirect(url_for("index"))
        return _run_scraper_job(scrape_example, "Example-Scraper gestartet. Job ID: {}...")

    @app.route("/admin/run_payback", methods=["POST"])
    @login_required
    def admin_run_payback():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return redirect(url_for("index"))
        return _run_scraper_job(scrape_payback, "Payback-Scraper gestartet. Job ID: {}...")

    @app.route("/admin/run_miles_and_more", methods=["POST"])
    @login_required
    def admin_run_miles_and_more():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return redirect(url_for("index"))
        return _run_scraper_job(
            scrape_miles_and_more, "Miles & More-Scraper gestartet. Job ID: {}..."
        )

    @app.route("/admin/job_status/<job_id>", methods=["GET"])
    @login_required
    def job_status(job_id):
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        job = job_queue.get_job(job_id)
        if not job:
            return jsonify({"error": "Job not found"}), 404

        return jsonify(job.to_dict())

    @app.route("/admin/jobs", methods=["GET"])
    @login_required
    def list_jobs():
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        all_jobs = job_queue.get_all_jobs()
        all_jobs.sort(key=lambda job: job.created_at, reverse=True)
        return jsonify([job.to_dict() for job in all_jobs[:20]])

    @app.route("/admin/rate/<int:rate_id>/comment", methods=["POST"])
    @login_required
    def add_rate_comment(rate_id):
        if current_user.role not in ["admin", "contributor"]:
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json(silent=True) or {}
        comment_text = data.get("comment")
        comment_type = data.get("type", "FEEDBACK")

        if not comment_text:
            return jsonify({"error": "Comment text required"}), 400

        rate = ShopProgramRate.query.get_or_404(rate_id)
        comment = RateComment(
            rate_id=rate.id,
            reviewer_id=current_user.id,
            comment_type=comment_type,
            comment_text=comment_text,
        )
        db.session.add(comment)
        db.session.commit()

        notify_rate_comment(rate, comment, current_user.username)

        return jsonify(
            {
                "success": True,
                "comment": {
                    "id": comment.id,
                    "type": comment.comment_type,
                    "text": comment.comment_text,
                    "created_at": comment.created_at.isoformat(),
                },
            }
        )

    @app.route("/admin/rate/<int:rate_id>/comments", methods=["GET"])
    @login_required
    def get_rate_comments(rate_id):
        rate = ShopProgramRate.query.get_or_404(rate_id)
        comments = (
            RateComment.query.filter_by(rate_id=rate.id)
            .order_by(RateComment.created_at.desc())
            .all()
        )

        return jsonify(
            {
                "comments": [
                    {
                        "id": comment.id,
                        "type": comment.comment_type,
                        "text": comment.comment_text,
                        "reviewer": comment.reviewer.username,
                        "created_at": comment.created_at.isoformat(),
                    }
                    for comment in comments
                ]
            }
        )

    @app.route("/admin/shops/merge_proposals", methods=["GET"])
    @login_required
    def list_merge_proposals():
        if current_user.role not in ["admin", "contributor"]:
            return jsonify({"error": "Unauthorized"}), 403

        proposals = ShopMergeProposal.query.filter_by(status="PENDING").all()

        return jsonify(
            {
                "proposals": [
                    {
                        "id": proposal.id,
                        "variant_a": {
                            "id": proposal.variant_a_id,
                            "name": ShopVariant.query.get(proposal.variant_a_id).source_name,
                            "source": ShopVariant.query.get(proposal.variant_a_id).source,
                        },
                        "variant_b": {
                            "id": proposal.variant_b_id,
                            "name": ShopVariant.query.get(proposal.variant_b_id).source_name,
                            "source": ShopVariant.query.get(proposal.variant_b_id).source,
                        },
                        "reason": proposal.reason,
                        "proposed_by": User.query.get(proposal.proposed_by_user_id).username,
                        "created_at": proposal.created_at.isoformat(),
                    }
                    for proposal in proposals
                ]
            }
        )

    @app.route("/admin/shops/merge_proposal", methods=["POST"])
    @login_required
    def create_merge_proposal():
        if current_user.role not in ["admin", "contributor"]:
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json(silent=True) or {}
        variant_a_id = data.get("variant_a_id")
        variant_b_id = data.get("variant_b_id")
        reason = data.get("reason")

        if not all([variant_a_id, variant_b_id]):
            return jsonify({"error": "Both variant IDs required"}), 400

        proposal = ShopMergeProposal(
            variant_a_id=variant_a_id,
            variant_b_id=variant_b_id,
            proposed_by_user_id=current_user.id,
            reason=reason,
            status="PENDING",
        )
        db.session.add(proposal)
        db.session.commit()

        return jsonify({"success": True, "proposal_id": proposal.id})

    @app.route("/admin/shops/merge_proposal/<int:proposal_id>/approve", methods=["POST"])
    @login_required
    def approve_merge_proposal(proposal_id):
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        proposal = ShopMergeProposal.query.get_or_404(proposal_id)
        if proposal.status != "PENDING":
            return jsonify({"error": "Proposal already decided"}), 400

        variant_a = ShopVariant.query.get(proposal.variant_a_id)
        variant_b = ShopVariant.query.get(proposal.variant_b_id)

        try:
            merge_shops(
                main_from_id=variant_a.shop_main_id,
                main_to_id=variant_b.shop_main_id,
                user_id=current_user.id,
            )
            proposal.status = "APPROVED"
            proposal.decided_at = datetime.now(UTC)
            proposal.decided_by_user_id = current_user.id
            db.session.commit()
            notify_merge_approved(proposal)
            return jsonify({"success": True})
        except Exception as exc:  # pragma: no cover - defensive
            return jsonify({"error": str(exc)}), 500

    @app.route("/admin/shops/merge_proposal/<int:proposal_id>/reject", methods=["POST"])
    @login_required
    def reject_merge_proposal(proposal_id):
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        proposal = ShopMergeProposal.query.get_or_404(proposal_id)
        if proposal.status != "PENDING":
            return jsonify({"error": "Proposal already decided"}), 400

        data = request.get_json(silent=True) or {}
        reason = data.get("reason", "Rejected by admin")
        proposal.status = "REJECTED"
        proposal.decided_at = datetime.now(UTC)
        proposal.decided_by_user_id = current_user.id
        proposal.decided_reason = reason
        db.session.commit()

        notify_merge_rejected(proposal, reason)

        return jsonify({"success": True})

    @app.route("/admin/shops/metadata_proposals", methods=["GET"])
    @login_required
    def list_metadata_proposals():
        if current_user.role not in ["admin", "contributor"]:
            return jsonify({"error": "Unauthorized"}), 403

        proposals = ShopMetadataProposal.query.filter_by(status="PENDING").all()
        return jsonify(
            {
                "proposals": [
                    {
                        "id": proposal.id,
                        "shop_main_id": proposal.shop_main_id,
                        "proposed_name": proposal.proposed_name,
                        "proposed_website": proposal.proposed_website,
                        "proposed_logo_url": proposal.proposed_logo_url,
                        "reason": proposal.reason,
                        "user_id": proposal.proposed_by_user_id,
                        "created_at": proposal.created_at.isoformat(),
                    }
                    for proposal in proposals
                ]
            }
        )

    @app.route("/admin/shops/metadata_proposals/<int:proposal_id>/approve", methods=["POST"])
    @login_required
    def approve_metadata_proposal(proposal_id):
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        proposal = ShopMetadataProposal.query.get_or_404(proposal_id)
        if proposal.status != "PENDING":
            return jsonify({"error": "Already decided"}), 400

        main = ShopMain.query.get_or_404(proposal.shop_main_id)
        if proposal.proposed_name:
            main.canonical_name = proposal.proposed_name
            main.canonical_name_lower = proposal.proposed_name.lower()
        if proposal.proposed_website:
            main.website = proposal.proposed_website
        if proposal.proposed_logo_url:
            main.logo_url = proposal.proposed_logo_url
        main.updated_at = datetime.now(UTC)
        main.updated_by_user_id = current_user.id

        proposal.status = "APPROVED"
        proposal.decided_at = datetime.now(UTC)
        proposal.decided_by_user_id = current_user.id
        db.session.commit()
        return jsonify({"success": True})

    @app.route("/admin/shops/metadata_proposals/<int:proposal_id>/reject", methods=["POST"])
    @login_required
    def reject_metadata_proposal(proposal_id):
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        proposal = ShopMetadataProposal.query.get_or_404(proposal_id)
        if proposal.status != "PENDING":
            return jsonify({"error": "Already decided"}), 400

        data = request.get_json(silent=True) or {}
        reason = data.get("reason", "Rejected by admin")
        proposal.status = "REJECTED"
        proposal.decided_at = datetime.now(UTC)
        proposal.decided_by_user_id = current_user.id
        proposal.decided_reason = reason
        db.session.commit()
        return jsonify({"success": True})

    @app.route("/admin/shops/metadata_proposals/<int:proposal_id>/delete", methods=["POST"])
    @login_required
    def delete_metadata_proposal(proposal_id):
        if current_user.role != "admin":
            return jsonify({"error": "Unauthorized"}), 403

        proposal = ShopMetadataProposal.query.get_or_404(proposal_id)
        db.session.delete(proposal)
        db.session.commit()
        return jsonify({"success": True})

    @app.route("/admin/clear_shops", methods=["POST"])
    @login_required
    def admin_clear_shops():
        if current_user.role != "admin":
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return jsonify({"error": "Unauthorized"}), 403

        try:
            # Count how many shops will be deleted
            shop_count = Shop.query.count()
            rate_count = ShopProgramRate.query.count()

            # Delete all shops
            Shop.query.delete()
            db.session.commit()

            flash(
                f"✅ {shop_count} Shops gelöscht. ({rate_count} Raten wurden archiviert)", "success"
            )
            db.session.add(ScrapeLog(message=f"Admin cleared {shop_count} shops"))
            db.session.commit()

            if request.headers.get("Accept") == "application/json":
                return jsonify({"success": True, "deleted": shop_count})
            return redirect("/admin")
        except Exception as e:
            flash(f"❌ Fehler beim Löschen: {str(e)}", "error")
            if request.headers.get("Accept") == "application/json":
                return jsonify({"error": str(e)}), 500
            return redirect("/admin")

    return app
