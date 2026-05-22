#!/usr/bin/env python3
"""
Run this whenever you want to submit for an opportunity.

    python draft.py

It will ask you three questions and create a draft in your Gmail.
"""

import os
import sys

# Make sure the package is importable when run from the repo root
sys.path.insert(0, os.path.dirname(__file__))

from acting_opportunity_finder.submit import (
    _build_message,
    _create_gmail_draft,
    _fallback_opening,
    _fetch_posting,
    _generate_opening,
    SPOTLIGHT_URL,
)

print()
print("─" * 50)
print("  Acting Submission Draft Creator")
print("─" * 50)
print()

to = input("Recipient email address: ").strip()
if not to:
    print("No email address entered. Exiting.")
    sys.exit(1)

role = input("Role / what are you applying for: ").strip()

url = input("Paste the posting URL (or press Enter to skip): ").strip()

print()

posting_info = ""
if url:
    print("Fetching posting…")
    posting_info = _fetch_posting(url)
    if not posting_info:
        posting_info = url

print("Writing personalised opening…")
opening = _generate_opening(posting_info, role)

print()
print("Opening line:")
print(f"  {opening}")
print()

confirm = input("Looks good? Press Enter to create draft, or type 'edit' to write your own: ").strip().lower()
if confirm == "edit":
    opening = input("Your opening (1–2 sentences): ").strip()

role_label = role or "Self-Submission"
subject = f"Roze Logtenberg – {role_label}"
msg = _build_message(to, subject, opening)
_create_gmail_draft(msg)
print()
