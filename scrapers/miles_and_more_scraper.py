"""
Miles & More Scraper
Scrapes partner shops and their point rates from miles-and-more.com
"""
# noqa: E402
import os
import re
import sys
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from spo.extensions import db  # noqa: E402
from spo.models import BonusProgram, Proposal, Shop, ShopProgramRate, User  # noqa: E402
from spo.services.dedup import get_or_create_shop_main  # noqa: E402


class MilesAndMoreScraper:
    def __init__(self):
        self.base_url = "https://www.miles-and-more.com/de/de/program/partners.html"
        self.program_name = "MilesAndMore"
        self.system_user = None

    def get_or_create_system_user(self):
        """Get or create a special 'system' user for scraper-generated proposals"""
        if self.system_user:
            return self.system_user

        user = User.query.filter_by(username="_scraper_system").first()
        if not user:
            user = User(
                username="_scraper_system",
                email="scraper@system.local",
                role="contributor",
                password_hash="locked",  # System user, no login
            )
            db.session.add(user)
            db.session.commit()

        self.system_user = user
        return user

    def scrape(self):
        """
        Scrape Miles & More partners
        Returns: (shops_added, shops_updated, errors)
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("[!] Playwright not installed. Install with: pip install playwright")
            return 0, 0, []

        print("\n[*] Starting Miles & More scraper...")

        program = BonusProgram.query.filter_by(name=self.program_name).first()
        if not program:
            print(f"[!] {self.program_name} program not found in database")
            return 0, 0, [f"{self.program_name} program not found"]

        shops_added = 0
        shops_updated = 0
        errors = []

        with sync_playwright() as p:
            # Try to look less like a bot: real UA, locale, timezone, viewport, and hide webdriver flag
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                ),
                locale="de-DE",
                timezone_id="Europe/Berlin",
                viewport={"width": 1366, "height": 768},
                java_script_enabled=True,
                extra_http_headers={
                    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
                },
            )
            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )
            page = context.new_page()

            try:
                print(f"   [+] Loading {self.base_url}...")
                page.goto(self.base_url, wait_until="networkidle", timeout=45000)
                page.wait_for_timeout(1500)
                # Handle cookie banner if present; missing this often blocks content
                self._accept_cookies(page)
                # Try again after a short wait
                page.wait_for_timeout(1500)
                # Wait for partner list to load (more generous timeout, allow attached not only visible)
                page.wait_for_selector('a[href*="/partners/"]', timeout=60000, state="attached")

                # Scroll to load all partners
                print("   [+] Scrolling to load all partners...")
                last_height = page.evaluate("document.body.scrollHeight")
                scroll_count = 0
                max_scrolls = 40  # allow more scrolls for lazy loading

                while scroll_count < max_scrolls:
                    page.evaluate("window.scrollBy(0, window.innerHeight)")
                    time.sleep(1)

                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
                    scroll_count += 1

                # Get all partner links
                partner_links = page.locator('a[href*="/partners/"]').all()
                if not partner_links:
                    partner_links = page.locator(
                        'a.partner-tile, a[href*="/program/partners/"]'
                    ).all()
                if not partner_links:
                    print(
                        "   [!] Keine Partner-Links gefunden. Eventuell Cookie-Banner blockiert oder Layout geaendert."
                    )
                partner_urls = []

                for link in partner_links:
                    try:
                        href = link.get_attribute("href")
                        if href and "/partners/" in href:
                            shop_name = link.text_content().strip()
                            if shop_name and not shop_name.startswith("/"):
                                partner_urls.append(
                                    {
                                        "name": shop_name,
                                        "url": href
                                        if href.startswith("http")
                                        else f"https://www.miles-and-more.com{href}",
                                    }
                                )
                    except Exception:
                        continue

                print(f"   [+] Found {len(partner_urls)} partners")

                # Scrape each partner
                for i, partner in enumerate(partner_urls, 1):
                    try:
                        print(
                            f"   [{i}/{len(partner_urls)}] Scraping {partner['name']}...",
                            end="",
                            flush=True,
                        )

                        # Get or create ShopMain + ShopVariant with automatic deduplication
                        shop_main, is_new, confidence = get_or_create_shop_main(
                            shop_name=partner["name"],
                            source="miles_and_more",
                            source_id=partner.get("id"),
                        )

                        # For backward compatibility, also update legacy Shop table
                        legacy_shop = Shop.query.filter_by(name=partner["name"]).first()
                        if not legacy_shop:
                            legacy_shop = Shop(name=partner["name"], shop_main_id=shop_main.id)
                            db.session.add(legacy_shop)
                            db.session.commit()
                            shops_added += 1
                            print(" (NEW)", end="", flush=True)
                        else:
                            if not legacy_shop.shop_main_id:
                                legacy_shop.shop_main_id = shop_main.id
                            shops_updated += 1

                        # Scrape partner detail page
                        page.goto(partner["url"], wait_until="networkidle", timeout=15000)
                        time.sleep(0.5)

                        # Try to extract points rate
                        points_per_eur = self._extract_points_rate(page.content())
                        cashback_pct = 0.0

                        # Always create a rate, even if extraction fails
                        # Use fallback value and mark for manual review
                        if points_per_eur is None:
                            points_per_eur = 0.5  # Default fallback rate

                        # Update or create rate
                        rate = ShopProgramRate.query.filter_by(
                            shop_id=legacy_shop.id, program_id=program.id, valid_to=None
                        ).first()

                        if rate:
                            # Expire old rate
                            rate.valid_to = datetime.utcnow()

                        # Create new rate
                        new_rate = ShopProgramRate(
                            shop_id=legacy_shop.id,
                            program_id=program.id,
                            points_per_eur=points_per_eur,
                            cashback_pct=cashback_pct,
                            valid_from=datetime.utcnow(),
                        )
                        db.session.add(new_rate)
                        db.session.commit()

                        print(f" [OK] ({points_per_eur} P/EUR)")

                    except Exception as e:
                        error_msg = f"{partner['name']}: {str(e)}"
                        errors.append(error_msg)
                        print(" [ERROR]")

            except Exception as e:
                print(f"[!] Scraper error: {str(e)}")
                errors.append(f"Scraper error: {str(e)}")
                try:
                    page.screenshot(path="miles_more_error.png", full_page=True)
                    with open("miles_more_error.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                    print(
                        "   [+] Saved debug artifacts: miles_more_error.png / miles_more_error.html"
                    )
                except Exception:
                    pass
                browser.close()

        print("\n[OK] Miles & More scraping complete")
        print(f"   Added: {shops_added}, Updated: {shops_updated}, Errors: {len(errors)}")

        return shops_added, shops_updated, errors

    def _extract_points_rate(self, html):
        """
        Extract points per EUR from HTML content
        Returns: float or None if not found
        """
        # Make a plain-text version for simpler matching
        plain = re.sub(r"<[^>]+>", " ", html)
        plain = re.sub(r"\s+", " ", plain)

        # Common patterns for miles-and-more (digits with Meilen/Miles/icon)
        patterns = [
            r"(\d+[\d,.]*)\s*(?:|Meilen|Miles|Punkte|P\.?)\s*pro\s*(?:€|EUR|Euro)",
            r"(\d+[\d,.]*)\s*(?:Meilen|Miles|Punkte)\s*per\s*(\d+[\d,.]*)?\s*€",
            r"(\d+[\d,.]*)\s*(?:Meilen|Miles|Punkte)\s*pro\s*(\d+[\d,.]*)\s*€",
            r"pro\s*€\s*(\d+[\d,.]*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, plain, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    num_str = groups[0].replace(".", "").replace(",", ".")
                    points = float(num_str)
                    if len(groups) > 1 and groups[1]:
                        div_str = groups[1].replace(".", "").replace(",", ".")
                        divisor = float(div_str) if float(div_str) != 0 else 1.0
                        return points / divisor
                    return points
                except Exception:
                    continue

        # HTML-level pattern (tagged mainBenefit text)
        try:
            tag_match = re.search(r"offer__mainBenefitText[^>]*>([^<]+)", html, re.IGNORECASE)
            if tag_match:
                txt = tag_match.group(1)
                num_match = re.search(r"(\d+[\d,.]*)", txt)
                if num_match:
                    return float(num_match.group(1).replace(".", "").replace(",", "."))
        except Exception:
            pass

        return None

    def _accept_cookies(self, page):
        """Try to accept cookie banners so content loads."""
        selectors = [
            "#onetrust-accept-btn-handler",
            "button:has-text('Alle akzeptieren')",
            "button:has-text('Accept all')",
            "button.cookieconsent__buttonAcceptAll",  # observed on current page
            "button:has-text('Alle zulassen')",
            "button.cookieconsent__buttonAcceptAll .button__text:has-text('Alle zulassen')",
        ]
        for sel in selectors:
            try:
                btn = page.locator(sel)
                if btn.count() > 0:
                    btn.first.click(timeout=2000)
                    page.wait_for_timeout(500)
                    return True
            except Exception:
                continue
        return False

    def _create_scraper_proposal(self, user, shop, program, reason, source_url):
        """
        Create a proposal for manual review of scraped data
        """
        try:
            proposal = Proposal(
                proposal_type="rate_change",
                status="pending",
                source="scraper",  # Mark as from scraper
                user_id=user.id,
                shop_id=shop.id,
                program_id=program.id,
                proposed_points_per_eur=None,  # Unknown
                proposed_cashback_pct=None,
                reason=reason,
                source_url=source_url,
            )
            db.session.add(proposal)
            db.session.commit()
            return proposal.id
        except Exception as e:
            print(f"Error creating proposal: {e}")
            return None


def run_scraper():
    """Run the Miles & More scraper within an active app context."""
    scraper = MilesAndMoreScraper()
    added, updated, errors = scraper.scrape()

    return {"added": added, "updated": updated, "errors": errors}


if __name__ == "__main__":
    scraper = MilesAndMoreScraper()
    result = scraper.scrape()
    print(f"\nResult: {result}")
