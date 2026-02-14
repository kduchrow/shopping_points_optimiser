import os
from typing import Any

import requests

from scrapers.and_charge_scraper import AndChargeScraper
from scrapers.letyshops_scraper import LetyshopsScraper
from scrapers.miles_and_more_scraper import MilesAndMoreScraper
from scrapers.payback_scraper import PaybackScraper
from scrapers.shoop_scraper import ShoopScraper
from scrapers.topcashback_scraper import TopCashbackScraper

SCRAPER_MAP = {
    "payback": PaybackScraper,
    "miles_and_more": MilesAndMoreScraper,
    "topcashback": TopCashbackScraper,
    "shoop": ShoopScraper,
    "letyshops": LetyshopsScraper,
    "and_charge": AndChargeScraper,
}


def _get_api_base_url() -> str:
    return os.environ.get("SCRAPER_API_BASE_URL", "http://app:5000")


def _get_api_token() -> str | None:
    return os.environ.get("SCRAPER_API_TOKEN")


def _post_results(payload: dict[str, Any]) -> None:
    api_base = _get_api_base_url().rstrip("/")
    url = f"{api_base}/api/scrape-results"
    headers = {"Content-Type": "application/json"}
    token = _get_api_token()
    if not token:
        raise RuntimeError("SCRAPER_API_TOKEN is not set")
    headers["X-Scraper-Token"] = token
    timeout = int(os.environ.get("SCRAPER_API_TIMEOUT", "120"))
    resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()


def run_scrape_job(program: str, run_id: str | None = None, requested_by: str | None = None):
    """Run scraper for program and send results back to API in batches."""
    program_key = program.lower().strip()
    scraper_cls = SCRAPER_MAP.get(program_key)
    if not scraper_cls:
        raise ValueError(f"Unsupported program: {program}")

    scraper = scraper_cls()
    if not hasattr(scraper, "fetch"):
        raise ValueError(f"Scraper does not support fetch(): {program}")

    data = scraper.fetch() or []

    # Add source to each shop if missing
    source_name = scraper.__class__.__name__
    for item in data:
        if "source" not in item:
            item["source"] = source_name

    # Send results in batches to avoid timeouts
    batch_size = int(os.environ.get("SCRAPER_BATCH_SIZE", "50"))
    total_shops = len(data)
    batch_count = 0

    for i in range(0, total_shops, batch_size):
        batch = data[i : i + batch_size]
        batch_count += 1

        payload = {
            "run_id": run_id,
            "program": program_key,
            "requested_by": requested_by,
            "shops": batch,
            "batch_info": {
                "batch_number": batch_count,
                "batch_size": len(batch),
                "total_shops": total_shops,
            },
        }
        _post_results(payload)

    return {"count": total_shops, "batches": batch_count}


def run_import_job(
    import_payload: dict[str, Any],
    run_id: str | None = None,
    requested_by: str | None = None,
):
    """Import consolidated JSON payload via the same API used by scrapers."""
    if not isinstance(import_payload, dict):
        raise ValueError("import_payload must be a dict")

    program = (import_payload.get("program") or "").strip()
    source = import_payload.get("source") or program or "import"
    if not program:
        program = source
    shops = import_payload.get("shops") or []
    if not isinstance(shops, list):
        raise ValueError("import_payload.shops must be a list")

    # Ensure source is present on all shops
    for item in shops:
        if isinstance(item, dict) and "source" not in item:
            item["source"] = source

    batch_size = int(os.environ.get("SCRAPER_BATCH_SIZE", "50"))
    total_shops = len(shops)
    batch_count = 0

    for i in range(0, total_shops, batch_size):
        batch = shops[i : i + batch_size]
        batch_count += 1

        payload = {
            "run_id": run_id,
            "program": program.lower(),
            "requested_by": requested_by,
            "shops": batch,
            "batch_info": {
                "batch_number": batch_count,
                "batch_size": len(batch),
                "total_shops": total_shops,
            },
        }
        _post_results(payload)

    return {"count": total_shops, "batches": batch_count}


def run_coupon_import_job(
    import_payload: dict[str, Any],
    run_id: str | None = None,
    requested_by: str | None = None,
):
    """Import consolidated coupon payload via the coupon-import API."""
    if not isinstance(import_payload, dict):
        raise ValueError("import_payload must be a dict")

    program = (import_payload.get("program") or "").strip() or "import"
    source = import_payload.get("source") or program
    coupons = import_payload.get("coupons") or []
    if not isinstance(coupons, list):
        raise ValueError("import_payload.coupons must be a list")

    # Ensure source is present on all coupons
    for item in coupons:
        if isinstance(item, dict) and "source" not in item:
            item["source"] = source

    # Drop program if it's just the platform/source label
    if program and source and program == source:
        has_coupon_program = any(isinstance(item, dict) and item.get("program") for item in coupons)
        if not has_coupon_program:
            program = ""

    batch_size = int(os.environ.get("SCRAPER_BATCH_SIZE", "50"))
    total_coupons = len(coupons)
    batch_count = 0

    for i in range(0, total_coupons, batch_size):
        batch = coupons[i : i + batch_size]
        batch_count += 1

        payload = {
            "run_id": run_id,
            "requested_by": requested_by,
            "coupons": batch,
            "batch_info": {
                "batch_number": batch_count,
                "batch_size": len(batch),
                "total_coupons": total_coupons,
            },
        }
        if program:
            payload["program"] = program

        api_base = _get_api_base_url().rstrip("/")
        url = f"{api_base}/api/coupon-import"
        headers = {"Content-Type": "application/json"}
        token = _get_api_token()
        if not token:
            raise RuntimeError("SCRAPER_API_TOKEN is not set")
        headers["X-Scraper-Token"] = token
        timeout = int(os.environ.get("SCRAPER_API_TIMEOUT", "120"))
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()

    return {"count": total_coupons, "batches": batch_count}
