from bonus_programs.topcashback import scrape_and_register
from spo import create_app


def run():
    app = create_app(start_jobs=False, run_seed=False)
    with app.app_context():
        print("Starting TopCashback scraper...")
        added = scrape_and_register()
        print(f"TopCashback scraper finished. Shops added: {added}")


if __name__ == "__main__":
    run()
