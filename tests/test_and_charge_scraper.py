from scrapers.and_charge_scraper import AndChargeScraper


def test_parse_sample_partner():
    sample = {
        "id": 3019,
        "name": "ManoMano DE",
        "userReward": 1,
        "perSalesVolume": 4,
        "logo": "https://example.com/logo.png",
    }

    s = AndChargeScraper()
    shop = s._parse_partner(sample)

    assert shop["name"] == "ManoMano DE"
    assert shop["source"] == "AndCharge"
    assert shop["source_id"] == "3019"
    assert isinstance(shop["rates"], list) and len(shop["rates"]) == 1
    rate = shop["rates"][0]
    # userReward 1 with perSalesVolume 4 -> 0.25 points per EUR
    assert abs(rate["points_per_eur"] - 0.25) < 1e-6
    assert rate["point_value_eur"] == 0.08


def test_fetch_makes_requests(monkeypatch):
    calls = []

    def fake_get(url, params=None, timeout=None):
        class R:
            def raise_for_status(self):
                return None

            def json(self):
                return [{"id": 1, "name": "X", "userReward": 1, "perSalesVolume": 1}]

        calls.append((url, params))
        return R()

    monkeypatch.setattr("requests.get", fake_get)
    s = AndChargeScraper()
    res = s.fetch()
    assert isinstance(res, list)
    assert len(res) >= 1
