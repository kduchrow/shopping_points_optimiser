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
)
from spo.utils import ensure_variant_for_shop


def register_public(app):
    @app.route("/", methods=["GET"])
    def index():
        # Show shop selection page with all active shops and support flags
        shop_mains = (
            ShopMain.query.filter_by(status="active").order_by(ShopMain.canonical_name).all()
        )
        shops_data = []
        for shop_main in shop_mains:
            # Aggregate support flags across all Shops for this ShopMain
            sibling_shops = Shop.query.filter_by(shop_main_id=shop_main.id).all()
            if not sibling_shops:
                continue
            all_rates = ShopProgramRate.query.filter(
                ShopProgramRate.shop_id.in_([s.id for s in sibling_shops]),
                ShopProgramRate.valid_to.is_(None),
            ).all()
            supports_shopping = any(
                (r.points_per_eur or 0) > 0 or (r.cashback_pct or 0) > 0 for r in all_rates
            )
            supports_voucher = any((r.points_per_eur or 0) > 0 for r in all_rates)
            supports_contract = any(
                (r.points_per_eur or 0) == 0 and (r.cashback_pct or 0) == 0 for r in all_rates
            )
            # Use the first Shop for id (legacy: one-to-many)
            shop = sibling_shops[0]
            shops_data.append(
                {
                    "id": shop.id,
                    "name": shop_main.canonical_name,
                    "supports_shopping": supports_shopping,
                    "supports_voucher": supports_voucher,
                    "supports_contract": supports_contract,
                }
            )
        return render_template("index.html", shops_data=shops_data)

    @app.route("/evaluate", methods=["POST"])
    def evaluate():
        # Handle calculation logic for selected shop
        shop_id = request.form.get("shop", type=int)
        amount = request.form.get("amount", type=float, default=100.0)
        mode = request.form.get("mode", default="shopping")
        shop = Shop.query.get(shop_id) if shop_id else None
        shop_coupons = []
        if shop:
            shop_coupons = Coupon.query.filter_by(shop_id=shop.id).all()
        if not shop:
            return redirect(url_for("index"))
        shop_ids = [shop.id]
        rates = ShopProgramRate.query.filter(
            ShopProgramRate.shop_id.in_(shop_ids), ShopProgramRate.valid_to.is_(None)
        ).all()
        has_coupons = bool(shop_coupons)
        if mode == "shopping":
            program_map = {}
            for rate in rates:
                program = db.session.get(BonusProgram, rate.program_id)
                if not program:
                    continue
                base_points = amount * rate.points_per_eur
                base_cashback = amount * (rate.cashback_pct / 100.0)
                base_euros = base_points * program.point_value_eur + base_cashback
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
                category_name = None
                if hasattr(rate, "category_obj") and rate.category_obj is not None:
                    try:
                        category_name = rate.category_obj.name
                    except Exception:
                        category_name = None
                prog = program_map.setdefault(
                    program.name, {"program": program.name, "best_value": 0.0, "categories": []}
                )
                entry = {
                    "rate_id": rate.id,
                    "category": category_name,
                    "sub_category": getattr(rate, "sub_category", None),
                    "points": round(base_points, 2),
                    "cashback": round(base_cashback, 2),
                    "euros": round(base_euros, 2),
                    "coupon_info": coupon_info,
                }
                prog["categories"].append(entry)
                value_for_sort = coupon_info["euros"] if coupon_info else entry["euros"]
                if value_for_sort > prog["best_value"]:
                    prog["best_value"] = value_for_sort
            programs_list = sorted(
                program_map.values(), key=lambda p: p["best_value"], reverse=True
            )
            return render_template(
                "result.html",
                mode="shopping",
                shop=shop,
                amount=amount,
                grouped_results=programs_list,
                has_coupons=has_coupons,
                active_coupons=shop_coupons,
            )
        elif mode == "voucher":
            voucher = float(request.form.get("voucher") or 0)
            results = []
            for rate in rates:
                program = db.session.get(BonusProgram, rate.program_id)
                if not program or program.point_value_eur is None:
                    continue
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
                        "program": program.name if program else "?",
                        "spend": round(spend, 2),
                        "req_points": round(req_points, 2),
                    }
                )
            results.sort(key=lambda r: r["spend"])
            return render_template(
                "result.html", mode="voucher", shop=shop, voucher=voucher, results=results
            )
        elif mode == "contract":
            results = []
            for rate in rates:
                program = db.session.get(BonusProgram, rate.program_id)
                if not program:
                    continue
                results.append(
                    {
                        "program": program.name if program else "?",
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
                    proposal = ShopMetadataProposal()
                    proposal.shop_main_id = shop.shop_main_id
                    proposal.proposed_name = proposed_name
                    proposal.proposed_website = proposed_website
                    proposal.proposed_logo_url = proposed_logo
                    proposal.reason = reason
                    proposal.proposed_by_user_id = current_user.id
                    proposal.status = "PENDING"
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
                        proposal = ShopMergeProposal()
                        proposal.variant_a_id = variant_a.id
                        proposal.variant_b_id = variant_b.id
                        proposal.proposed_by_user_id = current_user.id
                        proposal.reason = merge_reason
                        proposal.status = "PENDING"
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
