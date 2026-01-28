from scrapers.base import BaseScraper


class _IngestScraper(BaseScraper):
    def fetch(self):
        return []


def ingest_scrape_results(shops: list[dict], *, source: str | None = None) -> int:
    """Persist scraped shop data using BaseScraper logic."""
    scraper = _IngestScraper()
    count = 0
    for shop_data in shops:
        if source and "source" not in shop_data:
            shop_data["source"] = source
        scraper.register_to_db(shop_data)
        count += 1
    return count
