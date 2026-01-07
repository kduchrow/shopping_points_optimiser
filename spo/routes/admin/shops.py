"""Admin shop management, merge, metadata, and comments routes."""

from datetime import UTC, datetime

from flask import flash, jsonify, redirect, request, url_for
from flask_login import current_user, login_required

from spo.extensions import db
from spo.models import (
    BonusProgram,
    Coupon,
    Proposal,
    ProposalAuditTrail,
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
    notify_metadata_approved,
    notify_metadata_rejected,
    notify_rate_comment,
)


def register_admin_shops(app):
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
        notify_metadata_approved(proposal)
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
        notify_metadata_rejected(proposal, reason)
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
            if request.headers.get("Accept") == "application/json":
                return jsonify({"error": "Unauthorized"}), 403
            flash("Sie haben keine Berechtigung für diese Aktion.", "error")
            return redirect(url_for("admin"))

        try:
            # Count what will be deleted
            shop_main_count = ShopMain.query.count()
            shop_count = Shop.query.count()
            variant_count = ShopVariant.query.count()
            rate_count = ShopProgramRate.query.count()
            merge_proposal_count = ShopMergeProposal.query.count()
            metadata_proposal_count = ShopMetadataProposal.query.count()

            # Delete in correct order to avoid FK constraint violations
            # 1. Delete ShopMergeProposal (references ShopVariant)
            ShopMergeProposal.query.delete()

            # 2. Delete ShopMetadataProposal (references both Shop and ShopMain)
            ShopMetadataProposal.query.delete()

            # 3. Delete ProposalAuditTrail (references Proposal)
            ProposalAuditTrail.query.delete()

            # 4. Delete Proposal (references Shop)
            Proposal.query.delete()

            # 5. Delete Coupon (references Shop)
            Coupon.query.delete()

            # 6. Delete ShopProgramRate (references Shop)
            ShopProgramRate.query.delete()

            # 7. Delete Shop entries (references ShopMain)
            Shop.query.delete()

            # 8. Delete ShopVariant (references ShopMain)
            ShopVariant.query.delete()

            # 9. Delete ShopMain
            ShopMain.query.delete()

            db.session.commit()

            db.session.add(
                ScrapeLog(
                    message=f"Admin cleared {shop_main_count} ShopMains, {shop_count} Shops, {variant_count} variants, {rate_count} rates, {merge_proposal_count} merge proposals, {metadata_proposal_count} metadata proposals"
                )
            )
            db.session.commit()

            if request.headers.get("Accept") == "application/json":
                return jsonify({"success": True, "deleted": shop_main_count})

            flash(
                f"✅ {shop_main_count} ShopMains, {shop_count} Shops, {variant_count} Varianten gelöscht.",
                "success",
            )
            return redirect(url_for("admin"))
        except Exception as e:
            db.session.rollback()
            if request.headers.get("Accept") == "application/json":
                return jsonify({"error": str(e)}), 500
            flash(f"❌ Fehler beim Löschen: {str(e)}", "error")
            return redirect(url_for("admin"))

    return app
