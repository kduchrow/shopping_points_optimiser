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
    - TopCashback exposes merchants via category pages under `/kategorie/<name>/`.
    - We crawl categories from the homepage and extract merchant links and rates.
    """

    BASE_URL = "https://www.topcashback.de"

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "shopping-points-optimiser/1.0 (+https://github.com/kduchrow/shopping_points_optimiser)"
            }
        )

    def _extract_cashback_percentage(self, text: str) -> float:
        if not text:
            return 0.0
        m = re.search(r"(bis zu\s+)?(\d+[\.,]\d+|\d+)\s*%", text, re.I)
        if m:
            try:
                return float(m.group(2).replace(",", "."))
            except ValueError:
                return 0.0
        return 0.0

    def _extract_shop_url(self, container) -> str | None:
        link = container.find("a", href=True)
        if not link:
            return None
        href = (link.get("href") or "").strip()
        if not href:
            return None
        if href.startswith("/"):
            return f"{self.BASE_URL}{href}"
        if href.startswith("http"):
            return href
        return None

    def fetch(self):
        results = []
        debug = {
            "status_code": None,
            "html_length": 0,
            "partners_found": 0,
            "error": None,
            "categories_traversed": 0,
        }

        # Discover categories from homepage
        try:
            print("[*] Fetching TopCashback homepage to discover categories...")
            resp_home = self.session.get(self.BASE_URL, timeout=20)
            resp_home.raise_for_status()
            debug["status_code"] = resp_home.status_code
            debug["html_length"] = len(resp_home.text or "")
        except requests.RequestException as e:
            msg = f"Error fetching TopCashback homepage: {e}"
            print(f"[!] {msg}")
            debug["error"] = msg
            return results, debug

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
            debug["error"] = "No category links found on homepage"
            print("[!] No category links found; cannot enumerate merchants")
            return results, debug
        debug["categories_traversed"] = len(category_links)
        print(f"[+] Discovered {len(category_links)} category pages")

        seen_names = set()
        for cat_url in category_links:
            try:
                resp_cat = self.session.get(cat_url, timeout=20)
                resp_cat.raise_for_status()
            except requests.RequestException as e:
                print(f"[!] Error fetching category {cat_url}: {e}")
                continue

            soup_cat = BeautifulSoup(resp_cat.text, "html.parser")
            merchant_links = soup_cat.find_all(
                "a",
                href=re.compile(r"^/[a-z0-9-]+/$"),
            )

            for link in merchant_links:
                name = link.get_text(strip=True) or None
                if not name:
                    img = link.find("img", alt=True)
                    if img:
                        alt = img.get("alt")
                        if alt:
                            name = str(alt).strip()
                name = (name or "").strip()
                if not name or name in seen_names:
                    continue
                seen_names.add(name)

                cashback_pct = 0.0
                incentive_text = ""
                text_block = link.get_text(" ", strip=True)
                m = re.search(r"(\d+[\.,]\d+|\d+)\s*%", text_block)
                if not m and link.parent:
                    text_block = link.parent.get_text(" ", strip=True)
                    m = re.search(r"(\d+[\.,]\d+|\d+)\s*%", text_block)
                if m:
                    incentive_text = m.group(0)
                    cashback_pct = self._extract_cashback_percentage(incentive_text)

                shop_url = str(link.get("href") or "")
                if shop_url.startswith("/"):
                    shop_url = f"{self.BASE_URL}{shop_url}"

                rate = {
                    "program": "TopCashback",
                    "cashback_pct": cashback_pct,
                    "points_per_eur": 0.0,
                    "point_value_eur": 0.01,
                }
                if incentive_text:
                    rate["incentive_text"] = incentive_text
                if shop_url:
                    rate["shop_url"] = shop_url

                results.append({"name": name, "rate": rate})
                if len(results) >= 2000:
                    break
            if len(results) >= 2000:
                break

        debug["partners_found"] = len(results)
        print(
            f"[+] Successfully enumerated {len(results)} merchants across {debug['categories_traversed']} categories"
        )
        return results, debug
