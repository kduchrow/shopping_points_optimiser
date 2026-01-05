import re
import requests
from bs4 import BeautifulSoup
from .base import BaseScraper


class PaybackScraper(BaseScraper):
    """Simple scraper for Payback partner pages.

    Notes:
    - This is a best-effort implementation. HTML structure may change; adapt selectors accordingly.
    - Run locally and respect Payback's robots.txt / terms of service.
    """

    PARTNER_LIST_URL = 'https://www.payback.de/online-shopping/shop-a-z'

    def _extract_numeric(self, text):
        if not text:
            return None
        # find percent values
        m = re.search(r"(\d+[\.,]?\d*)\s*%", text)
        if m:
            return {'cashback_pct': float(m.group(1).replace(',', '.'))}
        # find patterns like '1 Punkt je 1 €' or '1 Punkt pro 1 €'
        m = re.search(r"(\d+[\.,]?\d*)\s*(?:Punkt|Punkte)\s*(?:je|pro)\s*(\d+[\.,]?\d*)\s*(?:€|EUR)", text, re.I)
        if m:
            pts = float(m.group(1).replace(',', '.'))
            per = float(m.group(2).replace(',', '.'))
            return {'points_per_eur': pts / per if per != 0 else 0.0}
        # fallback: find 'Punkte' with a single number -> treat as points per euro
        m = re.search(r"(\d+[\.,]?\d*)\s*(?:Punkte|Punkt)", text, re.I)
        if m:
            return {'points_per_eur': float(m.group(1).replace(',', '.'))}
        return {}

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
        # partner tiles are <a class="partner-tile ...">
        candidates = soup.find_all('a', class_=re.compile(r'partner-tile', re.I))
        # fallback: links that point to /shop/<name>
        if not candidates:
            candidates = soup.find_all('a', href=re.compile(r'^/shop/'))

        seen = set()
        for c in candidates:
            # prefer data-partner-vanity-name, fallback to img alt or visible text
            name = c.get('data-partner-vanity-name') or None
            if not name:
                img = c.find('img', alt=True)
                if img:
                    name = img['alt']
            if not name:
                name = c.get_text(' ', strip=True)

            name = (name or '').strip()
            if not name or name in seen:
                continue
            seen.add(name)

            # incentive text inside .partner-tile__incentive-text
            incentive_el = c.select_one('.partner-tile__incentive-text')
            incentive = incentive_el.get_text(' ', strip=True) if incentive_el else ''

            numeric = self._extract_numeric(incentive)

            # detect points-per-completion like '555 °P pro Abschluss'
            per_completion = None
            m = re.search(r"(\d+[\.,]?\d*)\s*°?P\s*(?:pro|pro Abschluss|pro Abschluss)", incentive, re.I)
            if m:
                per_completion = float(m.group(1).replace(',', '.'))

            rate = {
                'program': 'Payback',
                'points_per_eur': numeric.get('points_per_eur', 0.0),
                'cashback_pct': numeric.get('cashback_pct', 0.0),
                'point_value_eur': 0.005,
            }
            # include raw incentive and per-completion info as metadata
            if incentive:
                rate['incentive_text'] = incentive
            if per_completion is not None:
                rate['per_completion_points'] = per_completion

            results.append({'name': name, 'rate': rate})

            if len(results) >= 1000:
                break

        debug = {
            'status_code': resp.status_code,
            'html_length': len(resp.text or ''),
            'found_partner_tile': ('partner-tile' in (resp.text or '')),
            'candidates_count': len(candidates),
        }

        return results, debug
