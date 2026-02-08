from scrapers.letyshops_scraper import LetyshopsScraper


def test_parse_shop_detail_table():
    html = """
    <div class="rates">
      <table>
        <tr><td>Schuhe</td><td>2 %</td></tr>
        <tr><td>Kleidung</td><td>1.5%</td></tr>
      </table>
    </div>
    """

    rates = LetyshopsScraper.parse_shop_detail(html)
    assert isinstance(rates, list)
    assert any(r.get("category") == "Schuhe" and r.get("cashback_pct") == 2.0 for r in rates)
    assert any(r.get("category") == "Kleidung" and r.get("cashback_pct") == 1.5 for r in rates)
