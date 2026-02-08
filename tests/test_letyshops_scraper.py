from scrapers.letyshops_scraper import LetyshopsScraper


def test_parse_shops_from_html_basic():
    html = """
    <div>
      <a href="/de/shops/nike-de">
        <div class="h-full w-full">
          <div class="text-sm">Nike</div>
          <div class="font-bold">1.5 % Cashback</div>
          <img src="https://image.letyshops.com/logos/nike.png" />
        </div>
      </a>
      <a href="/de/shops/amazon-de">
        <div>
          <h3>Amazon</h3>
          <div>0.75%</div>
          <img src="https://image.letyshops.com/logos/amazon.png" />
        </div>
      </a>
    </div>
    """

    shops = LetyshopsScraper.parse_shops_from_html(html)
    assert isinstance(shops, list)
    assert len(shops) == 2

    names = {s["name"] for s in shops}
    assert "Nike" in names
    assert "Amazon" in names

    nike = next(s for s in shops if s["source_id"] == "nike-de")
    assert nike["rates"] and nike["rates"][0]["cashback_pct"] == 1.5

    amazon = next(s for s in shops if s["source_id"] == "amazon-de")
    assert amazon["rates"] and amazon["rates"][0]["cashback_pct"] == 0.75
