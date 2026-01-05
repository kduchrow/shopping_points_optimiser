from flask import Flask
from models import db, init_db
import bonus_programs.miles_and_more as mam
import bonus_programs.payback as pb
import bonus_programs.shoop as sh
import scrapers.example_scraper as exs

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shopping.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def run():
    with app.app_context():
        init_db()
        # ensure base programs exist
        mam.register()
        pb.register()
        sh.register()

        # run example scraper
        scraper = exs.ExampleScraper()
        data = scraper.fetch()
        scraper.register_to_db(data)
        print('Scraper finished; data registered.')


if __name__ == '__main__':
    run()
