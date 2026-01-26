from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from spo.extensions import db
from spo.models import (
    BonusProgram,
    Coupon,
    Proposal,
    Shop,
    ShopMain,
    ShopMetadataProposal,
    ShopProgramRate,
)
from spo.utils import ensure_variant_for_shop


def register_public(app):
    @app.route("/shop_names", methods=["GET"])
    def shop_names():
        # API: Liefert Shop-Namen für das Dropdown, gefiltert nach Query-String
        q = request.args.get("q", "").strip().lower()
        limit = 30
        query = ShopMain.query.filter_by(status="active")
        if q:
            query = query.filter(ShopMain.canonical_name_lower.contains(q))
        shop_mains = query.order_by(ShopMain.canonical_name).limit(limit).all()
        # Hole jeweils den ersten aktiven Shop für die ID
        result = []
        for shop_main in shop_mains:
            shop = Shop.query.filter_by(shop_main_id=shop_main.id).first()
            if not shop:
                continue
            result.append({"id": shop.id, "name": shop_main.canonical_name})
        return result

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/evaluate", methods=["POST"])
    def evaluate():
        # Handle calculation logic for selected shop
        shop_id = request.form.get("shop", type=int)
        raw_amount = (request.form.get("amount") or "").strip()
        include_my_proposals = request.form.get("include_my_proposals") == "on"
        try:
            amount = float(raw_amount) if raw_amount else None
        except (TypeError, ValueError):
            amount = None
        mode = request.form.get("mode", default="shopping")
        shop = db.session.get(Shop, shop_id) if shop_id else None
        shop_coupons = []
        if shop:
            # Get coupons for this shop or global coupons (shop_id is NULL)
            from sqlalchemy import or_

            shop_coupons = Coupon.query.filter(
                or_(Coupon.shop_id == shop.id, Coupon.shop_id.is_(None))
            ).all()

            # Show own pending coupon proposals
            if current_user.is_authenticated and include_my_proposals:
                from types import SimpleNamespace

                coupon_proposals = Proposal.query.filter(
                    Proposal.user_id == current_user.id,
                    Proposal.shop_id == shop.id,
                    Proposal.proposal_type == "coupon_add",
                    Proposal.status == "pending",
                ).all()

                for p in coupon_proposals:
                    # Only include proposals that define coupon details
                    if p.proposed_coupon_type is None or p.proposed_coupon_value is None:
                        continue

                    # Create pseudo-coupon from proposal
                    pseudo_coupon = SimpleNamespace(
                        id=f"proposal-{p.id}",
                        name=f"{p.proposed_coupon_description or 'Dein Coupon-Vorschlag'}",
                        coupon_type=p.proposed_coupon_type,
                        value=p.proposed_coupon_value,
                        description=p.proposed_coupon_description or "",
                        shop_id=shop.id,
                        shop=shop,
                        program_id=p.program_id,
                        program=(
                            db.session.get(BonusProgram, p.program_id) if p.program_id else None
                        ),
                        valid_to=p.proposed_coupon_valid_to,
                        combinable=p.proposed_coupon_combinable,
                        selected=False,
                        is_proposal=True,
                        proposal_status=p.status,
                    )
                    shop_coupons.append(pseudo_coupon)

        if not shop:
            return redirect(url_for("index"))
        # Use all sibling shops for this ShopMain to ensure all rates (e.g. Payback) are included
        shop_ids = [s.id for s in Shop.query.filter_by(shop_main_id=shop.shop_main_id).all()]
        rates = ShopProgramRate.query.filter(
            ShopProgramRate.shop_id.in_(shop_ids), ShopProgramRate.valid_to.is_(None)
        ).all()

        # Show own pending proposals for this shop only to the submitting user
        if current_user.is_authenticated and include_my_proposals:
            user_proposals = Proposal.query.filter(
                Proposal.user_id == current_user.id,
                Proposal.shop_id == shop.id,
                Proposal.proposal_type == "rate_change",
                Proposal.program_id.isnot(None),
                Proposal.status == "pending",
            ).all()
            from types import SimpleNamespace

            for p in user_proposals:
                # Only include proposals that define a numeric rate
                if p.proposed_points_per_eur is None and p.proposed_cashback_pct is None:
                    continue
                rates.append(
                    SimpleNamespace(
                        id=f"proposal-{p.id}",
                        shop_id=shop.id,
                        program_id=p.program_id,
                        points_per_eur=p.proposed_points_per_eur or 0.0,
                        points_absolute=None,
                        cashback_pct=p.proposed_cashback_pct or 0.0,
                        cashback_absolute=None,
                        rate_note="Dein Vorschlag (wartet auf Freigabe)",
                        rate_type=p.proposed_rate_type or "shop",
                        category_obj=None,
                        valid_to=None,
                        is_proposal=True,
                        proposal_status=p.status,
                    )
                )
        has_coupons = bool(shop_coupons)
        # Get selected coupon IDs from form (may be multiple, includes both "123" and "proposal-123" formats)
        selected_coupon_ids = request.form.getlist("coupon_ids")
        selected_coupon_ids_set = set()
        for cid in selected_coupon_ids:
            if cid.startswith("proposal-"):
                selected_coupon_ids_set.add(cid)  # Keep as string for proposals
            elif cid.isdigit():
                selected_coupon_ids_set.add(int(cid))  # Convert to int for regular coupons
        selected_coupon_ids = selected_coupon_ids_set
        # Only set default best coupon selection on initial page load (not AJAX)
        if not selected_coupon_ids and request.headers.get("X-Requested-With") != "XMLHttpRequest":
            # For each program, select the best coupon (prefer multiplier, then highest value),
            # and also select the best global coupon (program_id is None) if available.
            best_coupons = set()
            # Find all program IDs in use
            program_ids = set(c.program_id for c in shop_coupons if c.program_id is not None)
            # For each program, pick best coupon
            for pid in program_ids:
                best = None
                for c in shop_coupons:
                    if c.program_id == pid:
                        if not best:
                            best = c
                        elif c.coupon_type == "multiplier" and best.coupon_type != "multiplier":
                            best = c
                        elif c.coupon_type == best.coupon_type and c.value > best.value:
                            best = c
                if best:
                    best_coupons.add(best.id)
            # Also pick the best global coupon (program_id is None)
            best_global = None
            for c in shop_coupons:
                if c.program_id is None:
                    if not best_global:
                        best_global = c
                    elif c.coupon_type == "multiplier" and best_global.coupon_type != "multiplier":
                        best_global = c
                    elif c.coupon_type == best_global.coupon_type and c.value > best_global.value:
                        best_global = c
            if best_global:
                best_coupons.add(best_global.id)
            selected_coupon_ids = best_coupons
        if mode == "shopping":
            shopping_rates = [r for r in rates if getattr(r, "rate_type", "shop") != "contract"]
            # Mark selected coupons for template
            for c in shop_coupons:
                c.selected = c.id in selected_coupon_ids

            if amount is None:
                program_map = {}
                for rate in shopping_rates:
                    program = db.session.get(BonusProgram, rate.program_id)
                    if not program:
                        continue
                    category_name = None
                    if hasattr(rate, "category_obj") and rate.category_obj is not None:
                        try:
                            category_name = rate.category_obj.name
                        except Exception:
                            category_name = None
                    prog = program_map.setdefault(
                        program.name, {"program": program.name, "categories": []}
                    )
                    entry = {
                        "rate_id": rate.id,
                        "category": category_name,
                        "sub_category": getattr(rate, "sub_category", None),
                        "points_per_eur": rate.points_per_eur,
                        "points_absolute": rate.points_absolute,
                        "cashback_pct": rate.cashback_pct,
                        "cashback_absolute": rate.cashback_absolute,
                        "rate_type": getattr(rate, "rate_type", None),
                        "is_proposal": getattr(rate, "is_proposal", False),
                        "proposal_status": getattr(rate, "proposal_status", None),
                    }
                    prog["categories"].append(entry)
                programs_list = sorted(program_map.values(), key=lambda p: p["program"])
                return render_template(
                    "result.html",
                    mode="shopping",
                    shop=shop,
                    amount=None,
                    grouped_results=programs_list,
                    has_coupons=has_coupons,
                    active_coupons=shop_coupons,
                    combine_coupons=False,
                    include_my_proposals=include_my_proposals,
                )

            program_map = {}
            for rate in shopping_rates:
                program = db.session.get(BonusProgram, rate.program_id)
                if not program:
                    continue
                # Defensive: Only use non-None values for calculations
                base_points = (
                    amount * rate.points_per_eur if rate.points_per_eur is not None else 0.0
                )
                base_points_abs = rate.points_absolute if rate.points_absolute is not None else 0.0
                base_cashback = (
                    amount * (rate.cashback_pct / 100.0) if rate.cashback_pct is not None else 0.0
                )
                base_cashback_abs = (
                    rate.cashback_absolute if rate.cashback_absolute is not None else 0.0
                )
                # Sum all possible values
                total_points = base_points + base_points_abs
                total_cashback = base_cashback + base_cashback_abs
                base_euros = total_points * program.point_value_eur + total_cashback
                # Only apply coupons that are global (program_id is None) or match the current program
                program_coupons = [
                    c
                    for c in shop_coupons
                    if (c.program_id is None or c.program_id == program.id)
                    and c.id in selected_coupon_ids
                ]
                # Apply all selected coupons: multiply all multipliers, add all discounts
                total_multiplier = 1.0
                total_discount = 0.0
                multipliers = []
                discounts = []
                for c in program_coupons:
                    if c.coupon_type == "multiplier":
                        total_multiplier *= c.value
                        multipliers.append(f"{c.value}x")
                    elif c.coupon_type == "discount":
                        total_discount += c.value
                        discounts.append(f"-{c.value}%")
                coupon_points = total_points * total_multiplier
                coupon_cashback = total_cashback + (amount * (total_discount / 100.0))
                coupon_euros = coupon_points * program.point_value_eur + coupon_cashback
                coupon_info = None
                if total_multiplier != 1.0 or total_discount != 0.0:
                    coupon_info = {
                        "euros": round(coupon_euros, 2),
                        "points": round(coupon_points, 2),
                        "multipliers": multipliers,
                        "discounts": discounts,
                        "unknown_combinability": False,
                    }
                category_name = None
                if hasattr(rate, "category_obj") and rate.category_obj is not None:
                    try:
                        category_name = rate.category_obj.name
                    except Exception:
                        category_name = None
                prog = program_map.setdefault(
                    program.name,
                    {"program": program.name, "best_value": 0.0, "categories": []},
                )
                entry = {
                    "rate_id": rate.id,
                    "category": category_name,
                    "sub_category": getattr(rate, "sub_category", None),
                    "points": round(total_points, 2),
                    "points_absolute": base_points_abs,
                    "cashback_rate": rate.cashback_pct,
                    "cashback": round(total_cashback, 2),
                    "cashback_absolute": base_cashback_abs,
                    "euros": round(base_euros, 2),
                    "coupon_info": coupon_info,
                    "is_proposal": getattr(rate, "is_proposal", False),
                    "proposal_status": getattr(rate, "proposal_status", None),
                }
                prog["categories"].append(entry)
                value_for_sort = coupon_info["euros"] if coupon_info else entry["euros"]
                if value_for_sort > prog["best_value"]:
                    prog["best_value"] = value_for_sort
            programs_list = sorted(
                program_map.values(), key=lambda p: p["best_value"], reverse=True
            )
            # If AJAX, return only the results list HTML
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                rendered = render_template(
                    "result.html",
                    mode="shopping",
                    shop=shop,
                    amount=amount,
                    grouped_results=programs_list,
                    has_coupons=has_coupons,
                    active_coupons=shop_coupons,
                    combine_coupons=False,
                    include_my_proposals=include_my_proposals,
                )
                # Extract only the results-list HTML
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(rendered, "html.parser")
                results_list = soup.find(id="results-list")
                return str(results_list)
            return render_template(
                "result.html",
                mode="shopping",
                shop=shop,
                amount=amount,
                grouped_results=programs_list,
                has_coupons=has_coupons,
                active_coupons=shop_coupons,
                combine_coupons=False,
                include_my_proposals=include_my_proposals,
            )
        # VOUCHER MODE COMMENTED OUT
        # elif mode == "voucher":
        #     rates = ShopProgramRate.query.filter(
        #         ShopProgramRate.shop_id.in_(shop_ids), ShopProgramRate.valid_to.is_(None), ShopProgramRate.rate_type == "voucher"
        #     ).all()
        #     voucher = float(request.form.get("voucher") or 0)
        #     results = []
        #     for rate in rates:
        #         program = db.session.get(BonusProgram, rate.program_id)
        #         if not program or program.point_value_eur is None:
        #             continue
        #         req_points = (
        #             voucher / program.point_value_eur
        #             if program.point_value_eur > 0
        #             else float("inf")
        #         )
        #         spend = (
        #             req_points / rate.points_per_eur if rate.points_per_eur > 0 else float("inf")
        #         )
        #         results.append(
        #             {
        #                 "program": program.name if program else "?",
        #                 "spend": round(spend, 2),
        #                 "req_points": round(req_points, 2),
        #             }
        #         )
        #     results.sort(key=lambda r: r["spend"])
        #     return render_template(
        #         "result.html", mode="voucher", shop=shop, voucher=voucher, results=results
        #     )
        elif mode == "voucher":
            # Voucher mode is currently disabled
            flash("Gutschein-Modus ist derzeit nicht verfügbar.", "error")
            return redirect(url_for("index"))
        elif mode == "contract":
            # Filter only contract-type rates
            contract_rates = [r for r in rates if getattr(r, "rate_type", "shop") == "contract"]
            results = []
            for rate in contract_rates:
                program = db.session.get(BonusProgram, rate.program_id)
                if not program:
                    continue
                # Build bonus description
                bonus_parts = []
                if rate.points_absolute:
                    bonus_parts.append(f"{rate.points_absolute:.0f} Punkte")
                if rate.points_per_eur:
                    bonus_parts.append(f"{rate.points_per_eur} P/EUR")
                if rate.cashback_absolute:
                    bonus_parts.append(f"{rate.cashback_absolute}€ Cashback")
                if rate.cashback_pct:
                    bonus_parts.append(f"{rate.cashback_pct}% Cashback")

                bonus_text = " + ".join(bonus_parts) if bonus_parts else "Siehe Admin für Details"
                results.append(
                    {
                        "program": program.name if program else "?",
                        "bonus": bonus_text,
                        "note": rate.rate_note or "",
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
                proposal = ShopMetadataProposal()
                proposal.shop_main_id = shop.shop_main_id
                proposal.proposed_name = proposed_name
                proposal.proposed_website = proposed_website
                proposal.proposed_logo_url = proposed_logo
                proposal.reason = request.form.get("reason") or None
                proposal.proposed_by_user_id = current_user.id
                proposal.status = "PENDING"
                db.session.add(proposal)
                db.session.commit()
                message = "Dein Metadaten-Vorschlag wurde eingereicht."

            if action == "rate":
                program_id = request.form.get("program_id")
                rate_type = request.form.get("rate_type", "cashback")
                points_per_eur = request.form.get("points_per_eur")
                cashback_pct = request.form.get("cashback_pct")
                reason = request.form.get("reason") or None
                if not program_id:
                    flash("Bitte Programm wählen.", "error")
                elif rate_type == "cashback":
                    if not cashback_pct:
                        flash("Bitte Cashback-Prozentsatz angeben.", "error")
                    else:
                        from spo.models import Proposal

                        proposal = Proposal()
                        proposal.proposal_type = "rate_change"
                        proposal.user_id = current_user.id
                        proposal.shop_id = shop.id
                        proposal.program_id = int(program_id)
                        proposal.proposed_cashback_pct = float(cashback_pct)
                        proposal.proposed_points_per_eur = 0.0
                        proposal.reason = reason
                        db.session.add(proposal)
                        db.session.commit()
                        message = "Dein Rate-Vorschlag wurde eingereicht."
                elif rate_type == "points":
                    if not points_per_eur:
                        flash("Bitte Points/EUR angeben.", "error")
                    else:
                        from spo.models import Proposal

                        proposal = Proposal()
                        proposal.proposal_type = "rate_change"
                        proposal.user_id = current_user.id
                        proposal.shop_id = shop.id
                        proposal.program_id = int(program_id)
                        proposal.proposed_points_per_eur = float(points_per_eur)
                        proposal.proposed_cashback_pct = 0.0
                        proposal.reason = reason
                        db.session.add(proposal)
                        db.session.commit()
                        message = "Dein Rate-Vorschlag wurde eingereicht."

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
        programs = BonusProgram.query.order_by(BonusProgram.name).all()
        return render_template(
            "suggest_shop.html", shop=shop, main=main, shops=shops, programs=programs
        )

    @app.route("/health", methods=["GET"])
    def health():
        return "OK"

    return app
