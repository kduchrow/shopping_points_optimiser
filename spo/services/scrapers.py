from flask import current_app

from spo.extensions import db
from spo.models import ScrapeLog, Shop
import scrapers.example_scraper as exs_scraper
import scrapers.payback_scraper_js as pb_scraper
import bonus_programs.miles_and_more as mam


def scrape_example(job):
    with current_app.app_context():
        job.add_message('Starte Example-Scraper...')
        job.set_progress(10, 100)

        db.session.add(ScrapeLog(message='Example scraper started'))
        db.session.commit()

        job.add_message('Fetche Daten...')
        job.set_progress(30, 100)

        before_shops = Shop.query.count()
        scraper = exs_scraper.ExampleScraper()
        data = scraper.fetch()

        job.add_message('Registriere Daten in Datenbank...')
        job.set_progress(60, 100)

        scraper.register_to_db(data)
        after_shops = Shop.query.count()
        added = after_shops - before_shops

        job.add_message(f'Fertig: {added} Shops hinzugefügt')
        db.session.add(ScrapeLog(message=f'Example scraper finished, added {added} shops'))
        db.session.commit()

        job.set_progress(100, 100)
        return {'added': added}


def scrape_payback(job):
    with current_app.app_context():
        job.add_message('Starte Payback-Scraper...')
        job.set_progress(10, 100)
        db.session.add(ScrapeLog(message='Payback scraper started'))
        db.session.commit()
        job.add_message('Fetche Partner von Payback...')
        job.set_progress(30, 100)
        scraper = pb_scraper.PaybackScraperJS()
        data = scraper.fetch_partners()
        job.add_message('Registriere Daten in Datenbank...')
        job.set_progress(70, 100)
        added = scraper.register_partners(data)
        job.add_message(f'Fertig: {added} Partner registriert')
        db.session.add(ScrapeLog(message=f'Payback scraper finished, {added} partners'))
        db.session.commit()
        job.set_progress(100, 100)
        return {'partners_added': added}


def scrape_miles_and_more(job):
    with current_app.app_context():
        job.add_message('Starte Miles & More-Scraper...')
        job.set_progress(10, 100)
        db.session.add(ScrapeLog(message='M&M scraper started'))
        db.session.commit()
        job.add_message('Scrape partner data...')
        job.set_progress(30, 100)
        added = mam.scrape_and_register(job)
        job.add_message(f'Fertig: {added} Partner registriert')
        db.session.add(ScrapeLog(message=f'M&M scraper finished, {added} partners'))
        db.session.commit()
        job.set_progress(100, 100)
        return {'partners_added': added}
