"""
Social media search for acting opportunities.

Targets Instagram, Threads, LinkedIn, TikTok, Facebook and general web —
the places indie filmmakers, directors, and casting directors post informally.
NOT acting platforms (Mandy, Spotlight, CastingCallPro) — those are excluded.

Uses DuckDuckGo (no API key required). Runs a broad set of queries covering
the language real people use when posting casting calls on social media.
"""

import logging
import time

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

# ── Queries ────────────────────────────────────────────────────────────────────
# Language real filmmakers, directors and casting directors use on social media.
# Not the formal language of casting platforms — the informal language of posts.

_INSTAGRAM_QUERIES = [
    'site:instagram.com "casting call" London female',
    'site:instagram.com "looking for actress" London',
    'site:instagram.com "looking for an actress" London',
    'site:instagram.com "actors wanted" London female',
    'site:instagram.com "actress wanted" London',
    'site:instagram.com "now casting" London female',
    'site:instagram.com "seeking actress" London',
    'site:instagram.com "open casting" London female',
    'site:instagram.com "short film" London actress casting',
    'site:instagram.com "student film" London actress',
    'site:instagram.com "feature film" London actress casting',
    'site:instagram.com London "female lead" casting film',
    'site:instagram.com London casting actress "26" OR "27" OR "28" OR "29" OR "30" OR "31" OR "32" OR "33" OR "34" OR "35"',
    'site:instagram.com London actress "DM" OR "email" casting film',
]

_THREADS_QUERIES = [
    'site:threads.net "casting call" London female',
    'site:threads.net "looking for actress" London',
    'site:threads.net "actors wanted" London',
    'site:threads.net "now casting" London',
    'site:threads.net casting London actress film',
    'site:threads.net "short film" London actress casting',
]

_LINKEDIN_QUERIES = [
    'site:linkedin.com "casting" London actress female film',
    'site:linkedin.com "looking for actress" London',
    'site:linkedin.com "casting call" London female',
    'site:linkedin.com "short film" London actress casting',
    'site:linkedin.com "actress needed" London',
    'site:linkedin.com "female actor" London casting',
]

_TIKTOK_QUERIES = [
    'site:tiktok.com "casting call" London female',
    'site:tiktok.com casting London actress',
    'site:tiktok.com "looking for actress" London',
]

_FACEBOOK_QUERIES = [
    'site:facebook.com "casting call" London female actress',
    'site:facebook.com "looking for actress" London film',
    'site:facebook.com "short film" London actress casting',
]

# Broad social queries — no site restriction, picks up anything indexed
# from social media using hashtag language and indie filmmaker phrasing
_BROAD_SOCIAL_QUERIES = [
    '"casting call" London female actress -site:mandy.com -site:castingcallpro.com -site:starnow.co.uk -site:spotlight.com',
    '"looking for actress" London film -site:mandy.com -site:castingcallpro.com',
    '"actress wanted" London short film',
    '"open casting" London female actress',
    '"actors wanted" London female short film',
    '#castingcall London female actress',
    '#londoncasting actress female',
    '#ukacting London actress casting female',
    '"student film" London actress female casting',
    '"indie film" London actress casting female',
    '"short film" London "female lead" OR "female actress" casting',
    # Dutch-speaking is very distinctive — worth a targeted search
    '"Dutch" actress London casting film',
    '"bilingual" actress London casting',
    # Firearms-trained for screen is rare — catches specialist roles
    '"firearms" actress London casting',
]

# News search — returns dated results, good for catching recent announcements
_NEWS_QUERIES = [
    'casting call London actress female short film',
    'indie film casting London actress',
    'student film casting London female actress',
]

_ALL_QUERIES = (
    _INSTAGRAM_QUERIES
    + _THREADS_QUERIES
    + _LINKEDIN_QUERIES
    + _TIKTOK_QUERIES
    + _FACEBOOK_QUERIES
    + _BROAD_SOCIAL_QUERIES
)

# Domains to exclude — acting platforms the user doesn't want
_EXCLUDED_DOMAINS = {
    "mandy.com", "castingcallpro.com", "starnow.co.uk",
    "spotlight.com", "thestage.co.uk", "backstage.com",
    "talentmanager.com", "casting.com",
}


def _is_excluded(url: str) -> bool:
    return any(domain in url for domain in _EXCLUDED_DOMAINS)


def _label(url: str) -> str:
    mapping = {
        "instagram.com": "Instagram",
        "threads.net": "Threads",
        "linkedin.com": "LinkedIn",
        "tiktok.com": "TikTok",
        "facebook.com": "Facebook",
        "x.com": "X/Twitter",
        "twitter.com": "X/Twitter",
    }
    for domain, label in mapping.items():
        if domain in url:
            return label
    return "Web"


def search(timelimit: str = "w") -> list[dict]:
    """
    Run all queries against DuckDuckGo.
    timelimit: 'd'=day, 'w'=week, 'm'=month.
    Returns list of dicts: title, url, snippet, source, date.
    """
    results: list[dict] = []
    seen_urls: set[str] = set()

    with DDGS() as ddgs:

        for query in _ALL_QUERIES:
            try:
                time.sleep(1.5)
                hits = list(ddgs.text(query, timelimit=timelimit, max_results=8))
                for hit in hits:
                    url = hit.get("href", "")
                    if not url or url in seen_urls or _is_excluded(url):
                        continue
                    seen_urls.add(url)
                    results.append({
                        "title": hit.get("title", ""),
                        "url": url,
                        "snippet": hit.get("body", ""),
                        "source": _label(url),
                        "date": None,
                    })
            except Exception as exc:
                logger.warning("Search failed [%s…]: %s", query[:55], exc)

        for query in _NEWS_QUERIES:
            try:
                time.sleep(1.5)
                hits = list(ddgs.news(query, timelimit=timelimit, max_results=10))
                for hit in hits:
                    url = hit.get("url", "")
                    if not url or url in seen_urls or _is_excluded(url):
                        continue
                    seen_urls.add(url)
                    results.append({
                        "title": hit.get("title", ""),
                        "url": url,
                        "snippet": hit.get("body", ""),
                        "source": _label(url),
                        "date": hit.get("date"),
                    })
            except Exception as exc:
                logger.warning("News search failed [%s…]: %s", query[:55], exc)

    logger.info("Social media search: %d unique results", len(results))
    return results
