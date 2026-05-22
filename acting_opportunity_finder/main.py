"""
Acting Opportunity Finder — main pipeline.

Usage:
    python -m acting_opportunity_finder.main           # Normal run (deduped)
    python -m acting_opportunity_finder.main --all     # Show all matches, skip dedup
    python -m acting_opportunity_finder.main --dry-run # Print results, don't send email
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta, timezone

from .casting_sites import scrape_all as scrape_casting_sites
from .matcher import score_match
from .notifier import send_email
from .search import search as ddg_search
from .storage import filter_new

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DAYS_CUTOFF = 3


def _is_recent(result: dict) -> bool:
    """If a date is present and parseable, filter by DAYS_CUTOFF. Unknown dates pass."""
    date_str = result.get("date")
    if not date_str:
        return True
    try:
        from dateutil import parser as dateparser
        dt = dateparser.parse(date_str)
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        cutoff = datetime.now(timezone.utc) - timedelta(days=DAYS_CUTOFF)
        return dt >= cutoff
    except Exception:
        return True


def run(skip_dedup: bool = False, dry_run: bool = False) -> int:
    logger.info("=== Acting Opportunity Finder ===")
    logger.info("Filters: London | Female/non-binary | Age 26–37 | Last %d days", DAYS_CUTOFF)

    # Gather from all sources
    logger.info("--- Searching social media & web ---")
    raw = ddg_search(timelimit="w")

    logger.info("--- Scraping UK casting sites ---")
    raw += scrape_casting_sites()

    logger.info("Total raw results: %d", len(raw))

    # Deduplicate by URL within this run
    seen: set[str] = set()
    unique = [r for r in raw if not (r["url"] in seen or seen.add(r["url"]))]  # type: ignore[func-returns-value]
    logger.info("Unique URLs: %d", len(unique))

    # Date filter
    recent = [r for r in unique if _is_recent(r)]
    logger.info("Within %d days (or undated): %d", DAYS_CUTOFF, len(recent))

    # Profile matching
    matched = []
    for result in recent:
        scored = score_match(result["title"], result["snippet"])
        if scored["matches"]:
            result["score"] = scored["score"]
            result["reasons"] = scored["reasons"]
            matched.append(result)

    matched.sort(key=lambda x: x["score"], reverse=True)
    logger.info("Profile matches: %d", len(matched))

    # Deduplication against previous runs
    if skip_dedup:
        new_opportunities = matched
        logger.info("Dedup skipped (--all flag)")
    else:
        new_opportunities = filter_new(matched)
        logger.info("New (not seen before): %d", len(new_opportunities))

    if dry_run:
        logger.info("Dry run — skipping email")
        for i, opp in enumerate(new_opportunities, 1):
            print(f"\n{i}. [{opp.get('source')}] {opp['title']}")
            print(f"   {opp['url']}")
            print(f"   Score: {opp['score']} | {'; '.join(opp['reasons'])}")
    else:
        send_email(new_opportunities)

    return len(new_opportunities)


def main():
    parser = argparse.ArgumentParser(description="Find acting opportunities in London")
    parser.add_argument("--all", action="store_true", help="Show all matches, skip dedup")
    parser.add_argument("--dry-run", action="store_true", help="Print results, don't send email")
    args = parser.parse_args()

    count = run(skip_dedup=args.all, dry_run=args.dry_run)
    sys.exit(0 if count >= 0 else 1)


if __name__ == "__main__":
    main()
