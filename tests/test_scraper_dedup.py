"""
Test Miles & More scraper with shop deduplication
"""

from app import app, db
from models import ShopMain, ShopVariant, Shop, ShopProgramRate, BonusProgram
from scrapers.miles_and_more_scraper import MilesAndMoreScraper
from bonus_programs.registry import get_or_create_program

def test_scraper():
    with app.app_context():
        print("\n=== Miles & More Scraper Test with Shop Deduplication ===\n")
        
        # Create or get program
        program = get_or_create_program("MilesAndMore", point_value_eur=0.01)
        print(f"Program: {program.name} (Point Value: €{program.point_value_eur})\n")
        
        # Create test shops manually first to simulate existing data
        print("Pre-seeding: Creating 'amazon' manually...")
        from shop_dedup import get_or_create_shop_main
        existing_shop, _, _ = get_or_create_shop_main("amazon", "manual", None)
        print(f"   Created ShopMain: {existing_shop.canonical_name} (ID: {existing_shop.id[:8]}...)\n")
        
        # Run scraper (first 5 shops only for demo)
        print("Running Miles & More scraper (first 5 shops)...\n")
        scraper = MilesAndMoreScraper()
        
        # Monkey-patch to limit to 5 shops
        original_scrape = scraper.scrape
        def limited_scrape():
            # This will be a simplified version
            from playwright.sync_api import sync_playwright
            import time
            import re
            
            program = BonusProgram.query.filter_by(name=scraper.program_name).first()
            if not program:
                return 0, 0, []
            
            shops_added = 0
            shops_updated = 0
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                page.goto(scraper.base_url, wait_until='networkidle', timeout=30000)
                time.sleep(2)
                
                # Extract first 5 partners
                partner_urls = []
                elements = page.query_selector_all('a[href*="/partners/"]')[:5]
                for elem in elements:
                    href = elem.get_attribute('href')
                    text = elem.inner_text().strip()
                    if href and text and 'partner' in href.lower():
                        full_url = f"https://www.miles-and-more.com{href}" if href.startswith('/') else href
                        partner_urls.append({'name': text, 'url': full_url})
                
                print(f"   Found {len(partner_urls)} test partners\n")
                
                # Scrape each
                for i, partner in enumerate(partner_urls, 1):
                    try:
                        print(f"   [{i}/{len(partner_urls)}] {partner['name']}...", end='', flush=True)
                        
                        # Get or create ShopMain with dedup
                        shop_main, is_new, confidence = get_or_create_shop_main(
                            partner['name'], 'miles_and_more', None
                        )
                        
                        # Legacy Shop
                        legacy_shop = Shop.query.filter_by(name=partner['name']).first()
                        if not legacy_shop:
                            legacy_shop = Shop(name=partner['name'], shop_main_id=shop_main.id)
                            db.session.add(legacy_shop)
                            db.session.commit()
                            shops_added += 1
                            print(" NEW", end='', flush=True)
                        else:
                            shops_updated += 1
                            print(" UPDATED", end='', flush=True)
                        
                        if confidence < 98:
                            print(f" ⚠️ NEEDS_REVIEW (conf: {confidence}%)", end='', flush=True)
                        else:
                            print(f" ({confidence}%)", end='', flush=True)
                        
                        # Use fallback rate
                        points_per_eur = 0.5
                        
                        # Create rate
                        rate = ShopProgramRate.query.filter_by(
                            shop_id=legacy_shop.id, program_id=program.id, valid_to=None
                        ).first()
                        if rate:
                            rate.valid_to = db.func.now()
                        
                        new_rate = ShopProgramRate(
                            shop_id=legacy_shop.id,
                            program_id=program.id,
                            points_per_eur=points_per_eur,
                            cashback_pct=0.0,
                            valid_from=db.func.now()
                        )
                        db.session.add(new_rate)
                        db.session.commit()
                        print(f" → {points_per_eur} P/EUR")
                        
                    except Exception as e:
                        print(f" ERROR: {e}")
                
                browser.close()
            
            return shops_added, shops_updated, []
        
        scraper.scrape = limited_scrape
        added, updated, errors = scraper.scrape()
        
        # Results
        print(f"\n=== Results ===")
        print(f"Shops added: {added}")
        print(f"Shops updated: {updated}")
        print(f"Errors: {len(errors)}")
        
        # Show database state
        print(f"\n=== Database State ===")
        print(f"ShopMain: {ShopMain.query.count()}")
        print(f"ShopVariant: {ShopVariant.query.count()}")
        print(f"Shop (legacy): {Shop.query.count()}")
        print(f"ShopProgramRate: {ShopProgramRate.query.filter_by(valid_to=None).count()} current rates")
        
        # Show deduplication
        print(f"\n=== Shop Deduplication Details ===")
        for sm in ShopMain.query.all():
            variants = ShopVariant.query.filter_by(shop_main_id=sm.id).all()
            print(f"{sm.canonical_name}:")
            for v in variants:
                flag = " ⚠️ REVIEW" if v.confidence_score < 98 else ""
                print(f"  - {v.source}: '{v.source_name}' ({v.confidence_score}%){flag}")
        
        print("\n✅ Test completed!")

if __name__ == "__main__":
    test_scraper()
