from scrapers.example_scraper import ExampleScraper
from spo import create_app
from spo.services.bonus_programs import register_defaults
from spo.services.seed import register_example_shop

app = create_app()


def run():
    with app.app_context():
        register_defaults()
        register_example_shop()

        scraper = ExampleScraper()
        data = scraper.fetch()
        scraper.register_to_db(data)
        print("Scraper finished; data registered.")


if __name__ == "__main__":
    run()
