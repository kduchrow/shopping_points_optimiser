from flask import current_app

import scrapers.example_scraper as exs_scraper
import scrapers.payback_scraper_js as pb_scraper
import scrapers.shoop_scraper as sh_scraper
from scrapers.miles_and_more_scraper import MilesAndMoreScraper
from scrapers.topcashback_scraper import TopCashbackScraper
from spo.extensions import db
from spo.models import ScrapeLog, Shop
from spo.services.bonus_programs import ensure_program


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
        job.add_message("Starte Payback-Scraper...")
        job.set_progress(10, 100)
        db.session.add(ScrapeLog(message="Payback scraper started"))
        db.session.commit()
        job.add_message("Fetche Partner von Payback...")
        job.set_progress(30, 100)
        scraper = pb_scraper.PaybackScraperJS()
        data = scraper.fetch_partners()
        job.add_message("Registriere Daten in Datenbank...")
        job.set_progress(70, 100)
        added = scraper.register_partners(data)
        job.add_message(f"Fertig: {added} Partner registriert")
        db.session.add(ScrapeLog(message=f"Payback scraper finished, {added} partners"))
        db.session.commit()
        job.set_progress(100, 100)
        return {"partners_added": added}


def scrape_miles_and_more(job):
    with current_app.app_context():
        job.add_message("Starte Miles & More-Scraper...")
        job.set_progress(10, 100)
        db.session.add(ScrapeLog(message="M&M scraper started"))
        db.session.commit()
        job.add_message("Scrape partner data...")
        job.set_progress(30, 100)

        ensure_program("MilesAndMore", point_value_eur=0.01)
        scraper = MilesAndMoreScraper()
        added, updated, errors = scraper.scrape()

        if job:
            for err in errors:
                job.add_message(f"Fehler beim Scrapen: {err}")

        job.add_message(f"Fertig: {added} Partner registriert")
        db.session.add(ScrapeLog(message=f"M&M scraper finished, {added} partners"))
        db.session.commit()
        job.set_progress(100, 100)
        return {"partners_added": added}


def scrape_topcashback(job):
    with current_app.app_context():
        job.add_message("Starte TopCashback-Scraper...")
        job.set_progress(10, 100)
        db.session.add(ScrapeLog(message="TopCashback scraper started"))
        db.session.commit()
        job.add_message("Scrape partner data...")
        job.set_progress(30, 100)

        ensure_program("TopCashback", point_value_eur=0.01)
        scraper = TopCashbackScraper()
        added = scraper.scrape()

        job.add_message(f"Fertig: {added} Partner registriert")
        db.session.add(ScrapeLog(message=f"TopCashback scraper finished, {added} partners"))
        db.session.commit()
        job.set_progress(100, 100)
        return {"partners_added": added}


def scrape_shoop(job):
    with current_app.app_context():
        job.add_message("Starte Shoop-Scraper...")
        job.set_progress(10, 100)
        db.session.add(ScrapeLog(message="Shoop scraper started"))
        db.session.commit()
        job.add_message("Fetche Partner von Shoop...")
        job.set_progress(30, 100)
        scraper = sh_scraper.ShoopScraper()
        data = scraper.fetch()
        job.add_message("Registriere Daten in Datenbank...")
        job.set_progress(70, 100)
        # Already registered in fetch()
        added = len(data)
        job.add_message(f"Fertig: {added} Partner registriert")
        db.session.add(ScrapeLog(message=f"Shoop scraper finished, {added} partners"))
        db.session.commit()
        job.set_progress(100, 100)
        return {"partners_added": added}
