import pytest

from scrapers.shoop_scraper import ShoopScraper


@pytest.fixture
def shoop_scraper():
    return ShoopScraper()


@pytest.fixture
def app_ctx(app):
    with app.app_context():
        yield


def test_shoop_scraper_fetch_returns_shops(shoop_scraper, app_ctx):
    """Test that ShoopScraper.fetch() returns a list of shops with expected fields."""
    shops = shoop_scraper.fetch()
    assert isinstance(shops, list)
    assert len(shops) > 0
    for shop in shops:
        assert "name" in shop and isinstance(shop["name"], str)
        assert "rates" in shop and isinstance(shop["rates"], list)


def test_shoop_scraper_shop_rates_structure(shoop_scraper, app_ctx):
    """Test that each shop's rates have the expected structure."""
    shops = shoop_scraper.fetch()
    for shop in shops:
        for rate in shop["rates"]:
            assert "program" in rate and rate["program"] == "Shoop"
            assert "cashback_pct" in rate or "cashback_absolute" in rate
            assert "point_value_eur" in rate


def test_shoop_scraper_merchants_api(shoop_scraper):
    """Test that fetch_all_merchants_api returns merchants with required fields."""
    merchants = shoop_scraper.fetch_all_merchants_api()
    assert isinstance(merchants, list)
    for m in merchants:
        assert "id" in m
        assert "name" in m
        assert "rates" in m


def test_shoop_scraper_category_deduplication(shoop_scraper):
    """Test that merchants are deduplicated across categories."""
    merchants = shoop_scraper.fetch_all_merchants_api()
    ids = [m["id"] for m in merchants]
    assert len(ids) == len(set(ids))


def test_shoop_scraper_handles_api_failure(monkeypatch, shoop_scraper):
    """Test that API failure is handled gracefully and logs error."""

    def fake_requests_get(*args, **kwargs):
        class FakeResp:
            def raise_for_status(self):
                raise Exception("API error")

            def json(self):
                return {}

        return FakeResp()

    import requests

    monkeypatch.setattr(requests, "get", fake_requests_get)
    # Should not raise, just return empty list
    assert shoop_scraper.fetch_all_merchants_api() == []
