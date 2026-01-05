#!/usr/bin/env python
"""Test script for Payback scraper"""
import sys
sys.path.insert(0, '.')

from scrapers.payback_scraper_js import PaybackScraperJS

scraper = PaybackScraperJS()
print('Starting Payback scraper...')
print('This may take 1-2 minutes...\n')

try:
    partners, debug = scraper.fetch()
    print(f'\nResults:')
    print(f'  Status: {debug.get("status_code")}')
    print(f'  Partners found: {debug.get("partners_found")}')
    print(f'  Error: {debug.get("error")}')
    print(f'  Button clicks: {debug.get("button_clicks")}')
    print(f'  Final tile count: {debug.get("final_tile_count")}')
    
    if partners:
        print(f'\nFirst 5 partners:')
        for p in partners[:5]:
            rate = p["rate"]
            print(f'  - {p["name"]}')
            print(f'      Points/EUR: {rate.get("points_per_eur")}')
            print(f'      Cashback: {rate.get("cashback_pct")}%')
            if 'incentive_text' in rate:
                print(f'      Incentive: {rate["incentive_text"]}')
    else:
        print('\nNo partners found!')
        print(f'Error detail: {debug.get("error")}')
        
except Exception as e:
    print(f'Exception: {e}')
    import traceback
    traceback.print_exc()
