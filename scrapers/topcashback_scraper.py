"""TopCashback.de Scraper

Scrapes partner shops and their cashback rates from topcashback.de
TopCashback is a German cashback platform with 1,200+ partner shops.

API: No public API available
Data Access: Static HTML with minimal JavaScript
Difficulty: 2/5 (straightforward HTML parsing)
"""

import re

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper


class TopCashbackScraper(BaseScraper):
    """Scraper for TopCashback partner shops.

    Notes:
    - TopCashback has a clean partner directory at /partner/
    - Partner list is static HTML with minimal JS rendering
    - robots.txt allows crawling /partner/ paths
    - No explicit scraping prohibition in ToS
    """

    BASE_URL = "https://www.topcashback.de"
    PARTNER_DIRECTORY = "https://www.topcashback.de/partner/"

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "shopping-points-optimiser/1.0 (+https://github.com/kduchrow/shopping_points_optimiser)"
            }
        )

    def _extract_cashback_percentage(self, text):
        """Extract cashback percentage from incentive text.

        Examples:
            "3,5% Cashback" -> 3.5
            "Bis zu 5% Cashback" -> 5.0
            "5.0% Bonus" -> 5.0
        """
        if not text:
            return 0.0

        # Match patterns like "3,5%", "5%", "Bis zu 5%"
        match = re.search(r"(bis zu\s+)?(\d+[\.,]\d+|\d+)\s*%", text, re.IGNORECASE)
        if match:
            value_str = match.group(2).replace(",", ".")
            try:
                return float(value_str)
            except ValueError:
                return 0.0

        return 0.0

    def _extract_shop_url(self, shop_element):
        """Extract shop URL from partner element."""
        # Try to find link within the element
        link = shop_element.find("a", href=True)
        if link:
            href = link.get("href", "").strip()
            if href:
                # Convert relative URLs to absolute
                if href.startswith("/"):
                    return self.BASE_URL + href
                elif href.startswith("http"):
                    return href
        return None

    def fetch(self):
        """Fetch TopCashback partners and their cashback rates.

        Returns:
            list: List of dicts with keys:
                - name: shop name
                - rate: dict with program, cashback_pct, point_value_eur, etc.
        """
        results = []
        debug = {
            "status_code": None,
            "html_length": 0,
            "partners_found": 0,
            "error": None,
        }

        try:
            print("[*] Fetching TopCashback partner directory...")
            resp = self.session.get(
                self.PARTNER_DIRECTORY,
                timeout=20,
            )
            resp.raise_for_status()
            debug["status_code"] = resp.status_code
            debug["html_length"] = len(resp.text or "")

        except requests.RequestException as e:
            error_msg = f"Error fetching TopCashback partners: {e}"
            print(f"[!] {error_msg}")
            debug["error"] = error_msg
            return results, debug

        try:
            soup = BeautifulSoup(resp.text, "html.parser")

            # TopCashback uses various container classes for partner tiles
            # Common selectors: .partner-tile, .shop-item, .partner-box, [data-partner-*]
            partner_containers = []

            # Try multiple selectors (TopCashback structure may vary)
            selectors = [
                ("div.partner-tile", "class=partner-tile"),
                ("a.partner-link", "class=partner-link"),
                ("div.shop-item", "class=shop-item"),
                ("div[data-shop-id]", "data-shop-id attribute"),
                ("div.partner-box", "class=partner-box"),
            ]

            for selector, desc in selectors:
                found = soup.select(selector)
                if found:
                    print(f"[+] Found {len(found)} partners using selector: {desc}")
                    partner_containers = found
                    break

            # Fallback: find all links that look like partner pages
            if not partner_containers:
                print("[*] No standard partner containers found, trying fallback link matching...")
                partner_containers = soup.find_all(
                    "a", href=re.compile(r"/partner/", re.IGNORECASE)
                )
                print(f"[+] Found {len(partner_containers)} potential partner links")

            seen_names = set()

            for container in partner_containers:
                try:
                    # Extract shop name
                    shop_name = None

                    # Try various name sources
                    if isinstance(container, type(soup)) and container.name in ["a"]:
                        # It's a link element
                        shop_name = container.get_text(strip=True)
                    else:
                        # It's a div/container
                        # Try data attribute first
                        shop_name = container.get("data-shop-name") or container.get(
                            "data-partner-name"
                        )

                        # Try heading/title elements
                        if not shop_name:
                            heading = container.find(["h2", "h3", "h4"])
                            if heading:
                                shop_name = heading.get_text(strip=True)

                        # Try img alt text
                        if not shop_name:
                            img = container.find("img", alt=True)
                            if img:
                                shop_name = img.get("alt", "").strip()

                        # Fallback to visible text
                        if not shop_name:
                            shop_name = container.get_text(" ", strip=True)[:100]  # Limit length

                    shop_name = (shop_name or "").strip()
                    if not shop_name or len(shop_name) < 2 or shop_name in seen_names:
                        continue

                    seen_names.add(shop_name)

                    # Extract cashback rate
                    incentive_text = ""
                    cashback_pct = 0.0

                    # Look for incentive/rate text
                    rate_el = container.select_one(
                        ".incentive-text, .rate, .cashback-rate, .bonus-text, [data-rate]"
                    )
                    if rate_el:
                        incentive_text = rate_el.get_text(" ", strip=True)

                    if not incentive_text:
                        # Try to get text from any element with percentage
                        text_content = container.get_text(" ", strip=True)
                        # Extract first percentage found
                        pct_match = re.search(r"(\d+[\.,]\d+|\d+)\s*%", text_content)
                        if pct_match:
                            incentive_text = pct_match.group(0)

                    if incentive_text:
                        cashback_pct = self._extract_cashback_percentage(incentive_text)

                    # Extract shop URL if available
                    shop_url = self._extract_shop_url(container)

                    # Build rate record
                    rate = {
                        "program": "TopCashback",
                        "cashback_pct": cashback_pct,
                        "points_per_eur": 0.0,  # TopCashback uses cashback %, not points
                        "point_value_eur": 0.01,  # 1% cashback ≈ 1 cent value
                    }

                    if incentive_text:
                        rate["incentive_text"] = incentive_text

                    if shop_url:
                        rate["shop_url"] = shop_url

                    results.append(
                        {
                            "name": shop_name,
                            "rate": rate,
                        }
                    )

                    if len(results) >= 2000:  # Limit to prevent runaway
                        break

                except Exception as e:
                    print(f"[!] Error processing partner element: {e}")
                    continue

            debug["partners_found"] = len(results)
            print(f"[+] Successfully scraped {len(results)} TopCashback partners")

        except Exception as e:
            error_msg = f"Error parsing TopCashback HTML: {e}"
            print(f"[!] {error_msg}")
            debug["error"] = error_msg

        return results, debug
