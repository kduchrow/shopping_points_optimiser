"""TopCashback.de Scraper

Scrapes partner shops and their cashback rates from topcashback.de
TopCashback is a German cashback platform with 1,200+ partner shops.

API: No public API available
Data Access: Static HTML with minimal JavaScript
Difficulty: 2/5 (straightforward HTML parsing)
"""

import requests
from bs4 import BeautifulSoup

from .base import BaseScraper


class TopCashbackScraper(BaseScraper):
    def _extract_shop_url(self, div):
        """Extract shop URL from a BeautifulSoup div."""
        a_tag = div.find("a", href=True)
        if not a_tag:
            return None
        href = a_tag["href"]
        if href.startswith("http"):
            return href
        return f"{self.BASE_URL}{href}" if href.startswith("/") else f"{self.BASE_URL}/{href}"

    def __init__(self):
        super().__init__()
        self.session = requests.Session()

    @staticmethod
    def _extract_cashback_percentage(text):
        """Extract cashback percentage as float from text like 'Bis zu 8%' or '8% Cashback'"""
        import re

        if not text:
            return 0.0
        match = re.search(r"([\d,.]+)\s*%", text)
        if match:
            return float(match.group(1).replace(",", "."))
        return 0.0

    """Scraper for TopCashback partner shops.

    Notes:
    - TopCashback exposes merchants via category pages under `/kategorie/<name>/`.
    - We crawl categories from the homepage and extract merchant links and rates.
    """

    BASE_URL = "https://www.topcashback.de"

    def fetch(self):
        """Override this method to return a value or None if not overridden."""
        import time

        # Discover categories from homepage
        try:
            print("[*] Fetching TopCashback homepage to discover categories...")
            resp_home = self.session.get(self.BASE_URL, timeout=20)
            resp_home.raise_for_status()
        except requests.RequestException as e:
            print(f"[!] Error fetching TopCashback homepage: {e}")
            return []

        soup_home = BeautifulSoup(resp_home.text, "html.parser")
        category_links = []
        for a in soup_home.find_all("a", href=True):
            href = a.get("href")
            if not href:
                continue
            href_str = str(href)
            if "/kategorie/" in href_str:
                url = (
                    href_str
                    if href_str.startswith("http")
                    else (
                        f"{self.BASE_URL}{href_str}"
                        if href_str.startswith("/")
                        else f"{self.BASE_URL}/{href_str}"
                    )
                )
                category_links.append(url)

        category_links = sorted(set(category_links))
        if not category_links:
            print("[!] No category links found; cannot enumerate merchants")
            return []
        print(f"[+] Discovered {len(category_links)} category pages")

        NON_SHOP_NAMES = {
            "blog",
            "browser erweiterung",
            "browser-erweiterung",
            "app",
            "hilfe",
            "faq",
            "kontakt",
            "über uns",
            "impressum",
            "datenschutz",
            "agb",
            "browser extension",
            "extension",
            "newsletter",
            "community",
            "karriere",
            "jobs",
            "team",
            "partner werden",
            "partnerprogramm",
            "überblick",
            "ratgeber",
            "magazin",
            "news",
            "mein konto",
            "login",
            "registrieren",
            "logout",
            "bedingungen",
            "support",
            "feedback",
            "datenschutzerklärung",
            "cookie einstellungen",
            "cookies",
            "sicherheit",
            "preise",
            "angebote",
            "aktionen",
            "aktionen & angebote",
            "aktionen und angebote",
        }

        shop_map = {}
        for cat_url in category_links:
            print(f"[*] Crawling category: {cat_url}")
            # Extract category name from URL (e.g., /kategorie/elektronik/ -> elektronik)
            import re

            cat_match = re.search(r"/kategorie/([^/]+)/", cat_url)
            category_name = cat_match.group(1) if cat_match else cat_url
            page = 1
            while True:
                paged_url = f"{cat_url}?page={page}"
                try:
                    resp_cat = self.session.get(paged_url, timeout=20)
                    resp_cat.raise_for_status()
                except requests.RequestException as e:
                    print(f"[!] Error fetching category {paged_url}: {e}")
                    break

                soup_cat = BeautifulSoup(resp_cat.text, "html.parser")
                panels = soup_cat.find_all("a", class_="category-panel", href=True)
                if not panels:
                    break

                for panel in panels:
                    name_tag = panel.find("span", class_="search-merchant-name")
                    name = name_tag.get_text(strip=True) if name_tag else None
                    if not name:
                        continue
                    canonical = name.lower().strip()
                    if canonical in NON_SHOP_NAMES:
                        continue
                    shop_url = panel.get("href")
                    if shop_url:
                        shop_url = str(shop_url)
                        if shop_url.startswith("/"):
                            shop_url = f"{self.BASE_URL}{shop_url}"
                    cashback_tag = panel.find("span", class_="category-cashback-rate")
                    cashback_text = cashback_tag.get_text(strip=True) if cashback_tag else ""
                    description_tag = panel.find("span", class_="category-description")
                    description = description_tag.get_text(strip=True) if description_tag else ""

                    # Fetch detail page for all rates
                    rates = []
                    if shop_url:
                        shop_url = str(shop_url)
                        try:
                            resp_detail = self.session.get(shop_url, timeout=20)
                            resp_detail.raise_for_status()
                            soup_detail = BeautifulSoup(resp_detail.text, "html.parser")
                            for rate_card in soup_detail.find_all("div", class_="merch-rate-card"):
                                # Collect sub-categories and rate elements and pair them by index
                                subcat_elems = rate_card.find_all(
                                    "span", class_="merch-cat__sub-cat"
                                )
                                subcats = [s.get_text(strip=True) for s in subcat_elems]
                                rate_spans = rate_card.find_all("span", class_="merch-cat__rate")

                                import re as _re

                                for idx, rate_span in enumerate(rate_spans):
                                    rate_val = TopCashbackScraper._extract_cashback_percentage(
                                        rate_span.get_text(strip=True)
                                    )
                                    subcat_text = subcats[idx] if idx < len(subcats) else ""

                                    # Prefer the per-rate sub-category as the stored category (clean parentheses)
                                    category_field = category_name
                                    if subcat_text:
                                        cleaned = _re.sub(r"\s*\(.*\)\s*$", "", subcat_text).strip()
                                        if cleaned:
                                            category_field = cleaned

                                    rate_obj = {
                                        "program": "TopCashback",
                                        "cashback_pct": rate_val,
                                        "points_per_eur": 0.0,
                                        "point_value_eur": 0.0,
                                        "category": category_field,
                                    }
                                    if subcat_text:
                                        rate_obj["sub_category"] = subcat_text
                                    rates.append(rate_obj)
                        except Exception as e:
                            print(f"[!] Error fetching detail page for {name}: {e}")

                    # Fallback: if no rates found, use summary from category page
                    if not rates and cashback_text:
                        rate_val = TopCashbackScraper._extract_cashback_percentage(cashback_text)
                        rates.append(
                            {
                                "program": "TopCashback",
                                "cashback_pct": rate_val,
                                "points_per_eur": 0.0,
                                "point_value_eur": 0.0,
                                "category": category_name,
                            }
                        )

                    if not rates:
                        continue

                    # Deduplicate by canonical name
                    if canonical not in shop_map:
                        shop_map[canonical] = {
                            "name": name,
                            "description": description,
                            "rates": rates,
                            "category": category_name,
                            "source": "TopCashback",
                            "source_id": shop_url or canonical,
                        }
                    else:
                        # Merge rates if shop seen again
                        shop_map[canonical]["rates"].extend(rates)
                        if shop_url and not shop_map[canonical].get("source_id"):
                            shop_map[canonical]["source_id"] = shop_url
                        if description and len(description) > len(
                            shop_map[canonical]["description"]
                        ):
                            shop_map[canonical]["description"] = description

                page += 1
                time.sleep(0.5)  # Be polite

        # ...existing code...
        # For test compatibility: if called in test context, return (results, debug)
        results = list(shop_map.values())
        # If running in test, return (results, debug) if requested

        return results
