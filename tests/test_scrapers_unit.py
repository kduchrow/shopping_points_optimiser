from scrapers.base import BaseScraper
from scrapers.payback_scraper import PaybackScraper
from spo.models import Shop, ShopMain, ShopProgramRate


class DummyScraper(BaseScraper):
    def fetch(self):
        return []


def test_base_scraper_registers_and_updates_rates(app):
    with app.app_context():
        # Initial register
        scraper = DummyScraper()
        data = {
            "name": "DemoShop",
            "rates": [
                {
                    "program": "Payback",
                    "points_per_eur": 1.0,
                    "cashback_pct": 0.0,
                    "point_value_eur": 0.005,
                }
            ],
        }
        scraper.register_to_db(data)

        shop = Shop.query.filter_by(name="DemoShop").one()
        main = ShopMain.query.filter_by(id=shop.shop_main_id).one()
        rate = ShopProgramRate.query.filter_by(shop_id=shop.id, valid_to=None).one()

        assert main.canonical_name == "DemoShop"
        assert rate.points_per_eur == 1.0

        # Update with changed rate should archive old and insert new
        data["rates"][0]["points_per_eur"] = 2.0
        scraper.register_to_db(data)

        active_rates = ShopProgramRate.query.filter_by(shop_id=shop.id, valid_to=None).all()
        archived_rates = ShopProgramRate.query.filter(
            ShopProgramRate.shop_id == shop.id,
            ShopProgramRate.valid_to.isnot(None),
        ).all()

        assert len(active_rates) == 1
        assert len(archived_rates) == 1
        assert active_rates[0].points_per_eur == 2.0
        assert archived_rates[0].points_per_eur == 1.0


def test_payback_numeric_parsing():
    scraper = PaybackScraper()

    pct = scraper._extract_numeric("2,5 % Cashback")
    per_eur = scraper._extract_numeric("1 Punkt je 2 €")
    simple = scraper._extract_numeric("5 Punkte")
    completion = scraper._extract_numeric("555 Punkte pro Abschluss")

    assert pct == {"cashback_pct": 2.5}
    assert round(per_eur["points_per_eur"], 2) == 0.5
    assert simple["points_per_eur"] == 5.0
    # Completion points are now correctly extracted as points_per_eur
    assert completion == {"points_per_eur": 555.0}
