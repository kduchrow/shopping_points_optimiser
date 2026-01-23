from datetime import UTC, datetime

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from spo.extensions import db
from spo.models import (
    BonusProgram,
    Proposal,
    ProposalAuditTrail,
    ProposalVote,
    Shop,
    ShopMain,
    ShopMergeProposal,
    ShopMetadataProposal,
    User,
)
from spo.utils import ensure_variant_for_shop


def register_proposals(app):
    @app.route("/proposals")
    @login_required
    def proposals():
        if current_user.role not in ["viewer", "user", "contributor", "admin"]:
            flash("Sie müssen registriert sein, um Beiträge zu sehen.", "error")
            return redirect(url_for("index"))

        all_proposals = (
            Proposal.query.filter_by(status="pending").order_by(Proposal.created_at.desc()).all()
        )
        proposals_data = []
        for proposal in all_proposals:
            votes = ProposalVote.query.filter_by(proposal_id=proposal.id).all()
            upvotes = sum(v.vote_weight for v in votes if v.vote == 1)
            downvotes = sum(1 for v in votes if v.vote == -1)
            user_vote = None
            if current_user.role in ["contributor", "admin"]:
                user_vote_obj = ProposalVote.query.filter_by(
                    proposal_id=proposal.id, voter_id=current_user.id
                ).first()
                if user_vote_obj:
                    user_vote = user_vote_obj.vote
            submitter = db.session.get(User, proposal.user_id)
            shop = db.session.get(Shop, proposal.shop_id) if proposal.shop_id else None
            program = (
                db.session.get(BonusProgram, proposal.program_id) if proposal.program_id else None
            )
            proposals_data.append(
                {
                    "proposal": proposal,
                    "upvotes": upvotes,
                    "downvotes": downvotes,
                    "user_vote": user_vote,
                    "submitter": submitter,
                    "shop": shop,
                    "program": program,
                }
            )

        metadata_proposals = (
            ShopMetadataProposal.query.filter_by(status="PENDING")
            .order_by(ShopMetadataProposal.created_at.desc())
            .all()
        )
        metadata_data = []
        for meta in metadata_proposals:
            submitter = db.session.get(User, meta.proposed_by_user_id)
            main = db.session.get(ShopMain, meta.shop_main_id) if meta.shop_main_id else None
            metadata_data.append({"proposal": meta, "submitter": submitter, "main": main})

        merge_proposals = (
            ShopMergeProposal.query.filter_by(status="PENDING")
            .order_by(ShopMergeProposal.created_at.desc())
            .all()
        )
        merge_data = []
        from spo.models import ShopVariant  # late import to avoid cycles

        for merge in merge_proposals:
            variant_a = db.session.get(ShopVariant, merge.variant_a_id)
            variant_b = db.session.get(ShopVariant, merge.variant_b_id)
            submitter = db.session.get(User, merge.proposed_by_user_id)
            merge_data.append(
                {
                    "proposal": merge,
                    "variant_a": variant_a,
                    "variant_b": variant_b,
                    "submitter": submitter,
                }
            )

        return render_template(
            "proposals.html",
            proposals_data=proposals_data,
            metadata_data=metadata_data,
            merge_data=merge_data,
        )

    @app.route("/vote/<int:proposal_id>", methods=["POST"])
    @login_required
    def vote_proposal(proposal_id):
        if current_user.role not in ["contributor", "admin"]:
            flash("Sie müssen Contributor sein zum Abstimmen.", "error")
            return redirect(url_for("proposals"))

        proposal = Proposal.query.get_or_404(proposal_id)
        vote = int(request.form.get("vote", 0))
        if vote not in [-1, 1]:
            flash("Ungültige Abstimmung.", "error")
            return redirect(url_for("proposals"))

        vote_weight = 3 if current_user.role == "admin" else 1
        existing_vote = ProposalVote.query.filter_by(
            proposal_id=proposal_id, voter_id=current_user.id
        ).first()
        if existing_vote:
            existing_vote.vote = vote
            existing_vote.vote_weight = vote_weight
        else:
            db.session.add(
                ProposalVote(
                    proposal_id=proposal_id,
                    voter_id=current_user.id,
                    vote=vote,
                    vote_weight=vote_weight,
                )
            )
        db.session.commit()

        all_votes = ProposalVote.query.filter_by(proposal_id=proposal_id).all()
        upvote_weight = sum(v.vote_weight for v in all_votes if v.vote == 1)
        if upvote_weight >= 3 and proposal.status == "pending":
            # Apply proposal changes to database (same logic as approve_proposal)
            if proposal.proposal_type == "coupon_add":
                from datetime import timedelta

                from spo.models import Coupon, utcnow

                now = utcnow()
                valid_to = proposal.proposed_coupon_valid_to or (now + timedelta(days=30))

                coupon = Coupon(
                    name=f"{proposal.proposed_coupon_value}{'x' if proposal.proposed_coupon_type == 'multiplier' else '%'} Coupon",
                    description=proposal.proposed_coupon_description,
                    coupon_type=proposal.proposed_coupon_type,
                    value=proposal.proposed_coupon_value,
                    shop_id=proposal.shop_id,
                    program_id=proposal.program_id,
                    valid_from=now,
                    valid_to=valid_to,
                    status="active",
                    combinable=(
                        proposal.proposed_coupon_combinable
                        if proposal.proposed_coupon_combinable is not None
                        else False
                    ),
                )
                db.session.add(coupon)

            elif proposal.proposal_type == "rate_change":
                from spo.models import ShopProgramRate, utcnow

                # Archive old rate
                old_rate = ShopProgramRate.query.filter_by(
                    shop_id=proposal.shop_id, program_id=proposal.program_id, valid_to=None
                ).first()
                if old_rate:
                    old_rate.valid_to = utcnow()

                # Create new rate
                new_rate = ShopProgramRate(
                    shop_id=proposal.shop_id,
                    program_id=proposal.program_id,
                    points_per_eur=proposal.proposed_points_per_eur,
                    cashback_pct=proposal.proposed_cashback_pct,
                    valid_from=utcnow(),
                    valid_to=None,
                )
                db.session.add(new_rate)

            elif proposal.proposal_type == "shop_add":
                from spo.models import Shop
                from spo.services.dedup import get_or_create_shop_main

                shop_main, _, _ = get_or_create_shop_main(
                    shop_name=proposal.proposed_name,
                    source="user_proposal",
                    source_id=str(proposal.id),
                )
                shop = Shop(name=proposal.proposed_name, shop_main_id=shop_main.id)
                db.session.add(shop)

            elif proposal.proposal_type == "program_add":
                from spo.models import BonusProgram

                program = BonusProgram(
                    name=proposal.proposed_name, point_value_eur=proposal.proposed_point_value_eur
                )
                db.session.add(program)

            proposal.status = "approved"
            proposal.approved_at = datetime.now(UTC)
            proposal.approved_by_system = True
            db.session.commit()
            flash(
                "✓ Proposal wurde mit 3+ gewichteten Upvotes automatisch genehmigt und angewendet!",
                "success",
            )

        return redirect(url_for("proposals"))

    @app.route("/approve/<int:proposal_id>", methods=["POST"])
    @login_required
    def approve_proposal(proposal_id):
        if current_user.role != "admin":
            flash("Nur Admins können Proposals direkt genehmigen.", "error")
            return redirect(url_for("proposals"))

        proposal = Proposal.query.get_or_404(proposal_id)
        if proposal.status != "pending":
            flash("Dieser Proposal ist nicht mehr ausstehend.", "error")
            return redirect(url_for("proposals"))

        # Apply proposal changes to database
        if proposal.proposal_type == "coupon_add":
            from datetime import timedelta

            from spo.models import Coupon, utcnow

            now = utcnow()
            valid_to = proposal.proposed_coupon_valid_to or (now + timedelta(days=30))

            coupon = Coupon(
                name=f"{proposal.proposed_coupon_value}{'x' if proposal.proposed_coupon_type == 'multiplier' else '%'} Coupon",
                description=proposal.proposed_coupon_description,
                coupon_type=proposal.proposed_coupon_type,
                value=proposal.proposed_coupon_value,
                shop_id=proposal.shop_id,
                program_id=proposal.program_id,
                valid_from=now,
                valid_to=valid_to,
                status="active",
                combinable=(
                    proposal.proposed_coupon_combinable
                    if proposal.proposed_coupon_combinable is not None
                    else False
                ),
            )
            db.session.add(coupon)

        elif proposal.proposal_type == "rate_change":
            from spo.models import ShopProgramRate, utcnow

            # Archive old rate
            old_rate = ShopProgramRate.query.filter_by(
                shop_id=proposal.shop_id, program_id=proposal.program_id, valid_to=None
            ).first()
            if old_rate:
                old_rate.valid_to = utcnow()

            # Create new rate
            new_rate = ShopProgramRate(
                shop_id=proposal.shop_id,
                program_id=proposal.program_id,
                points_per_eur=proposal.proposed_points_per_eur,
                cashback_pct=proposal.proposed_cashback_pct,
                valid_from=utcnow(),
                valid_to=None,
            )
            db.session.add(new_rate)

        elif proposal.proposal_type == "shop_add":
            from spo.models import Shop
            from spo.services.dedup import get_or_create_shop_main

            shop_main, _, _ = get_or_create_shop_main(
                shop_name=proposal.proposed_name, source="user_proposal", source_id=str(proposal.id)
            )
            shop = Shop(name=proposal.proposed_name, shop_main_id=shop_main.id)
            db.session.add(shop)

        elif proposal.proposal_type == "program_add":
            from spo.models import BonusProgram

            program = BonusProgram(
                name=proposal.proposed_name, point_value_eur=proposal.proposed_point_value_eur
            )
            db.session.add(program)

        proposal.status = "approved"
        proposal.approved_at = datetime.now(UTC)
        proposal.approved_by_system = False
        db.session.commit()

        flash(f"✓ Proposal {proposal_id} wurde genehmigt und angewendet!", "success")
        return redirect(url_for("proposals"))

    @app.route("/proposals/new", methods=["GET", "POST"])
    @login_required
    def create_proposal():
        if current_user.role not in ["viewer", "user", "contributor", "admin"]:
            flash("Sie müssen registriert sein, um Beiträge zu erstellen.", "error")
            return redirect(url_for("index"))

        if request.method == "POST":
            proposal_type = request.form.get("proposal_type")
            reason = request.form.get("reason", "").strip()
            source_url = request.form.get("source_url", "").strip()

            if proposal_type in ["rate_change", "shop_add", "program_add", "coupon_add"]:
                proposal = Proposal(
                    proposal_type=proposal_type,
                    user_id=current_user.id,
                    reason=reason,
                    source_url=source_url if source_url else None,
                )

                if proposal_type == "rate_change":
                    shop_id = request.form.get("shop_id")
                    program_id = request.form.get("program_id")
                    rate_type = request.form.get("rate_type", "cashback")
                    rate_category = request.form.get("rate_category", "shop")
                    points_per_eur = request.form.get("points_per_eur")
                    cashback_pct = request.form.get("cashback_pct")
                    if not shop_id or not program_id:
                        flash("Shop und Programm müssen ausgewählt werden.", "error")
                        return redirect(url_for("create_proposal"))
                    proposal.shop_id = int(shop_id)
                    proposal.program_id = int(program_id)
                    if rate_type == "cashback":
                        if not cashback_pct:
                            flash("Bitte Cashback-Prozentsatz angeben.", "error")
                            return redirect(url_for("create_proposal"))
                        proposal.proposed_cashback_pct = float(cashback_pct)
                        proposal.proposed_points_per_eur = 0.0
                    elif rate_type == "points":
                        if not points_per_eur:
                            flash("Bitte Points/EUR angeben.", "error")
                            return redirect(url_for("create_proposal"))
                        proposal.proposed_points_per_eur = float(points_per_eur)
                        proposal.proposed_cashback_pct = 0.0
                    # Store whether this is a contract or shop rate
                    proposal.proposed_rate_type = rate_category

                elif proposal_type == "shop_add":
                    shop_name = request.form.get("shop_name", "").strip()
                    if not shop_name:
                        flash("Shop-Name ist erforderlich.", "error")
                        return redirect(url_for("create_proposal"))
                    proposal.proposed_name = shop_name

                elif proposal_type == "program_add":
                    program_name = request.form.get("program_name", "").strip()
                    program_type = request.form.get("program_type")
                    conversion_type = request.form.get("conversion_type")
                    points_per_eur = request.form.get("points_per_eur")
                    eur_per_point = request.form.get("eur_per_point")
                    normalized_point_value = None
                    if not program_name or not program_type:
                        flash("Programmname und Typ sind erforderlich.", "error")
                        return redirect(url_for("create_proposal"))
                    if program_type == "points":
                        if conversion_type == "points_per_eur" and points_per_eur:
                            try:
                                normalized_point_value = 1.0 / float(points_per_eur)
                            except Exception:
                                flash("Ungültiger Wert für Punkte pro Euro.", "error")
                                return redirect(url_for("create_proposal"))
                        elif conversion_type == "eur_per_point" and eur_per_point:
                            try:
                                normalized_point_value = float(eur_per_point)
                            except Exception:
                                flash("Ungültiger Wert für Euro pro Punkt.", "error")
                                return redirect(url_for("create_proposal"))
                        else:
                            flash("Bitte die Umrechnung für das Punkteprogramm angeben.", "error")
                            return redirect(url_for("create_proposal"))
                        proposal.proposed_name = program_name
                        proposal.proposed_point_value_eur = normalized_point_value
                    elif program_type == "cashback":
                        proposal.proposed_name = program_name
                        proposal.proposed_point_value_eur = 0.0

                elif proposal_type == "coupon_add":
                    coupon_type = request.form.get("coupon_type")
                    coupon_value = request.form.get("coupon_value")
                    coupon_description = request.form.get("coupon_description", "").strip()
                    coupon_shop_id = request.form.get("coupon_shop_id")
                    coupon_program_id = request.form.get("coupon_program_id")
                    coupon_combinable = request.form.get("coupon_combinable")
                    coupon_valid_to = request.form.get("coupon_valid_to")
                    if not coupon_type or not coupon_value or not coupon_description:
                        flash("Coupon-Typ, Wert und Beschreibung sind erforderlich.", "error")
                        return redirect(url_for("create_proposal"))
                    proposal.proposed_coupon_type = coupon_type
                    proposal.proposed_coupon_value = float(coupon_value)
                    proposal.proposed_coupon_description = coupon_description
                    proposal.shop_id = int(coupon_shop_id) if coupon_shop_id else None
                    proposal.program_id = int(coupon_program_id) if coupon_program_id else None
                    if coupon_combinable == "yes":
                        proposal.proposed_coupon_combinable = True
                    elif coupon_combinable == "no":
                        proposal.proposed_coupon_combinable = False
                    else:
                        proposal.proposed_coupon_combinable = None
                    if coupon_valid_to:
                        proposal.proposed_coupon_valid_to = datetime.strptime(
                            coupon_valid_to, "%Y-%m-%d"
                        )

                db.session.add(proposal)
                db.session.commit()
                db.session.add(
                    ProposalAuditTrail(
                        proposal_id=proposal.id,
                        action="created",
                        actor_id=current_user.id,
                    )
                )
                db.session.commit()
                flash("Vorschlag erfolgreich eingereicht!", "success")
                return redirect(url_for("proposals"))

            if proposal_type == "metadata_edit":
                shop_id = request.form.get("metadata_shop_id")
                if not shop_id:
                    flash("Bitte einen Shop auswählen.", "error")
                    return redirect(url_for("create_proposal"))
                shop = db.session.get(Shop, int(shop_id))
                if not shop or not shop.shop_main_id:
                    flash("Shop konnte nicht gefunden werden oder ist nicht verknüpft.", "error")
                    return redirect(url_for("create_proposal"))
                proposed_name = request.form.get("metadata_name") or None
                proposed_website = request.form.get("metadata_website") or None
                proposed_logo = request.form.get("metadata_logo") or None
                if not any([proposed_name, proposed_website, proposed_logo]):
                    flash("Bitte mindestens Name, Website oder Logo angeben.", "error")
                    return redirect(url_for("create_proposal"))
                metadata_proposal = ShopMetadataProposal(
                    shop_main_id=shop.shop_main_id,
                    proposed_name=proposed_name,
                    proposed_website=proposed_website,
                    proposed_logo_url=proposed_logo,
                    reason=reason if reason else None,
                    proposed_by_user_id=current_user.id,
                    status="PENDING",
                )
                db.session.add(metadata_proposal)
                db.session.commit()
                flash("Metadaten-Vorschlag erfolgreich eingereicht!", "success")
                return redirect(url_for("proposals"))

            if proposal_type == "merge_request":
                source_shop_id = request.form.get("merge_source_shop_id")
                target_shop_id = request.form.get("merge_target_shop_id")
                if not source_shop_id or not target_shop_id:
                    flash("Bitte beide Shops für den Merge auswählen.", "error")
                    return redirect(url_for("create_proposal"))
                source_shop = db.session.get(Shop, int(source_shop_id)) if source_shop_id else None
                target_shop = db.session.get(Shop, int(target_shop_id)) if target_shop_id else None
                if not source_shop or not target_shop:
                    flash("Shop-Auswahl ungültig.", "error")
                    return redirect(url_for("create_proposal"))
                if source_shop.id == target_shop.id:
                    flash("Bitte zwei unterschiedliche Shops auswählen.", "error")
                    return redirect(url_for("create_proposal"))
                if not source_shop.shop_main_id or not target_shop.shop_main_id:
                    flash("Beide Shops müssen bereits verknüpft sein.", "error")
                    return redirect(url_for("create_proposal"))
                variant_a = ensure_variant_for_shop(source_shop)
                variant_b = ensure_variant_for_shop(target_shop)
                merge_proposal = ShopMergeProposal(
                    variant_a_id=variant_a.id,
                    variant_b_id=variant_b.id,
                    proposed_by_user_id=current_user.id,
                    reason=reason if reason else None,
                    status="PENDING",
                )
                db.session.add(merge_proposal)
                db.session.commit()
                flash("Merge-Vorschlag erfolgreich eingereicht!", "success")
                return redirect(url_for("proposals"))

            flash("Ungültiger Beitragstyp.", "error")
            return redirect(url_for("create_proposal"))

        shops = Shop.query.all()
        programs = BonusProgram.query.all()
        return render_template("create_proposal.html", shops=shops, programs=programs)

    @app.route("/review-scraper-proposal/<int:proposal_id>", methods=["GET", "POST"])
    @login_required
    def review_scraper_proposal(proposal_id):
        scraper_proposal = Proposal.query.get_or_404(proposal_id)
        if scraper_proposal.source != "scraper":
            flash("Dies ist kein Scraper-Vorschlag.", "error")
            return redirect(url_for("proposals"))

        if request.method == "POST":
            proposal_type = scraper_proposal.proposal_type
            user_proposal = Proposal(
                proposal_type=proposal_type,
                status="pending",
                source="user",
                user_id=current_user.id,
                shop_id=scraper_proposal.shop_id,
                program_id=scraper_proposal.program_id,
                reason=f"User review of scraper proposal #{scraper_proposal.id}: {request.form.get('reason', '')}",
            )
            if proposal_type == "rate_change":
                user_proposal.proposed_points_per_eur = request.form.get(
                    "points_per_eur", scraper_proposal.proposed_points_per_eur
                )
                user_proposal.proposed_cashback_pct = request.form.get(
                    "cashback_pct", scraper_proposal.proposed_cashback_pct
                )
            elif proposal_type == "shop_add":
                user_proposal.proposed_name = request.form.get(
                    "name", scraper_proposal.proposed_name
                )
            elif proposal_type == "program_add":
                user_proposal.proposed_name = request.form.get(
                    "name", scraper_proposal.proposed_name
                )
                user_proposal.proposed_point_value_eur = request.form.get(
                    "point_value_eur", scraper_proposal.proposed_point_value_eur
                )
            elif proposal_type == "coupon_add":
                user_proposal.proposed_coupon_type = request.form.get(
                    "coupon_type", scraper_proposal.proposed_coupon_type
                )
                user_proposal.proposed_coupon_value = request.form.get(
                    "coupon_value", scraper_proposal.proposed_coupon_value
                )
                user_proposal.proposed_coupon_description = request.form.get(
                    "coupon_description", scraper_proposal.proposed_coupon_description
                )
                user_proposal.proposed_coupon_combinable = request.form.get(
                    "coupon_combinable", scraper_proposal.proposed_coupon_combinable
                )
                user_proposal.proposed_coupon_valid_to = request.form.get(
                    "coupon_valid_to", scraper_proposal.proposed_coupon_valid_to
                )
            db.session.add(user_proposal)
            scraper_proposal.status = "approved"
            db.session.commit()
            flash("✓ Ihr Vorschlag wurde eingereicht!", "success")
            return redirect(url_for("proposals"))

        return render_template("review_scraper_proposal.html", proposal=scraper_proposal)

    return app
