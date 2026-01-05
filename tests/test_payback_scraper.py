"""Quick debug script to test Payback scraper without running the full app."""
import re
import requests
from bs4 import BeautifulSoup

# Inline minimal scraper to avoid dependency on models/flask
class PaybackScraper:
    PARTNER_LIST_URL = 'https://www.payback.de/online-shopping/shop-a-z'
    
    def fetch(self):
        try:
            resp = requests.get(self.PARTNER_LIST_URL, headers={
                'User-Agent': 'shopping-points-optimiser/1.0 (+https://example.local)'
            }, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            raise RuntimeError(f'Error fetching payback partners: {e}')

        soup = BeautifulSoup(resp.text, 'html.parser')

        results = []
        candidates = soup.find_all('a', class_=re.compile(r'partner-tile', re.I))
        
        # Debug: print first few elements with "partner-tile" in their class
        if not candidates:
            print("\n[DEBUG] No match on 'a' with class regex 'partner-tile'")
            print("[DEBUG] Trying alternative selectors...")
            
            # Try divs with partner-tile
            divs_with_tile = soup.find_all(class_=re.compile(r'partner-tile', re.I))
            print(f"[DEBUG] Found {len(divs_with_tile)} elements with 'partner-tile' in class (any tag)")
            if divs_with_tile:
                print(f"[DEBUG] First element: {str(divs_with_tile[0])[:200]}...")
            
            # Try links with /shop/ href
            candidates = soup.find_all('a', href=re.compile(r'^/shop/'))
            print(f"[DEBUG] Found {len(candidates)} <a> elements with href=/shop/...")
            if candidates:
                print(f"[DEBUG] First <a> with /shop/: {str(candidates[0])[:200]}...")
        else:
            print(f"[DEBUG] Found {len(candidates)} <a class='partner-tile'> elements")

        for c in candidates:
            name = c.get('data-partner-vanity-name') or None
            if not name:
                img = c.find('img', alt=True)
                if img:
                    name = img['alt']
            if not name:
                name = c.get_text(' ', strip=True)
            
            name = (name or '').strip()
            if name:
                incentive_el = c.select_one('.partner-tile__incentive-text')
                incentive = incentive_el.get_text(' ', strip=True) if incentive_el else ''
                results.append({'name': name, 'incentive': incentive})

        debug = {
            'status_code': resp.status_code,
            'html_length': len(resp.text or ''),
            'found_partner_tile': ('partner-tile' in (resp.text or '')),
            'candidates_count': len(candidates),
        }
        
        return results, debug

def main():
    print("Testing Payback Scraper...")
    print("-" * 60)
    
    scraper = PaybackScraper()
    
    try:
        print(f"Fetching: {scraper.PARTNER_LIST_URL}")
        resp = requests.get(scraper.PARTNER_LIST_URL, headers={
            'User-Agent': 'shopping-points-optimiser/1.0 (+https://example.local)'
        }, timeout=15)
        resp.raise_for_status()
        
        print("\n=== DEBUG INFO ===")
        print(f"Status Code: {resp.status_code}")
        print(f"HTML Length: {len(resp.text)}")
        print(f"Found 'partner-tile' in HTML: {'partner-tile' in resp.text}")
        
        # Save first 5000 chars to file for inspection
        with open('payback_debug.html', 'w', encoding='utf-8') as f:
            f.write(resp.text[:10000])
        print("\n✓ Saved first 10000 chars to payback_debug.html")
        
        # Search for common patterns
        print("\n=== CONTENT ANALYSIS ===")
        if '/shop/' in resp.text:
            print("✓ Found '/shop/' in HTML")
            # Find a few /shop/ URLs
            matches = re.findall(r'/shop/([a-z0-9\-]+)', resp.text)
            unique = list(set(matches))[:10]
            print(f"  Sample shops found: {unique}")
        else:
            print("✗ No '/shop/' found in HTML")
        
        if 'data-partner-vanity-name' in resp.text:
            print("✓ Found 'data-partner-vanity-name' in HTML")
        else:
            print("✗ No 'data-partner-vanity-name' found")
        
        if '<a' in resp.text:
            links = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>', resp.text)
            print(f"✓ Found {len(links)} <a> elements")
            print(f"  First 5 links: {links[:5]}")
        
        # Check if it looks like JS-rendered content (check for script tags, data attributes, etc)
        script_count = resp.text.count('<script')
        print(f"\n<script> tags in HTML: {script_count}")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        candidates = soup.find_all('a')
        print(f"BeautifulSoup found {len(candidates)} <a> elements total")
        
        if candidates:
            print("\nFirst 3 <a> elements:")
            for a in candidates[:3]:
                print(f"  {str(a)[:100]}...")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
