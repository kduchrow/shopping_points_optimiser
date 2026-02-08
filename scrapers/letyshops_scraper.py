"""
LetyShops scraper (HTML-first approach).

Provides `LetyshopsScraper.fetch()` which returns a list of shop dicts
in the same shape as other scrapers in this project.
"""

import logging
import re

import requests
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper

logger = logging.getLogger("LetyShopsScraper")


class LetyshopsScraper(BaseScraper):
    BASE_URL = "https://letyshops.com"
    LISTING_PATH = "/de/shops"

    def fetch(self) -> list[dict]:
        """Fetch shops by scraping the paginated listing pages.

        Returns a list of shop dicts: {name, rates, source_id, source}
        """
        shops = []
        page = 1
        while True:
            url = f"{self.BASE_URL}{self.LISTING_PATH}?page={page}"
            try:
                resp = requests.get(url, timeout=15)
                resp.raise_for_status()
            except Exception as e:
                logger.error("Failed to fetch %s: %s", url, e)
                break

            page_shops = self.parse_shops_from_html(resp.text)
            if not page_shops:
                break
            shops.extend(page_shops)

            # Basic pagination stop: if fewer than a typical page (e.g. < 1), stop.
            # We rely on server-rendered pages; this is conservative.
            if len(page_shops) < 1:
                break
            page += 1
            # Safety cap to avoid infinite loops
            if page > 50:
                logger.warning("Reached page cap while scraping LetyShops")
                break

        # After collecting listing teasers, try to enrich each shop with
        # detail (per-category) rates where available. We do this here so
        # callers receive a shop dict where the teaser rate is replaced by
        # categorized rates when present (avoids keeping an empty-category
        # teaser alongside real category rates).
        for item in shops:
            sid = item.get("source_id")
            if not sid:
                continue
            try:
                detail_rates = self.fetch_shop_detail(sid)
                if detail_rates:
                    # Replace teaser rates with detail rates (detail_rates
                    # are already filtered to contain meaningful categories).
                    item["rates"] = detail_rates
            except Exception as e:
                logger.debug("Error fetching detail for %s: %s", sid, e)

        return shops

    def fetch_shop_detail(self, source_id: str) -> list[dict]:
        """Fetch a shop detail page and parse rates per category.

        Returns a list of rate dicts with `category` when available.
        """
        url = f"{self.BASE_URL}{self.LISTING_PATH}/{source_id}"
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            logger.debug("Failed to fetch shop detail %s: %s", url, e)
            return []

        return self.parse_shop_detail(resp.text)

    @staticmethod
    def parse_shop_detail(html: str) -> list[dict]:
        """Parse a shop detail page to extract per-category rates.

        Strategy:
        - Parse table rows with category and value
        - Fallback: look for elements containing both a category-like text and a percent
        """
        soup = BeautifulSoup(html, "html.parser")
        rates: list[dict] = []

        # 1) Table rows
        for tr in soup.select("table tr"):
            cols = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if len(cols) < 2:
                continue
            cat = cols[0]
            val_txt = cols[1]
            m = re.search(r"(\d+[\.,]?\d*)\s*%", val_txt)
            if m:
                try:
                    val = float(m.group(1).replace(",", "."))
                except Exception:
                    continue
                # Clean category text
                cat_clean = cat.strip() if cat else None
                if cat_clean:
                    # Ignore obvious non-category phrases
                    if re.search(
                        r"\b(bis zu|achtung|achtung!|monat|monate|monaten|monatlich|tage?)\b",
                        cat_clean.lower(),
                    ):
                        cat_clean = None
                    # Drop review/rating fragments like 'Bewertungen bei ... (1)'
                    if re.search(r"^\s*Bewertungen bei\b", cat_clean, flags=re.I):
                        cat_clean = None
                rates.append(
                    {
                        "program": "LetyShops",
                        "points_per_eur": 0.0,
                        "cashback_pct": val,
                        "point_value_eur": 0.0,
                        "category": cat_clean,
                    }
                )

        # 2) Targeted grid parsing: look for the promo box whose heading contains "Informationen & Bedingungen"
        if not rates:
            grid_parsed = False
            container = None
            for c in soup.select("div.pl-4"):
                heading = c.select_one(".font-heading, .font-extrabold, .font-bold")
                if heading and "informationen" in heading.get_text(strip=True).lower():
                    container = c
                    break

            if container:
                grid = container.select_one("div.grid")
                if grid:
                    # Preferred: find percent wrappers and their following description divs
                    wrappers = grid.select("div.whitespace-nowrap")
                    for w in wrappers:
                        sp = w.select_one("span.text-red-500, span.text-red-600, span.font-bold")
                        if not sp:
                            continue
                        left = sp.get_text(" ", strip=True)
                        m = re.search(r"(\d+[\.,]?\d*)\s*%", left)
                        if not m:
                            continue
                        try:
                            val = float(m.group(1).replace(",", "."))
                        except Exception:
                            continue

                        # Prefer the immediate next sibling with class 'ml-2'
                        desc = None
                        nxt = w.find_next_sibling()
                        while nxt is not None and not getattr(nxt, "get_text", None):
                            nxt = nxt.find_next_sibling()
                        if nxt and "ml-2" in (nxt.get("class") or []):
                            desc = nxt.get_text(" ", strip=True)
                        else:
                            # fallback: look for next element with class ml-2
                            alt = w.find_next(
                                lambda t: getattr(t, "get", None)
                                and "ml-2" in (t.get("class") or [])
                            )
                            if alt:
                                desc = alt.get_text(" ", strip=True)

                        if desc:
                            desc = re.sub(r"\s+", " ", desc).strip()
                            desc = re.sub(
                                r"\b(in\s+)?\d+\s+(monat|monate|monaten|wochen|tage)\b",
                                "",
                                desc,
                                flags=re.I,
                            ).strip()
                            low = desc.lower()
                            # discard JS blobs, long strings or links injected by third-party scripts
                            if re.search(
                                r"datalayer|googletagmanager|gtm\.js|window\.datalayer|function\(|http[s]?://|<script|googletag|server_side_tagging",
                                low,
                            ):
                                desc = None
                            if len(desc) > 140:
                                desc = None
                            # Drop review/rating fragments like 'Bewertungen bei ... (1)'
                            if desc and re.search(r"^\s*Bewertungen bei\b", desc, flags=re.I):
                                desc = None

                        rates.append(
                            {
                                "program": "LetyShops",
                                "points_per_eur": 0.0,
                                "cashback_pct": val,
                                "point_value_eur": 0.0,
                                "category": desc,
                            }
                        )
                        grid_parsed = True

            # fallback to generic percent text parsing if grid not found
            if not grid_parsed:
                candidates = soup.find_all(text=re.compile(r"\d+[\.,]?\d*\s*%"))

                def _is_noise(text: str) -> bool:
                    if not text:
                        return True
                    t = text.strip()
                    if len(t) <= 2:
                        return True
                    low = t.lower()
                    # blacklist short/noisy words
                    if re.match(r"^(hier|mehr|anzeigen|link|details?|achtung!?|bis zu)$", low):
                        return True
                    # durations, months, days, numeric-only
                    if re.search(
                        r"\b(monat|monate|monaten|monatlich|wochen|tage|stunden|in\b)\b", low
                    ):
                        return True
                    if re.match(r"^[0-9\s]+$", t):
                        return True
                    return False

                def _clean_category(text: str) -> str | None:
                    if not text:
                        return None
                    s = re.sub(r"\s+", " ", text).strip()
                    # strip trailing duration phrases like 'in 2 Monaten' or '2 Monaten'
                    s = re.sub(
                        r"\b(in\s+)?\d+\s+(monat|monate|monaten|wochen|tage)\b", "", s, flags=re.I
                    ).strip()
                    s = s.strip("-:,. ")
                    # Drop review/rating fragments like 'Bewertungen bei ... (1)'
                    if re.search(r"^\s*Bewertungen bei\b", s, flags=re.I):
                        return None
                    if _is_noise(s):
                        return None
                    return s

                for txt in candidates:
                    parent = getattr(txt, "parent", None)
                    # ignore text inside script/style/noscript tags
                    if parent is not None and getattr(parent, "name", None) in {
                        "script",
                        "noscript",
                        "style",
                    }:
                        continue
                    # skip very long text nodes (likely injected JS blobs)
                    if isinstance(txt, str) and len(txt.strip()) > 300:
                        continue
                    cat = None

                    # Look for nearby text: previous siblings, next siblings, and nearby headings
                    nearby_texts = []
                    if parent is not None:
                        # previous siblings (most relevant)
                        for sib in list(parent.previous_siblings)[-6:]:
                            try:
                                t = sib.get_text(strip=True)
                            except Exception:
                                t = str(sib).strip()
                            if t:
                                nearby_texts.append(t)
                        # next siblings
                        for sib in list(parent.next_siblings)[:6]:
                            try:
                                t = sib.get_text(strip=True)
                            except Exception:
                                t = str(sib).strip()
                            if t:
                                nearby_texts.append(t)
                        # headings before parent
                        h = parent.find_previous(
                            lambda t: getattr(t, "name", None) in {"h2", "h3", "h4", "strong"}
                        )
                        if h:
                            nearby_texts.append(h.get_text(strip=True))

                    # pick first meaningful nearby text
                    for cand in nearby_texts:
                        cleaned = _clean_category(cand)
                        if cleaned:
                            cat = cleaned
                            break

                    m = re.search(r"(\d+[\.,]?\d*)\s*%", txt)
                    if m:
                        try:
                            val = float(m.group(1).replace(",", "."))
                        except Exception:
                            continue
                        rates.append(
                            {
                                "program": "LetyShops",
                                "points_per_eur": 0.0,
                                "cashback_pct": val,
                                "point_value_eur": 0.0,
                                "category": cat,
                            }
                        )

        # Remove any rates that do not have an explicit category label.
        rates = [r for r in rates if r.get("category")]

        # Only return detail rates when we found at least one explicit category label.
        # If no categories were detected, return empty so callers keep the basic listing rate.
        if not rates:
            return []

        return rates

    @staticmethod
    def parse_shops_from_html(html: str) -> list[dict]:
        """Parse listing HTML and return a list of shop dicts.

        The parser is intentionally forgiving: it looks for anchors whose
        href starts with `/de/shops/` and extracts name, link, logo and a
        cashback teaser when present.
        """
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []

        anchors = soup.select('a[href^="/de/shops/"]')
        seen = set()
        for a in anchors:
            href = a.get("href") or ""
            # Normalize href to avoid duplicates
            if href in seen:
                continue
            seen.add(href)

            # Shop name: try common candidate elements first
            def _clean_name(s: str) -> str:
                if not s:
                    return s
                s = s.strip()
                # If the string looks like a cashback teaser, drop it
                if re.match(r"^\d+[\.,]?\d*\s*%", s) or "cashback" in s.lower():
                    return ""
                return s

            name = None
            name_el = a.select_one(".text-sm, .shop-title, .title, h3, .b-card__title, strong")
            if name_el:
                cand = _clean_name(name_el.get_text(strip=True))
                if cand:
                    name = cand

            # Fallback: try to find name in ancestor card if anchor text is noisy
            if not name:
                parent = a
                for _ in range(3):
                    parent = parent.parent
                    if parent is None:
                        break
                    # look for heading elements inside parent
                    h = parent.select_one("h3, h2, .shop-title, .title, strong")
                    if h:
                        cand = _clean_name(h.get_text(strip=True))
                        if cand:
                            name = cand
                            break

            # Final fallback: use link text but clean cashback-like phrases
            if not name:
                cand = _clean_name(a.get_text(separator=" ", strip=True))
                name = cand or None

            # Logo
            logo_el = a.select_one("img")
            logo = None
            if logo_el and logo_el.get("src"):
                logo = logo_el.get("src")

            # Cashback: look for patterns like '1.5 %' or '1.5%'
            cashback_pct = None
            # Search within the anchor for a percent sign
            txt = a.get_text(" ", strip=True)
            m = re.search(r"(\d+[\.,]?\d*)\s*%", txt)
            if m:
                try:
                    cashback_pct = float(m.group(1).replace(",", "."))
                except Exception:
                    cashback_pct = None

            rates = []
            if cashback_pct is not None:
                rates.append(
                    {
                        "program": "LetyShops",
                        "points_per_eur": 0.0,
                        "cashback_pct": cashback_pct,
                        "point_value_eur": 0.0,
                    }
                )

            shop = {
                "name": name or None,
                "rates": rates,
                "logo": logo,
                "source_id": href.split("/")[-1] if href else None,
                "source": "Letyshops",
            }
            # Fallback: if name is missing, derive a readable name from source_id
            if not shop["name"] and shop.get("source_id"):
                sid = shop["source_id"]
                # strip common prefixes like 'shop-'
                sid = re.sub(r"^shop-", "", sid)
                # replace hyphens/underscores with spaces and title-case
                pretty = sid.replace("-", " ").replace("_", " ").strip()
                pretty = " ".join(p.title() for p in pretty.split())
                shop["name"] = pretty
            results.append(shop)

        return results
