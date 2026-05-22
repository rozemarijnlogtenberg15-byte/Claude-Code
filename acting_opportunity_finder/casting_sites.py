"""
Direct scraping of UK casting sites with public listings.
Falls back gracefully — if a site changes structure or blocks access,
the rest of the pipeline still runs.
"""
import logging
import time

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-GB,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def _get(url: str) -> BeautifulSoup | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as exc:
        logger.warning("Fetch failed [%s]: %s", url, exc)
        return None


def _extract_listings(soup: BeautifulSoup, base_url: str, source: str) -> list[dict]:
    """Generic extractor — tries common patterns for listing pages."""
    results = []

    # Try progressively broader selectors
    candidate_selectors = [
        "[class*='role']", "[class*='listing']", "[class*='audition']",
        "[class*='card']", "[class*='job']", "article", "li[class]",
    ]
    for sel in candidate_selectors:
        items = soup.select(sel)
        if len(items) >= 3:  # Found a meaningful list
            for item in items[:25]:
                title_el = item.find(["h2", "h3", "h4", "a"])
                link_el = item.find("a", href=True)
                snippet_el = item.find("p")
                if not (title_el and link_el):
                    continue
                href = link_el["href"]
                if not href.startswith("http"):
                    href = base_url.rstrip("/") + "/" + href.lstrip("/")
                results.append({
                    "title": title_el.get_text(strip=True),
                    "url": href,
                    "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                    "source": source,
                    "date": None,
                })
            break

    return results


def scrape_the_stage_rss() -> list[dict]:
    """The Stage jobs RSS — reliable dated feed."""
    results = []
    try:
        resp = requests.get(
            "https://www.thestage.co.uk/jobs/rss",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "xml")
        for item in soup.find_all("item")[:30]:
            title = item.find("title")
            link = item.find("link")
            desc = item.find("description")
            pub_date = item.find("pubDate")
            if title and link:
                results.append({
                    "title": title.get_text(strip=True),
                    "url": link.get_text(strip=True),
                    "snippet": BeautifulSoup(desc.get_text(), "html.parser").get_text()[:500] if desc else "",
                    "source": "The Stage",
                    "date": pub_date.get_text(strip=True) if pub_date else None,
                })
        logger.info("The Stage RSS: %d entries", len(results))
    except Exception as exc:
        logger.warning("The Stage RSS failed: %s", exc)
    return results


def scrape_casting_call_pro() -> list[dict]:
    """Casting Call Pro — London female roles."""
    url = "https://www.castingcallpro.com/uk/roles?location=London&gender=female"
    soup = _get(url)
    if not soup:
        return []
    results = _extract_listings(soup, "https://www.castingcallpro.com", "Casting Call Pro")
    logger.info("Casting Call Pro: %d listings", len(results))
    return results


def scrape_mandy() -> list[dict]:
    """Mandy.com UK auditions — London."""
    url = "https://www.mandy.com/uk/actor/auditions?location=London&gender=female"
    soup = _get(url)
    if not soup:
        return []
    results = _extract_listings(soup, "https://www.mandy.com", "Mandy.com")
    logger.info("Mandy.com: %d listings", len(results))
    return results


def scrape_starnow() -> list[dict]:
    """StarNow UK castings — London."""
    url = "https://www.starnow.co.uk/castings/?location=London&gender=female"
    soup = _get(url)
    if not soup:
        return []
    results = _extract_listings(soup, "https://www.starnow.co.uk", "StarNow")
    logger.info("StarNow: %d listings", len(results))
    return results


def scrape_all() -> list[dict]:
    results = []
    results.extend(scrape_the_stage_rss())
    time.sleep(2)
    results.extend(scrape_casting_call_pro())
    time.sleep(2)
    results.extend(scrape_mandy())
    time.sleep(2)
    results.extend(scrape_starnow())
    return results
