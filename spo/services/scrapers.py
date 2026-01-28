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
