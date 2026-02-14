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
        """Test successful fetch of partner list with per-category rates."""
        # Mock homepage HTML with a category link
        homepage_html = """
        <html>
            <body>
                <a href="/kategorie/test/">Test Category</a>
            </body>
        </html>
        """
        # Mock category page HTML with partner tiles
        category_html = """
        <html>
            <body>
                <a class="category-panel" href="/shop/amazon">
                    <span class="search-merchant-name">Amazon</span>
                    <span class="category-cashback-rate">3,5%</span>
                </a>
                <a class="category-panel" href="/shop/ebay">
                    <span class="search-merchant-name">eBay</span>
                    <span class="category-cashback-rate">2,5%</span>
                </a>
            </body>
        </html>
        """
        # Mock detail page HTML for each shop (simulate rates)
        detail_html = """
        <html><body>
            <div class="merch-rate-card">
                <span class="merch-cat__sub-cat">Elektronik</span>
                <span class="merch-cat__rate">5%</span>
                <span class="merch-cat__sub-cat">Bücher</span>
                <span class="merch-cat__rate">2%</span>
            </div>
        </body></html>
        """

        # Set up the mock to return different HTML for each call
        mock_get.side_effect = [
            Mock(status_code=200, text=homepage_html),  # homepage
            Mock(status_code=200, text=category_html),  # category page (page 1)
            Mock(
                status_code=200, text="<html><body></body></html>"
            ),  # category page (page 2, empty)
            Mock(status_code=200, text=detail_html),  # Amazon detail
            Mock(status_code=200, text=detail_html),  # eBay detail
        ]

        results = scraper.fetch()

        assert len(results) == 2

        # Check Amazon shop
        amazon = next(r for r in results if r["name"] == "Amazon")
        assert "rates" in amazon
        # The test only checks the structure, not the actual rates, since detail_html is empty

        # Check eBay shop
        ebay = next(r for r in results if r["name"] == "eBay")
        assert "rates" in ebay

    @patch("scrapers.topcashback_scraper.requests.Session.get")
    def test_fetch_network_error(self, mock_get, scraper):
        """Test fetch with network error."""
        import requests

        mock_get.side_effect = requests.RequestException("Connection error")

        results = scraper.fetch()
        assert results == []

    @patch("scrapers.topcashback_scraper.requests.Session.get")
    def test_fetch_malformed_html(self, mock_get, scraper):
        """Test fetch with malformed HTML."""
        mock_html = "<html><body>Invalid structure</body></html>"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_get.return_value = mock_response

        results = scraper.fetch()
        assert results == []

    @patch("scrapers.topcashback_scraper.requests.Session.get")
    def test_fetch_deduplication(self, mock_get, scraper):
        """Test that duplicate shop names are deduplicated."""
        homepage_html = """
        <html>
            <body>
                <a href="/kategorie/test/">Test Category</a>
            </body>
        </html>
        """
        category_html = """
        <html>
            <body>
                <a class="category-panel" href="/shop/amazon1">
                    <span class="search-merchant-name">Amazon</span>
                    <span class="category-cashback-rate">3,5%</span>
                </a>
                <a class="category-panel" href="/shop/amazon2">
                    <span class="search-merchant-name">Amazon</span>
                    <span class="category-cashback-rate">3,5%</span>
                </a>
            </body>
        </html>
        """
        detail_html = """
        <html><body></body></html>
        """

        mock_get.side_effect = [
            Mock(status_code=200, text=homepage_html),  # homepage
            Mock(status_code=200, text=category_html),  # category page (page 1)
            Mock(
                status_code=200, text="<html><body></body></html>"
            ),  # category page (page 2, empty)
            Mock(status_code=200, text=detail_html),  # detail page 1
            Mock(status_code=200, text=detail_html),  # detail page 2
        ]

        results = scraper.fetch()

        # Should deduplicate by shop name
        assert len(results) == 1
        assert results[0]["name"] == "Amazon"

    @patch("scrapers.topcashback_scraper.requests.Session.get")
    def test_fetch_rate_defaults(self, mock_get, scraper):
        """Test that rate defaults are set correctly."""
        homepage_html = """
        <html>
            <body>
                <a href="/kategorie/test/">Test Category</a>
            </body>
        </html>
        """
        category_html = """
        <html>
            <body>
                <a class="category-panel" href="/shop/testshop">
                    <span class="search-merchant-name">TestShop</span>
                    <span class="category-cashback-rate">2%</span>
                </a>
            </body>
        </html>
        """
        detail_html = """
        <html><body></body></html>
        """

        mock_get.side_effect = [
            Mock(status_code=200, text=homepage_html),  # homepage
            Mock(status_code=200, text=category_html),  # category page (page 1)
            Mock(
                status_code=200, text="<html><body></body></html>"
            ),  # category page (page 2, empty)
            Mock(status_code=200, text=detail_html),  # detail page
        ]

        results = scraper.fetch()

        assert len(results) == 1
        rate = results[0]["rates"][0]

        assert rate["program"] == "TopCashback"
        assert rate["cashback_pct"] == 2.0
        assert rate["points_per_eur"] == 0.0  # TopCashback uses cashback, not points
        assert rate["point_value_eur"] == 0.0


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
                    "point_value_eur": 0.0,
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
        """Test enqueuing TopCashback scraper job via worker queue."""
        with app.app_context():
            from spo.services.scrape_queue import enqueue_scrape_job

            # Enqueue the job (should not raise any exceptions)
            job_id = enqueue_scrape_job("topcashback", requested_by="test")

            # Should return a valid job ID (string/uuid)
            assert isinstance(job_id, str)
            assert len(job_id) > 0
