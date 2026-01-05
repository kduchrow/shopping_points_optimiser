#!/usr/bin/env python
"""Test Miles & More scraper"""
from app import app
from scrapers.miles_and_more_scraper import MilesAndMoreScraper

with app.app_context():
    print('Testing Miles & More Scraper...\n')
    
    scraper = MilesAndMoreScraper()
    added, updated, errors = scraper.scrape()
    
    print(f'\n\nRESULTS:')
    print(f'  Added: {added}')
    print(f'  Updated: {updated}')
    print(f'  Errors: {len(errors)}')
    
    if errors:
        print(f'\nFirst 10 errors:')
        for err in errors[:10]:
            print(f'  - {err}')
