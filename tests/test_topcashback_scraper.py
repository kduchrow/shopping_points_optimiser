"""Tests for TopCashback scraper."""

from unittest.mock import Mock, patch

import pytest

from scrapers.topcashback_scraper import TopCashbackScraper


class TestTopCashbackScraper:
    """Unit tests for TopCashbackScraper."""

    @pytest.fixture
    def scraper(self):
        """Create a TopCashbackScraper instance for testing."""
        return TopCashbackScraper()

    def test_extract_cashback_percentage_simple(self, scraper):
        """Test extraction of simple percentage values."""
        assert scraper._extract_cashback_percentage("3,5% Cashback") == 3.5
        assert scraper._extract_cashback_percentage("5% Bonus") == 5.0
        assert scraper._extract_cashback_percentage("10,25% Cashback") == 10.25

    def test_extract_cashback_percentage_with_prefix(self, scraper):
        """Test extraction of percentages with 'Bis zu' prefix."""
        assert scraper._extract_cashback_percentage("Bis zu 5% Cashback") == 5.0
        assert scraper._extract_cashback_percentage("bis zu 3,5% Bonus") == 3.5

    def test_extract_cashback_percentage_no_match(self, scraper):
        """Test extraction when no percentage is found."""
        assert scraper._extract_cashback_percentage("No percentage here") == 0.0
        assert scraper._extract_cashback_percentage("") == 0.0
        assert scraper._extract_cashback_percentage(None) == 0.0

    def test_extract_cashback_percentage_dot_notation(self, scraper):
        """Test extraction with dot notation (alternative decimal format)."""
        assert scraper._extract_cashback_percentage("5.0% Cashback") == 5.0
        assert scraper._extract_cashback_percentage("3.5% Bonus") == 3.5

    def test_extract_shop_url_relative(self, scraper):
        """Test URL extraction with relative links."""
        from bs4 import BeautifulSoup

        html = '<div><a href="/partner/amazon">Amazon</a></div>'
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")

        url = scraper._extract_shop_url(div)
        assert url == "https://www.topcashback.de/partner/amazon"

    def test_extract_shop_url_absolute(self, scraper):
        """Test URL extraction with absolute links."""
        from bs4 import BeautifulSoup

        html = '<div><a href="https://example.com">Example</a></div>'
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")

        url = scraper._extract_shop_url(div)
        assert url == "https://example.com"

    def test_extract_shop_url_no_link(self, scraper):
        """Test URL extraction when no link is present."""
        from bs4 import BeautifulSoup

        html = "<div>No link here</div>"
        soup = BeautifulSoup(html, "html.parser")
        div = soup.find("div")

        url = scraper._extract_shop_url(div)
        assert url is None

    @patch("scrapers.topcashback_scraper.requests.Session.get")
    def test_fetch_successful(self, mock_get, scraper):
        """Test successful fetch of partner list."""
        # Mock HTML response
        mock_html = """
        <html>
            <body>
                <div class="partner-tile" data-shop-name="Amazon">
                    <span class="incentive-text">3,5% Cashback</span>
                    <a href="/partner/amazon">Amazon</a>
                </div>
                <div class="partner-tile" data-shop-name="eBay">
                    <span class="incentive-text">2,5% Cashback</span>
                    <a href="/partner/ebay">eBay</a>
                </div>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response

        results, debug = scraper.fetch()

        assert debug["status_code"] == 200
        assert len(results) == 2

        # Check first result
        assert results[0]["name"] == "Amazon"
        assert results[0]["rate"]["program"] == "TopCashback"
        assert results[0]["rate"]["cashback_pct"] == 3.5

        # Check second result
        assert results[1]["name"] == "eBay"
        assert results[1]["rate"]["cashback_pct"] == 2.5

    @patch("scrapers.topcashback_scraper.requests.Session.get")
    def test_fetch_network_error(self, mock_get, scraper):
        """Test fetch with network error."""
        import requests

        mock_get.side_effect = requests.RequestException("Connection error")

        results, debug = scraper.fetch()

        assert results == []
        assert debug["error"] is not None
        assert "Connection error" in debug["error"]

    @patch("scrapers.topcashback_scraper.requests.Session.get")
    def test_fetch_malformed_html(self, mock_get, scraper):
        """Test fetch with malformed HTML."""
        mock_html = "<html><body>Invalid structure</body></html>"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response

        results, debug = scraper.fetch()

        assert results == []
        assert debug["status_code"] == 200

    @patch("scrapers.topcashback_scraper.requests.Session.get")
    def test_fetch_deduplication(self, mock_get, scraper):
        """Test that duplicate shop names are deduplicated."""
        mock_html = """
        <html>
            <body>
                <div class="partner-tile"><a href="/partner/amazon1">Amazon</a><span>3,5%</span></div>
                <div class="partner-tile"><a href="/partner/amazon2">Amazon</a><span>3,5%</span></div>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response

        results, debug = scraper.fetch()

        # Should only have one Amazon entry (deduplicated)
        amazon_entries = [r for r in results if "Amazon" in r["name"]]
        assert len(amazon_entries) == 1

    @patch("scrapers.topcashback_scraper.requests.Session.get")
    def test_fetch_rate_defaults(self, mock_get, scraper):
        """Test that rate defaults are set correctly."""
        mock_html = """
        <html>
            <body>
                <div class="partner-tile" data-shop-name="TestShop">
                    <span class="incentive-text">2% Cashback</span>
                </div>
            </body>
        </html>
        """

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response

        results, debug = scraper.fetch()

        assert len(results) == 1
        rate = results[0]["rate"]

        assert rate["program"] == "TopCashback"
        assert rate["cashback_pct"] == 2.0
        assert rate["points_per_eur"] == 0.0  # TopCashback uses cashback, not points
        assert rate["point_value_eur"] == 0.01


class TestTopCashbackIntegration:
    """Integration tests with database (requires app context)."""

    @pytest.mark.integration
    def test_register_to_db(self, app):
        """Test registering TopCashback data to database."""
        with app.app_context():
            scraper = TopCashbackScraper()

            # Create test data
            test_data = {
                "name": "Test Shop TopCashback",
                "rate": {
                    "program": "TopCashback",
                    "cashback_pct": 3.5,
                    "points_per_eur": 0.0,
                    "point_value_eur": 0.01,
                },
            }

            # Should not raise any exceptions
            scraper.register_to_db(test_data)

            # Verify shop was created
            from spo.models import ShopMain, ShopVariant

            shop_main = ShopMain.query.first()
            assert shop_main is not None

            # Check ShopVariant (the actual shop name is stored there)
            shop_variant = ShopVariant.query.filter_by(shop_main_id=shop_main.id).first()
            assert shop_variant is not None

    @pytest.mark.integration
    def test_scrape_and_register(self, app):
        """Test the full scrape_and_register function."""
        with app.app_context():
            from bonus_programs import topcashback

            # Should not raise any exceptions
            result = topcashback.scrape_and_register(job=None)

            # Should return a number (even if 0)
            assert isinstance(result, int)
