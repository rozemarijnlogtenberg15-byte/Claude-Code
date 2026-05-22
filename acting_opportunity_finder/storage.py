import json
import os
from datetime import datetime, timedelta, timezone

_FILE = os.path.join(os.path.dirname(__file__), "seen_opportunities.json")
_KEEP_DAYS = 14


def _load() -> dict:
    if not os.path.exists(_FILE):
        return {}
    with open(_FILE) as f:
        return json.load(f)


def _save(seen: dict):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=_KEEP_DAYS)).isoformat()
    pruned = {url: ts for url, ts in seen.items() if ts > cutoff}
    with open(_FILE, "w") as f:
        json.dump(pruned, f, indent=2, sort_keys=True)


def filter_new(opportunities: list) -> list:
    """Return opportunities not seen before and persist them as seen."""
    seen = _load()
    now = datetime.now(timezone.utc).isoformat()
    new = []
    for opp in opportunities:
        if opp["url"] not in seen:
            new.append(opp)
            seen[opp["url"]] = now
    _save(seen)
    return new
