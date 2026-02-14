"""
ShoopScraper: General structure for Shoop cashback scraper
"""

from scrapers.base import BaseScraper


class ShoopScraper(BaseScraper):
    """Scraper for Shoop cashback program."""

    BASE_URL = "https://www.shoop.de"
    API_URL_CATEGORIES = "https://api.shoop.de/api/deals/get-category-dropdown-deals"
    API_URL_MERCHANTS = "https://api.shoop.de/api/merchants/get-by-category"

    def fetch(self):
        """
        Fetch all Shoop merchants and map to project shop and rate format, supporting both relative and absolute cashback/points.
        Returns a list of dicts: {name, rates: [{program, points_per_eur, points_absolute, cashback_pct, cashback_absolute, rate_note, ...}]}
        """
        merchants = self.fetch_all_merchants_api()
        results = []
        for m in merchants:
            rates = []
            for r in m.get("rates", []):
                cashback_pct = 0.0
                cashback_absolute = 0.0
                points_per_eur = 0.0
                points_absolute = 0.0
                note = None
                # Shoop: percent = relative, EUR = absolute
                sign = r.get("basic", {}).get("sign")
                value = r.get("value", 0.0)
                try:
                    value = float(value)
                except Exception:
                    value = 0.0
                if r.get("relative") or sign == "%":
                    cashback_pct = value
                elif r.get("absolute") or sign in ["€", "EUR", "€uro"]:
                    cashback_absolute = value
                # If Shoop ever provides points, map accordingly (future-proof)
                if r.get("points_per_eur"):
                    points_per_eur = r.get("points_per_eur")
                if r.get("points_absolute"):
                    points_absolute = r.get("points_absolute")
                # Compose note for extra info
                note = r.get("text") or r.get("warning_text") or None
                rates.append(
                    {
                        "program": "Shoop",
                        "points_per_eur": points_per_eur,
                        "points_absolute": points_absolute,
                        "cashback_pct": cashback_pct,
                        "cashback_absolute": cashback_absolute,
                        "point_value_eur": 0,
                        "category": r.get("text") or None,
                        "rate_note": note,
                    }
                )
            shop_data = {
                "name": m.get("name"),
                "rates": rates,
                "source_id": str(m.get("id")),
                "source": "Shoop",
            }
            results.append(shop_data)
        return results

    """Scraper for Shoop cashback program."""
    BASE_URL = "https://www.shoop.de"
    API_URL_CATEGORIES = "https://api.shoop.de/api/deals/get-category-dropdown-deals"
    API_URL_MERCHANTS = "https://api.shoop.de/api/merchants/get-by-category"

    def __init__(self):
        super().__init__()
        import logging

        self.logger = logging.getLogger("ShoopScraper")

    def fetch_all_merchants_api(self):
        """
        Fetch all merchants from Shoop API, handling all categories and paging.
        Returns a list of merchant dicts in internal format.
        """
        import requests

        merchants = []
        seen_ids = set()
        categories = self._fetch_categories_api()
        for cat in categories:
            items_cursor = 0
            while True:
                params = {
                    "categoryId": cat,
                    "sort_by": "popular",
                    "sort_direction": -1,
                    "itemsCursor": items_cursor,
                }
                try:
                    resp = requests.get(self.API_URL_MERCHANTS, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    if "message" in data and isinstance(data["message"], dict):
                        items_cursor = data["message"].get("itemsCursor", 0)
                        shops = data["message"].get("merchants", [])
                    else:
                        break
                    if not shops:
                        break
                    for d in shops:
                        merchant_id = d.get("id")
                        if merchant_id in seen_ids:
                            continue
                        merchant = self._map_merchant_api(d)
                        merchants.append(merchant)
                        seen_ids.add(merchant_id)
                    if not items_cursor:
                        break
                except Exception as e:
                    self.logger.error(f"Error fetching merchants for category {cat}: {e}")
                    break
        return merchants

    def _fetch_categories_api(self):
        """Fetch category IDs from Shoop API."""
        import requests

        categories = []
        try:
            response = requests.get(self.API_URL_CATEGORIES)
            response.raise_for_status()
            data = response.json()
            if "message" in data and isinstance(data["message"], dict):
                for cat in data["message"].get("categoryDropdownDeals", []):
                    categories.append(cat.get("categoryId"))
        except Exception as e:
            self.logger.error(f"Error fetching categories: {e}")
        return categories

    def _map_merchant_api(self, obj):
        """
        Map Shoop API merchant dict to internal format.
        Returns a dict with keys: id, name, url_name, rates, categories, etc.
        """
        # Minimal mapping, extend as needed for your internal structure
        return {
            "id": obj.get("id"),
            "name": obj.get("name"),
            "url_name": obj.get("url_name"),
            "rates": obj.get("rates", []),
            "categories": obj.get("categories", []),
            "link": obj.get("link"),
            "live": obj.get("live", False),
            "rate_teaser": obj.get("rate_teaser", {}),
            "friend_only": obj.get("friend_only", False),
            "number_of_vouchers": obj.get("number_of_vouchers", 0),
        }
