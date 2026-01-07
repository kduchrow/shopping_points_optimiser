from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from spo.extensions import db
from spo.models import (
    BonusProgram,
    Coupon,
    Shop,
    ShopMain,
    ShopMetadataProposal,
    ShopProgramRate,
    utcnow,
)
from spo.utils import ensure_variant_for_shop


def register_public(app):
    @app.route("/", methods=["GET"])
    def index():
        # Get all ShopMain entries to avoid showing duplicate shops
        # Use ShopMain as the source of truth, then find the associated Shop entry
        shop_mains = (
            ShopMain.query.filter_by(status="active").order_by(ShopMain.canonical_name).all()
        )
        shops_data = []

        for shop_main in shop_mains:
            # Collect all Shop entries under this ShopMain
            shops = Shop.query.filter_by(shop_main_id=shop_main.id).all()
            if not shops:
                continue  # Skip if no Shop is linked yet

            # Compute support flags across all sibling shops
            shop_ids = [s.id for s in shops]
            rates = ShopProgramRate.query.filter(
                ShopProgramRate.shop_id.in_(shop_ids), ShopProgramRate.valid_to.is_(None)
            ).all()
            supports_shopping_voucher = any(r.points_per_eur > 0 for r in rates)
            supports_contract = True

            shops_data.append(
                {
                    # Use the first Shop.id for backwards compatibility with evaluate route
                    "id": shops[0].id,
                    "name": shop_main.canonical_name,  # Use canonical name from ShopMain
                    "supports_shopping": supports_shopping_voucher,
                    "supports_voucher": supports_shopping_voucher,
                    "supports_contract": supports_contract,
                }
            )

        return render_template("index.html", shops_data=shops_data)

    @app.route("/evaluate", methods=["POST"])
    def evaluate():
        mode = request.form.get("mode")
        shop_id = int(request.form.get("shop"))
        shop = db.session.get(Shop, shop_id)

        shop_ids = [shop.id]
        if shop and shop.shop_main_id:
            siblings = Shop.query.filter_by(shop_main_id=shop.shop_main_id).all()
            shop_ids = [s.id for s in siblings]

        now = utcnow()
        shop_coupons = Coupon.query.filter(
            db.or_(Coupon.shop_id.in_(shop_ids), Coupon.shop_id.is_(None)),
            Coupon.status == "active",
            Coupon.valid_from <= now,
            Coupon.valid_to >= now,
        ).all()

        if mode == "shopping":
            amount = float(request.form.get("amount") or 0)
            results = []
            rates = ShopProgramRate.query.filter(
                ShopProgramRate.shop_id.in_(shop_ids),
                ShopProgramRate.valid_to.is_(None),
            ).all()
            has_coupons = bool(shop_coupons)
            for rate in rates:
                program = db.session.get(BonusProgram, rate.program_id)
                # Base values without coupons
                base_points = amount * rate.points_per_eur
                base_cashback = amount * (rate.cashback_pct / 100.0)
                base_euros = base_points * program.point_value_eur + base_cashback

                # Apply best available coupon for this program (if any)
                program_coupons = [c for c in shop_coupons if c.program_id in (None, program.id)]
                best_coupon = max(
                    (c.value for c in program_coupons if c.coupon_type == "multiplier"), default=1
                )
                best_discount = max(
                    (c.value for c in program_coupons if c.coupon_type == "discount"), default=0
                )
                coupon_points = base_points * best_coupon
                coupon_cashback = base_cashback + (amount * (best_discount / 100.0))
                coupon_euros = coupon_points * program.point_value_eur + coupon_cashback

                coupon_info = None
                if best_coupon != 1 or best_discount != 0:
                    coupon_info = {
                        "euros": round(coupon_euros, 2),
                        "points": round(coupon_points, 2),
                        "multipliers": [f"{best_coupon}x"] if best_coupon != 1 else [],
                        "discounts": [f"-{best_discount}%"] if best_discount != 0 else [],
                        "unknown_combinability": False,
                    }
                results.append(
                    {
                        "program": program.name,
                        "points": round(base_points, 2),
                        "euros": round(base_euros, 2),
                        "coupon_info": coupon_info,
                    }
                )
            results.sort(
                key=lambda r: r["coupon_info"]["euros"] if r.get("coupon_info") else r["euros"],
                reverse=True,
            )
            return render_template(
                "result.html",
                mode="shopping",
                shop=shop,
                amount=amount,
                results=results,
                has_coupons=has_coupons,
                active_coupons=shop_coupons,
            )

        if mode == "voucher":
            voucher = float(request.form.get("voucher") or 0)
            results = []
            rates = ShopProgramRate.query.filter_by(shop_id=shop.id, valid_to=None).all()
            for rate in rates:
                program = db.session.get(BonusProgram, rate.program_id)
                req_points = (
                    voucher / program.point_value_eur
                    if program.point_value_eur > 0
                    else float("inf")
                )
                spend = (
                    req_points / rate.points_per_eur if rate.points_per_eur > 0 else float("inf")
                )
                results.append(
                    {
                        "program": program.name,
                        "spend": round(spend, 2),
                        "req_points": round(req_points, 2),
                    }
                )
            results.sort(key=lambda r: r["spend"])
            return render_template(
                "result.html", mode="voucher", shop=shop, voucher=voucher, results=results
            )

        results = []
        rates = ShopProgramRate.query.filter_by(shop_id=shop.id, valid_to=None).all()
        for rate in rates:
            program = db.session.get(BonusProgram, rate.program_id)
            results.append(
                {
                    "program": program.name,
                    "note": "Vertragsabschluss - siehe Admin für genaue Angaben",
                }
            )
        return render_template("result.html", mode="contract", shop=shop, results=results)

    @app.route("/shop/<int:shop_id>/suggest", methods=["GET", "POST"])
    @login_required
    def suggest_shop(shop_id):
        shop = Shop.query.get_or_404(shop_id)
        main = db.session.get(ShopMain, shop.shop_main_id) if shop.shop_main_id else None
        message = None

        if request.method == "POST":
            action = request.form.get("action")
            if action == "metadata":
                proposed_name = request.form.get("proposed_name") or None
                proposed_website = request.form.get("proposed_website") or None
                proposed_logo = request.form.get("proposed_logo") or None
                reason = request.form.get("reason") or None
                if not any([proposed_name, proposed_website, proposed_logo]):
                    flash("Bitte mindestens ein Feld ausfüllen (Name, Website oder Logo).", "error")
                else:
                    proposal = ShopMetadataProposal(
                        shop_main_id=shop.shop_main_id,
                        proposed_name=proposed_name,
                        proposed_website=proposed_website,
                        proposed_logo_url=proposed_logo,
                        reason=reason,
                        proposed_by_user_id=current_user.id,
                        status="PENDING",
                    )
                    db.session.add(proposal)
                    db.session.commit()
                    message = "Dein Metadaten-Vorschlag wurde eingereicht."

            if action == "merge":
                merge_shop_id = request.form.get("merge_shop_id")
                merge_reason = request.form.get("merge_reason")
                if merge_shop_id:
                    try:
                        merge_shop_id = int(merge_shop_id)
                        target_shop = db.session.get(Shop, merge_shop_id)
                    except Exception:
                        target_shop = None
                    if not target_shop or not target_shop.shop_main_id:
                        flash("Zielshop ungültig.", "error")
                    else:
                        from spo.models import ShopMergeProposal

                        variant_a = ensure_variant_for_shop(shop)
                        variant_b = ensure_variant_for_shop(target_shop)
                        proposal = ShopMergeProposal(
                            variant_a_id=variant_a.id,
                            variant_b_id=variant_b.id,
                            proposed_by_user_id=current_user.id,
                            reason=merge_reason,
                            status="PENDING",
                        )
                        db.session.add(proposal)
                        db.session.commit()
                        message = "Dein Merge-Vorschlag wurde eingereicht."
                else:
                    flash("Bitte Zielshop auswählen.", "error")

            if message:
                flash(message, "success")
                return redirect(url_for("suggest_shop", shop_id=shop_id))

        shops = Shop.query.order_by(Shop.name).all()
        return render_template("suggest_shop.html", shop=shop, main=main, shops=shops)

    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    return app
