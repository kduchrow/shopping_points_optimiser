from scrapers.miles_and_more_scraper import MilesAndMoreScraper
from spo.services.bonus_programs import ensure_program


def register():
    """Ensure the Miles & More program exists."""
    ensure_program("MilesAndMore", point_value_eur=0.01)


def scrape_and_register(job=None):
    """Run the Miles & More scraper and stream progress to the async job queue."""
    ensure_program("MilesAndMore", point_value_eur=0.01)

    scraper = MilesAndMoreScraper()
    added, updated, errors = scraper.scrape()

    if job:
        for err in errors:
            job.add_message(f"Fehler beim Scrapen: {err}")

    return added
