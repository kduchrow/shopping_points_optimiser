"""TopCashback bonus program registration and scraper coordination."""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.topcashback_scraper import TopCashbackScraper  # noqa: E402
from spo.services.bonus_programs import ensure_program  # noqa: E402


def register():
    """Ensure the TopCashback program exists in database."""
    ensure_program("TopCashback", point_value_eur=0.01)


def scrape_and_register(job=None):
    """Run the TopCashback scraper and stream progress to the async job queue.

    Args:
        job: Optional APScheduler job object for streaming progress updates.

    Returns:
        int: Number of shops added/updated.
    """
    # Ensure TopCashback program exists
    ensure_program("TopCashback", point_value_eur=0.01)

    scraper = TopCashbackScraper()
    results, debug = scraper.fetch()

    if job:
        job.add_message(
            f"TopCashback scraper started. Target: {debug.get('partners_found', 0)} shops"
        )

    added = 0
    errors = []

    for data in results:
        try:
            scraper.register_to_db(data)
            added += 1
        except Exception as e:
            error_msg = f"Error registering shop '{data.get('name', 'Unknown')}': {e}"
            errors.append(error_msg)
            if job:
                job.add_message(f"⚠️ {error_msg}")

    if job:
        job.add_message(
            f"TopCashback scraping complete: {added} shops added/updated, {len(errors)} errors"
        )
        if debug.get("error"):
            job.add_message(f"Debug info: {debug.get('error')}")

    return added
