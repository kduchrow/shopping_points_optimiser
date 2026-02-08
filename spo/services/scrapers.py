from flask import current_app

import scrapers.example_scraper as exs_scraper
from spo.extensions import db
from spo.models import ScrapeLog, Shop
from spo.services.scrape_queue import enqueue_scrape_job


def scrape_example(job):
    with current_app.app_context():
        job.add_message("Starte Example-Scraper...")
        job.set_progress(10, 100)

        db.session.add(ScrapeLog(message="Example scraper started"))
        db.session.commit()

        job.add_message("Fetche Daten...")
        job.set_progress(30, 100)

        before_shops = Shop.query.count()
        scraper = exs_scraper.ExampleScraper()
        data = scraper.fetch()

        job.add_message("Registriere Daten in Datenbank...")
        job.set_progress(60, 100)

        scraper.register_to_db(data)
        after_shops = Shop.query.count()
        added = after_shops - before_shops

        job.add_message(f"Fertig: {added} Shops hinzugefügt")
        db.session.add(ScrapeLog(message=f"Example scraper finished, added {added} shops"))
        db.session.commit()

        job.set_progress(100, 100)
        return {"added": added}


def scrape_payback(job):
    with current_app.app_context():
        job.add_message("Starte Payback-Scraper (Remote Worker)...")
        job.set_progress(10, 100)
        job_id = enqueue_scrape_job("payback", requested_by="app")
        job.add_message(f"Job in Queue: {job_id}")
        db.session.add(ScrapeLog(message=f"Payback scraper enqueued: {job_id}"))
        db.session.commit()
        job.set_progress(100, 100)
        return {"job_id": job_id}


def scrape_miles_and_more(job):
    with current_app.app_context():
        job.add_message("Starte Miles & More-Scraper (Remote Worker)...")
        job.set_progress(10, 100)
        job_id = enqueue_scrape_job("miles_and_more", requested_by="app")
        job.add_message(f"Job in Queue: {job_id}")
        db.session.add(ScrapeLog(message=f"M&M scraper enqueued: {job_id}"))
        db.session.commit()
        job.set_progress(100, 100)
        return {"job_id": job_id}


def scrape_topcashback(job):
    with current_app.app_context():
        job.add_message("Starte TopCashback-Scraper (Remote Worker)...")
        job.set_progress(10, 100)
        job_id = enqueue_scrape_job("topcashback", requested_by="app")
        job.add_message(f"Job in Queue: {job_id}")
        db.session.add(ScrapeLog(message=f"TopCashback scraper enqueued: {job_id}"))
        db.session.commit()
        job.set_progress(100, 100)
        return {"job_id": job_id}


def scrape_shoop(job):
    with current_app.app_context():
        job.add_message("Starte Shoop-Scraper (Remote Worker)...")
        job.set_progress(10, 100)
        job_id = enqueue_scrape_job("shoop", requested_by="app")
        job.add_message(f"Job in Queue: {job_id}")
        db.session.add(ScrapeLog(message=f"Shoop scraper enqueued: {job_id}"))
        db.session.commit()
        job.set_progress(100, 100)
        return {"job_id": job_id}


def scrape_letyshops(job):
    with current_app.app_context():
        job.add_message("Starte LetyShops-Scraper...")
        job.set_progress(10, 100)

        db.session.add(ScrapeLog(message="LetyShops scraper started"))
        db.session.commit()

        job.add_message("Fetche Daten...")
        job.set_progress(30, 100)

        before_shops = Shop.query.count()
        import scrapers.letyshops_scraper as lety_scraper

        scraper = lety_scraper.LetyshopsScraper()
        data = scraper.fetch()

        # The `LetyshopsScraper.fetch()` implementation already attempts to
        # enrich listing items with per-category detail rates where available.
        # Therefore we don't perform per-item detail fetches here; the
        # scraper returns shop dicts with `rates` already containing either
        # the teaser rate (if no categories) or the categorized detail rates.

        def _normalize_rates(rates_list: list) -> list:
            """Deduplicate and merge rates: keep highest cashback_pct per (program, category)."""
            if not rates_list:
                return []
            merged = {}
            for r in rates_list:
                prog = r.get("program")
                cat = r.get("category")
                key = (prog, cat)
                existing = merged.get(key)
                if not existing:
                    merged[key] = r.copy()
                    continue
                # prefer higher cashback_pct
                a = existing.get("cashback_pct") or 0.0
                b = r.get("cashback_pct") or 0.0
                if b > a:
                    merged[key] = r.copy()
                    continue
                # fallback: prefer higher points_per_eur
                a_p = existing.get("points_per_eur") or 0.0
                b_p = r.get("points_per_eur") or 0.0
                if b_p > a_p:
                    merged[key] = r.copy()

            return list(merged.values())

        job.add_message("Registriere Daten in Datenbank...")
        job.set_progress(60, 100)

        # `fetch()` returns a list of shop dicts for this scraper; handle both list and single-dict returns.
        added = 0
        if isinstance(data, list):
            for item in data:
                try:
                    # normalize/dedupe rates before registering
                    item["rates"] = _normalize_rates(item.get("rates", []))
                    scraper.register_to_db(item)
                except Exception as e:
                    job.add_message(f"Fehler beim Registrieren: {e}")
            after_shops = Shop.query.count()
            added = after_shops - before_shops
        elif isinstance(data, dict):
            scraper.register_to_db(data)
            after_shops = Shop.query.count()
            added = after_shops - before_shops
        else:
            job.add_message("Keine Daten zum Registrieren gefunden")

        job.add_message(f"Fertig: {added} Shops hinzugefügt")
        db.session.add(ScrapeLog(message=f"LetyShops scraper finished, added {added} shops"))
        db.session.commit()

        job.set_progress(100, 100)
        return {"added": added}
