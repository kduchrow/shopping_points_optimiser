"""API endpoints for browser extension."""

from flask import jsonify, request
from flask_login import current_user

from spo.extensions import db
from spo.models.proposals import ShopURLProposal
from spo.models.rates import ShopProgramRate
from spo.models.shops import Shop


def register_api_routes(app):
    """Register API routes for the browser extension."""

    @app.after_request
    def after_request(response):
        """Add CORS headers for browser extension."""
        # Allow extension to access API
        origin = request.headers.get("Origin")
        if origin and origin.startswith("chrome-extension://"):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    @app.route("/api/shops", methods=["GET"])
    def api_get_shops():
        """Get all shops with their URLs for matching."""
        shops = Shop.query.filter_by(is_active=True).all()

        shops_data = []
        for shop in shops:
            shop_data = {"id": shop.id, "name": shop.name, "url": shop.url, "alternative_urls": []}

            # Add alternative URLs from approved proposals
            proposals = ShopURLProposal.query.filter_by(shop_id=shop.id, status="approved").all()

            for proposal in proposals:
                if proposal.url and proposal.url not in shop_data["alternative_urls"]:
                    shop_data["alternative_urls"].append(proposal.url)

            shops_data.append(shop_data)

        return jsonify({"shops": shops_data})

    @app.route("/api/shops/<int:shop_id>/rates", methods=["GET"])
    def api_get_shop_rates(shop_id):
        """Get all rates for a specific shop."""
        shop = Shop.query.get_or_404(shop_id)

        rates = ShopProgramRate.query.filter_by(shop_id=shop_id).all()

        rates_data = []
        for rate in rates:
            rate_data = {
                "id": rate.id,
                "program": rate.bonus_program.name if rate.bonus_program else "Unknown",
                "points_per_eur": float(rate.points_per_eur or 0),
                "cashback_pct": float(rate.cashback_pct or 0),
                "point_value_eur": float(rate.point_value_eur or 0.005),
                "rate_type": rate.rate_type or "shop",
            }

            # Add incentive text if available
            if hasattr(rate, "incentive_text") and rate.incentive_text:
                rate_data["incentive_text"] = rate.incentive_text

            rates_data.append(rate_data)

        return jsonify(
            {"shop": {"id": shop.id, "name": shop.name, "url": shop.url}, "rates": rates_data}
        )

    @app.route("/api/user/status", methods=["GET"])
    def api_user_status():
        """Check if user is logged in."""
        return jsonify(
            {
                "logged_in": current_user.is_authenticated,
                "username": current_user.username if current_user.is_authenticated else None,
                "is_admin": current_user.is_admin if current_user.is_authenticated else False,
            }
        )

    @app.route("/api/proposals/url", methods=["POST"])
    def api_create_url_proposal():
        """Create a URL proposal for a shop."""
        if not current_user.is_authenticated:
            return jsonify({"error": "Authentication required"}), 401

        data = request.get_json()
        shop_id = data.get("shop_id")
        url = data.get("url")

        if not shop_id or not url:
            return jsonify({"error": "shop_id and url are required"}), 400

        shop = Shop.query.get(shop_id)
        if not shop:
            return jsonify({"error": "Shop not found"}), 404

        # Check if proposal already exists
        existing = ShopURLProposal.query.filter_by(shop_id=shop_id, url=url).first()

        if existing:
            return jsonify(
                {
                    "message": "Proposal already exists",
                    "proposal_id": existing.id,
                    "status": existing.status,
                }
            )

        # Create new proposal
        proposal = ShopURLProposal(
            shop_id=shop_id, url=url, proposed_by_id=current_user.id, status="pending"
        )

        db.session.add(proposal)
        db.session.commit()

        return (
            jsonify(
                {
                    "message": "Proposal created successfully",
                    "proposal_id": proposal.id,
                    "status": proposal.status,
                }
            ),
            201,
        )
