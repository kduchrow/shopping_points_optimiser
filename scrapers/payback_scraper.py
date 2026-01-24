import re

import requests  # type: ignore[import]

from .base import BaseScraper


class PaybackScraper(BaseScraper):
    """API-based scraper for Payback partner data.

    Uses the official Payback API endpoint to fetch all loyalty partners in JSON format.
    This is more reliable than HTML scraping and returns structured data directly.
    """

    API_URL = "https://www.payback.de/resources/json/getloyaltypartner?size=9999"

    def _extract_numeric(self, text):
        """Extract numeric rate information from incentive text."""
        if not text:
            return {}
        # find percent values
        m = re.search(r"(\d+[\.,]?\d*)\s*%", text)
        if m:
            return {"cashback_pct": float(m.group(1).replace(",", "."))}
        # find patterns like '1 °P pro 2 €' (Payback API format)
        m = re.search(
            r"(\d+[\.,]?\d*)\s*°?P\s*(?:je|pro)\s*(\d+[\.,]?\d*)\s*(?:€|EUR)",
            text,
            re.I,
        )
        if m:
            pts = float(m.group(1).replace(",", "."))
            per = float(m.group(2).replace(",", "."))
            return {"points_per_eur": pts / per if per != 0 else 0.0}
        # find patterns like '1 Punkt je 1 €' or '1 Punkt pro 1 €'
        m = re.search(
            r"(\d+[\.,]?\d*)\s*(?:Punkt|Punkte)\s*(?:je|pro)\s*(\d+[\.,]?\d*)\s*(?:€|EUR)",
            text,
            re.I,
        )
        if m:
            pts = float(m.group(1).replace(",", "."))
            per = float(m.group(2).replace(",", "."))
            return {"points_per_eur": pts / per if per != 0 else 0.0}
        # fallback: find 'Punkte' with a single number -> treat as points per euro
        m = re.search(r"(\d+[\.,]?\d*)\s*(?:Punkte|Punkt)", text, re.I)
        if m:
            return {"points_per_eur": float(m.group(1).replace(",", "."))}
        return {}

    def fetch(self):
        """Fetch partner data from Payback API."""
        try:
            resp = requests.get(
                self.API_URL,
                headers={"User-Agent": "shopping-points-optimiser/1.0 (+https://example.local)"},
                timeout=15,
            )
            resp.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Error fetching payback partners from API: {e}")

        try:
            data = resp.json()
        except Exception as e:
            raise RuntimeError(f"Error parsing JSON response from Payback API: {e}")

        partners = data.get("partners", {})
        if not partners:
            raise RuntimeError("No partners found in API response")

        results = []
        for partner_id, partner_data in partners.items():
            name = partner_data.get("displayName", "").strip()
            if not name:
                continue

            incentive = partner_data.get("incentive", "")
            numeric = self._extract_numeric(incentive)

            # detect points-per-completion like '555 °P pro Abschluss'
            per_completion = None
            m = re.search(r"(\d+[\.,]?\d*)\s*°?P\s*(?:pro|pro Abschluss|per)", incentive, re.I)
            if m:
                per_completion = float(m.group(1).replace(",", "."))

            rate = {
                "program": "Payback",
                "points_per_eur": numeric.get("points_per_eur", 0.0),
                "cashback_pct": numeric.get("cashback_pct", 0.0),
                "point_value_eur": 0.005,
            }

            # include raw incentive and per-completion info as metadata
            if incentive:
                rate["incentive_text"] = incentive
            if per_completion is not None:
                rate["per_completion_points"] = per_completion

            # include additional metadata from API
            rate["partner_id"] = partner_id
            if partner_data.get("vanityName"):
                rate["vanity_name"] = partner_data["vanityName"]
            if partner_data.get("detailsUrl"):
                rate["details_url"] = partner_data["detailsUrl"]

            results.append({"name": name, "rate": rate})

        debug = {
            "status_code": resp.status_code,
            "api_url": self.API_URL,
            "partners_count": len(partners),
            "results_count": len(results),
        }

        return results, debug
