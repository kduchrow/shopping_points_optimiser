from .base import BaseScraper


class ExampleScraper(BaseScraper):
    def fetch(self):
        return [
            {
                "name": "ExampleShopScraped",
                "rates": [
                    {
                        "program": "MilesAndMore",
                        "points_per_eur": 0.6,
                        "cashback_pct": 0.0,
                        "point_value_eur": 0.01,
                    },
                    {
                        "program": "Payback",
                        "points_per_eur": 1.2,
                        "cashback_pct": 0.0,
                        "point_value_eur": 0.005,
                    },
                    {
                        "program": "Shoop",
                        "points_per_eur": 0.8,
                        "cashback_pct": 1.5,
                        "point_value_eur": 0.008,
                    },
                ],
                "source": "Example",
                "source_id": "example",
            }
        ]
