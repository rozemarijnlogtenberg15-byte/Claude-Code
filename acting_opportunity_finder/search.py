"""
Searches for acting opportunities across social media and casting sites
using DuckDuckGo (no API key required).
"""
import logging
import time

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

# --- Social media queries ---
# Targeted at posts on Instagram, Threads, TikTok, X, Facebook
_SOCIAL_QUERIES = [
    # Instagram
    'casting call London female site:instagram.com',
    '"looking for" actress London site:instagram.com',
    '"actors wanted" London female site:instagram.com',
    '"now casting" London female site:instagram.com',
    # Threads
    'casting call London female site:threads.net',
    '"looking for" actress London site:threads.net',
    # TikTok
    'casting London actress short film site:tiktok.com',
    '"casting call" London female site:tiktok.com',
    # X / Twitter
    '"casting call" London female site:x.com',
    '"actors wanted" London female site:x.com',
    '"looking for" actress London "short film" site:x.com',
    # Facebook public posts
    '"casting call" London female site:facebook.com',
]

# --- Casting platform queries ---
# UK-specific casting sites that casting directors actively post on
_PLATFORM_QUERIES = [
    'site:mandy.com London actress female casting',
    'site:castingcallpro.com London female actress',
    'site:starnow.co.uk London female actress casting',
    'site:thestage.co.uk London actress audition',
    'site:spotlight.com casting London female',
]

# --- Broad casting call queries ---
# Catches anything that slipped through platform/social searches
_BROAD_QUERIES = [
    '"casting call" London female actress "short film"',
    '"looking for actors" London female',
    '"actors wanted" London female actress',
    '"open casting" London female',
    '"now casting" London female actress',
    '"casting director" London "looking for" female actress',
    '#londoncastingcall actress female',
    '#ukcastingcall London female actress',
    '"bilingual" casting London Dutch OR European actress',
    '"firearms" casting London actress',  # Matches Roze's rare skill
]

# News search queries (DuckDuckGo news returns dated results)
_NEWS_QUERIES = [
    'casting call London actress female',
    'UK short film casting London actress',
    'London theatre casting actress',
    'casting call London non-binary actress',
]


def search(timelimit: str = "w") -> list[dict]:
    """
    Run all queries. timelimit: 'd'=day, 'w'=week, 'm'=month.
    Returns list of dicts with keys: title, url, snippet, source, date.
    """
    results: list[dict] = []
    seen_urls: set[str] = set()

    with DDGS() as ddgs:
        all_text_queries = _SOCIAL_QUERIES + _PLATFORM_QUERIES + _BROAD_QUERIES

        for query in all_text_queries:
            try:
                time.sleep(1.2)  # Respectful pacing
                hits = list(ddgs.text(query, timelimit=timelimit, max_results=8))
                for hit in hits:
                    url = hit.get("href", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        results.append({
                            "title": hit.get("title", ""),
                            "url": url,
                            "snippet": hit.get("body", ""),
                            "source": _label(url),
                            "date": None,
                        })
            except Exception as exc:
                logger.warning("Text search failed [%s…]: %s", query[:50], exc)

        for query in _NEWS_QUERIES:
            try:
                time.sleep(1.2)
                hits = list(ddgs.news(query, timelimit=timelimit, max_results=10))
                for hit in hits:
                    url = hit.get("url", "")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        results.append({
                            "title": hit.get("title", ""),
                            "url": url,
                            "snippet": hit.get("body", ""),
                            "source": _label(url),
                            "date": hit.get("date"),
                        })
            except Exception as exc:
                logger.warning("News search failed [%s…]: %s", query[:50], exc)

    logger.info("DuckDuckGo search: %d unique results", len(results))
    return results


def _label(url: str) -> str:
    mapping = {
        "instagram.com": "Instagram",
        "threads.net": "Threads",
        "tiktok.com": "TikTok",
        "x.com": "X/Twitter",
        "twitter.com": "X/Twitter",
        "facebook.com": "Facebook",
        "mandy.com": "Mandy.com",
        "castingcallpro.com": "Casting Call Pro",
        "starnow.co.uk": "StarNow",
        "thestage.co.uk": "The Stage",
        "spotlight.com": "Spotlight",
    }
    for domain, label in mapping.items():
        if domain in url:
            return label
    return "Web"
