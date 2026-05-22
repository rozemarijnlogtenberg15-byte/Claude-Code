import re
from .profile import PROFILE


def is_casting_call(text: str) -> bool:
    phrases = [
        "casting call", "casting for", "looking for actor", "looking for actress",
        "looking for a actor", "looking for a actress", "looking for female",
        "actors wanted", "actress wanted", "actor needed", "actress needed",
        "actor required", "actress required", "seeking actor", "seeking actress",
        "open audition", "open call", "open casting", "now casting",
        "need an actor", "need actors", "need an actress",
        "roles available", "talent search", "we are casting",
        "submissions open", "submitting for", "accepting submissions",
        "come audition", "casting director", "#castingcall", "#casting",
        "auditions now", "audition date", "filming", "short film cast",
        "feature film cast",
    ]
    t = text.lower()
    return any(p in t for p in phrases)


def check_location(text: str) -> bool:
    t = text.lower()
    return any(term in t for term in PROFILE["location_terms"])


def check_gender(text: str) -> bool:
    """True if the opportunity includes female/non-binary, or if no gender is specified."""
    t = text.lower()

    # Explicit male-only patterns
    male_only = [
        r'\bmale\s+only\b',
        r'\bmen\s+only\b',
        r'\bman\s+only\b',
        # "for a male actor" but NOT "for a male or female actor"
        r'\bfor\s+(?:a\s+)?male\b(?!\s+(?:or|and)\s+female)',
        r'\bfor\s+(?:a\s+)?man\b(?!\s+(?:or|and)\s+(?:woman|female))',
        r'\bmale\s+actor\b(?!\s*(?:or|/)\s*female)',
        r'\bactor\s+\(male\)\b',
    ]
    for pattern in male_only:
        if re.search(pattern, t):
            return False

    gender_terms = PROFILE["gender_terms"] + ["male", "man", "men", "boy", "he/him"]
    gender_mentioned = any(term in t for term in gender_terms)

    # No gender mentioned → include (open casting)
    if not gender_mentioned:
        return True

    return any(term in t for term in PROFILE["gender_terms"])


def check_age_overlap(text: str) -> bool:
    """True if the age range overlaps 26–37, or if no age range is specified."""
    lo, hi = PROFILE["search_age_min"], PROFILE["search_age_max"]

    patterns = [
        r'\b(\d{2})\s*[-–—]\s*(\d{2})\b',
        r'\b(\d{2})\s+to\s+(\d{2})\b',
        r'aged?\s+(\d{2})\s*[-–—]\s*(\d{2})',
        r'between\s+(\d{2})\s+and\s+(\d{2})',
        r'ages?\s+(\d{2})\s*[-–—]\s*(\d{2})',
    ]

    found_range = False
    for pattern in patterns:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            a, b = int(m.group(1)), int(m.group(2))
            if a > b:
                a, b = b, a
            if not (18 <= a <= 70 and 18 <= b <= 70):
                continue  # Not a realistic age range, skip
            found_range = True
            if a <= hi and b >= lo:
                return True  # Overlap found

    return not found_range  # No range found → include


def score_match(title: str, snippet: str) -> dict:
    """
    Returns {"matches": bool, "score": int, "reasons": list[str]}.
    Score reflects how well the opportunity fits the profile.
    Hard filters (casting call, London, gender, age) must all pass.
    Skill bonuses increase score for better matches.
    """
    full = f"{title} {snippet}"

    if not is_casting_call(full):
        return {"matches": False, "score": 0, "reasons": ["Not a casting call"]}

    if not check_location(full):
        return {"matches": False, "score": 0, "reasons": ["Not in London"]}

    if not check_gender(full):
        return {"matches": False, "score": 0, "reasons": ["Gender mismatch"]}

    if not check_age_overlap(full):
        return {"matches": False, "score": 0, "reasons": ["Age range doesn't overlap 26–37"]}

    score = 50
    reasons = ["London casting, female/open gender, age 26–37"]

    full_lower = full.lower()
    for keyword, bonus in PROFILE["skills_bonus"].items():
        if keyword in full_lower:
            score += bonus
            reasons.append(f"Skill/appearance match: {keyword}")

    return {"matches": True, "score": score, "reasons": reasons}
