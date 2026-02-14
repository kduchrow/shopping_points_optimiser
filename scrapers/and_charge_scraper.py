"""&Charge scraper (API-based).

Fetches partners from the public &Charge API and returns shop dicts
compatible with the project's `BaseScraper.register_to_db` shape.

Notes:
- 1 point = 0.08 EUR (point_value_eur)
- `points_per_eur` is computed as `userReward / perSalesVolume` when
  `perSalesVolume` is present and > 0, otherwise `userReward` is used
  as points per EUR.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from scrapers.base import BaseScraper

logger = logging.getLogger("AndChargeScraper")


class AndChargeScraper(BaseScraper):
    BASE_API = "https://api.and-charge.com/public/v1/partners"

    def fetch(self) -> list[dict[str, Any]]:
        """Fetch paginated partners and convert to shop dicts.

        Returns a list of shop dicts: {name, rates, source_id, source}
        """
        shops: list[dict[str, Any]] = []
        page = 1
        limit = 50
        while True:
            params = {
                "type": "ONLINE_SHOP",
                "page": page,
                "limit": limit,
                "sortby": "PREFERENCE",
                "locale": "de",
            }
            try:
                resp = requests.get(self.BASE_API, params=params, timeout=15)
                resp.raise_for_status()
            except Exception as e:
                logger.error("AndCharge API fetch failed (page %s): %s", page, e)
                break

            try:
                data = resp.json()
            except Exception:
                logger.exception("Failed to decode JSON from AndCharge API")
                break

            if not data:
                break

            for part in data:
                shop = self._parse_partner(part)
                if shop:
                    shops.append(shop)

            # stop if fewer than requested
            if len(data) < limit:
                break
            page += 1
            if page > 200:
                logger.warning("Reached page cap for AndCharge API")
                break

        return shops

    def _parse_partner(self, p: dict) -> dict[str, Any] | None:
        name = p.get("name")
        pid = p.get("id")
        # program name used when registering rates
        program = "AndCharge"

        user_reward = p.get("userReward") or 0
        per_sales = p.get("perSalesVolume") or 0
        reward_model = p.get("rewardModel")

        # point monetary value
        point_value_eur = 0.08

        # If rewardModel indicates a fixed absolute reward per contract, expose cashback_absolute
        if isinstance(reward_model, str) and reward_model.upper() == "FIXED_REWARD_PER_CONTRACT":
            try:
                cashback_abs = float(user_reward)
            except Exception:
                cashback_abs = 0.0

            rate = {
                "program": program,
                "points_per_eur": 0.0,
                "cashback_pct": 0.0,
                "cashback_absolute": cashback_abs,
                "point_value_eur": point_value_eur,
                "rate_note": f"rewardModel={reward_model}",
            }
        else:
            # Compute points_per_eur
            points_per_eur = 0.0
            try:
                if per_sales and per_sales > 0:
                    points_per_eur = float(user_reward) / float(per_sales)
                else:
                    points_per_eur = float(user_reward)
            except Exception:
                points_per_eur = 0.0

            rate = {
                "program": program,
                "points_per_eur": points_per_eur,
                "cashback_pct": 0.0,
                "point_value_eur": point_value_eur,
            }

        return {
            "name": name or None,
            "rates": [rate],
            "logo": p.get("logo"),
            "source_id": str(pid) if pid is not None else None,
            "source": program,
        }
