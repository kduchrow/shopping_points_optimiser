"""Payback scraper using Playwright to handle JavaScript-rendered content."""

import os
import re
import sys

from playwright.sync_api import sync_playwright

from .base import BaseScraper

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class PaybackScraperJS(BaseScraper):
    """Scraper for Payback partner pages using Playwright for JS rendering."""

    PARTNER_LIST_URL = "https://www.payback.de/online-shopping/shop-a-z"
    TIMEOUT = 30000  # 30 seconds

    def _extract_numeric(self, text):
        """Extract numeric values from incentive text."""
        if not text:
            return {}

        result = {}

        # find percent values (Cashback) - e.g., "2.5%"
        m = re.search(r"(\d+[\.,]?\d*)\s*%", text)
        if m:
            result["cashback_pct"] = float(m.group(1).replace(",", "."))
            return result

        # find °P or Punkt patterns with EUR amounts - e.g., "1 °P pro 2 €", "2 Punkte je 1 €"
        # Match: number + (°P|Punkt|Punkte) + (pro|je) + number + (€|EUR|Euro)
        m = re.search(
            r"(\d+[\.,]?\d*)\s*(?:°P|Punkt|Punkte)\s*(?:pro|je)\s*(\d+[\.,]?\d*)\s*(?:€|EUR|Euro)",
            text,
            re.I,
        )
        if m:
            pts = float(m.group(1).replace(",", "."))
            per = float(m.group(2).replace(",", "."))
            result["points_per_eur"] = pts / per if per != 0 else 0.0
            print(
                f"[DEBUG] Extracted points_per_eur from '{text}': {pts} / {per} = {result['points_per_eur']}"
            )
            return result

        # Fallback: find simple point patterns (but exclude per-completion patterns)
        # e.g., "2 Punkte" but NOT "555 Punkte pro Abschluss"
        if "abschluss" not in text.lower() and "vertrag" not in text.lower():
            m = re.search(
                r"(\d+[\.,]?\d*)\s*(?:°P|Punkte|Punkt)(?:\s*je\s*(?:€|EUR|Euro))?", text, re.I
            )
            if m:
                pts = float(m.group(1).replace(",", "."))
                # Only treat as points_per_eur if it looks reasonable (< 100 and not a per-completion value)
                if pts < 100:
                    result["points_per_eur"] = pts
                    print(f"[DEBUG] Extracted simple points_per_eur from '{text}': {pts}")

        return result

    def fetch(self):
        """Fetch partners using Playwright for JavaScript rendering with scrolling."""
        results = []
        debug = {
            "status_code": None,
            "playwright_used": True,
            "partners_found": 0,
            "error": None,
            "button_clicks": 0,
            "final_tile_count": 0,
        }

        try:
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Navigate to main page (no letter parameter)
                print(f"Navigating to {self.PARTNER_LIST_URL}...")
                page.goto(self.PARTNER_LIST_URL, wait_until="networkidle", timeout=self.TIMEOUT)

                # Wait for partner tiles to load
                print("Waiting for partner tiles to load...")
                try:
                    page.wait_for_selector("a.partner-tile", timeout=15000)
                except Exception as e:
                    print(f"Error waiting for partner-tile: {e}")

                # Keep clicking "Mehr anzeigen" button until all shops are loaded
                button_clicks = 0
                max_clicks = 100  # safety limit
                consecutive_no_button = 0

                while button_clicks < max_clicks:
                    # Get current tile count
                    tiles = page.locator("a.partner-tile").all()
                    current_count = len(tiles)

                    # Scroll to bottom to make button visible
                    print(f"Scrolling to bottom (current tiles: {current_count})...")
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(1500)  # longer wait after scroll

                    # Look for the "Mehr anzeigen" button with retries
                    more_btn = None
                    for retry in range(3):
                        more_btns = page.locator("button.btn-show-more-partner")
                        btn_count = more_btns.count()
                        print(f"Search attempt {retry + 1}: Found {btn_count} button(s)")

                        if btn_count > 0:
                            # Try to use the last visible button (sometimes multiple buttons exist)
                            for i in range(btn_count):
                                btn = more_btns.nth(i)
                                try:
                                    if btn.is_visible():
                                        print(f"  Button {i} is visible, using it")
                                        more_btn = btn
                                        break
                                except Exception:
                                    pass
                            if more_btn:
                                break

                        if retry < 2:
                            page.wait_for_timeout(1000)  # wait before retry

                    if not more_btn:
                        print("No visible 'Mehr anzeigen' button found after retries.")
                        consecutive_no_button += 1
                        if consecutive_no_button >= 2:
                            print("Button missing consistently. Stopping.")
                            break
                        page.wait_for_timeout(2000)
                        continue
                    else:
                        consecutive_no_button = 0

                    try:
                        # Check if button is enabled
                        is_disabled = more_btn.is_disabled()
                        print(f"Button disabled: {is_disabled}")

                        if is_disabled:
                            print("Button is disabled. All shops loaded.")
                            break

                        # Click button
                        print(f"Clicking 'Mehr anzeigen' (click #{button_clicks + 1})...")
                        more_btn.click()
                        button_clicks += 1

                        # Wait longer for content to load
                        print("Waiting for new content to load...")
                        page.wait_for_timeout(2000)  # initial wait

                        try:
                            page.wait_for_load_state("networkidle", timeout=20000)
                            print("Content loaded (networkidle)")
                        except Exception:
                            print("networkidle timeout, waiting manually...")
                            page.wait_for_timeout(3000)

                        # Re-count tiles to ensure we get the updated count
                        page.wait_for_timeout(500)
                        new_tiles = page.locator("a.partner-tile").all()
                        new_count = len(new_tiles)
                        added = new_count - current_count
                        print(f"After click: {new_count} tiles (added {added})")

                        if added <= 0:
                            print(
                                f"No new tiles loaded after click (was {current_count}, now {new_count})."
                            )
                            print("Checking if button still exists...")
                            remaining_btns = page.locator("button.btn-show-more-partner").count()
                            print(f"Remaining buttons: {remaining_btns}")
                            break

                    except Exception as e:
                        print(f"Error clicking button: {e}")
                        import traceback

                        traceback.print_exc()
                        break

                    # Small delay between clicks
                    page.wait_for_timeout(1000)

                # Extract all shop data
                print(f"\nExtracting shop data from {len(tiles)} tiles...")
                tiles = page.locator("a.partner-tile").all()
                debug["final_tile_count"] = len(tiles)

                seen = set()
                for i, tile in enumerate(tiles):
                    try:
                        # Extract name
                        name_attr = tile.get_attribute("data-partner-vanity-name")
                        if not name_attr:
                            img = tile.locator("img").first
                            if img:
                                name_attr = img.get_attribute("alt")
                        if not name_attr:
                            name_attr = tile.text_content()

                        name = (name_attr or "").strip()
                        if not name or name in seen:
                            continue
                        seen.add(name)

                        # Extract incentive text
                        incentive_el = tile.locator(".partner-tile__incentive-text").first
                        incentive = incentive_el.text_content().strip() if incentive_el else ""

                        # Parse numeric values
                        numeric = self._extract_numeric(incentive)

                        # Detect per-completion points
                        per_completion = None
                        m = re.search(
                            r"(\d+[\.,]?\d*)\s*°?P\s*(?:pro|pro Abschluss)", incentive, re.I
                        )
                        if m:
                            per_completion = float(m.group(1).replace(",", "."))

                        rate = {
                            "program": "Payback",
                            "points_per_eur": numeric.get("points_per_eur", 0.0),
                            "cashback_pct": numeric.get("cashback_pct", 0.0),
                            "point_value_eur": 0.005,
                        }
                        if incentive:
                            rate["incentive_text"] = incentive
                        if per_completion is not None:
                            rate["per_completion_points"] = per_completion

                        results.append({"name": name, "rate": rate})

                    except Exception as e:
                        print(f"Error processing tile {i}: {e}")
                        continue

                    if len(results) >= 5000:
                        print("Reached 5000 shops limit.")
                        break

                browser.close()
                debug["status_code"] = 200
                debug["partners_found"] = len(results)
                debug["button_clicks"] = button_clicks

        except Exception as e:
            debug["error"] = str(e)
            print(f"Error during scraping: {e}")
            import traceback

            traceback.print_exc()

        return results, debug

    def fetch_partners(self):
        """Compatibility wrapper matching the async job interface."""
        partners, debug = self.fetch()
        # Keep latest debug snapshot for optional inspection by callers
        self.last_debug = debug
        return partners

    def register_partners(self, partners):
        """Register scraped partners into the database via BaseScraper helper."""
        added = 0
        for partner in partners:
            self.register_to_db({"name": partner["name"], "rates": [partner["rate"]]})
            added += 1
        return added
