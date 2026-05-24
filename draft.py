#!/usr/bin/env python3
"""
Run this whenever you want to submit for an opportunity.

    python draft.py

Paste either a URL or the text of the posting — works for Instagram,
Threads, TikTok, DMs, anything. Then enter the recipient email and
a draft will appear in your Gmail ready to review and send.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from acting_opportunity_finder.submit import (
    _build_message,
    _create_gmail_draft,
    _fetch_posting,
    SPOTLIGHT_URL,
)
from acting_opportunity_finder.profile import PROFILE

try:
    import anthropic
    _CLIENT = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
except Exception:
    _CLIENT = None


def generate_opening_and_subject(posting_text: str) -> tuple[str, str]:
    """Return (opening sentence, subject line) from the posting."""
    if not _CLIENT or not os.environ.get("ANTHROPIC_API_KEY"):
        return (
            "I'd like to put myself forward for this.",
            "Roze Logtenberg – Self-Submission",
        )
    try:
        msg = _CLIENT.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": f"""You are helping Roze Logtenberg write a self-submission email for an acting role.

The casting posting:
{posting_text}

Return exactly two lines — nothing else:
LINE 1: A subject line in the format "Roze Logtenberg – [role or project name]"
LINE 2: 1–2 sentences opening the email. Rules: reference something specific about this project; no sycophancy ("I'd be thrilled", "I'm so excited"); don't start with "I'm writing" or "I came across"; direct, warm, specific — sounds like a person not a form letter."""
            }],
        )
        lines = msg.content[0].text.strip().splitlines()
        subject = lines[0].strip() if lines else "Roze Logtenberg – Self-Submission"
        opening = lines[1].strip() if len(lines) > 1 else "I'd like to put myself forward for this."
        return opening, subject
    except Exception as exc:
        print(f"(Claude unavailable: {exc} — using standard opening)")
        return (
            "I'd like to put myself forward for this.",
            "Roze Logtenberg – Self-Submission",
        )


print()
print("─" * 50)
print("  Acting Submission Draft Creator")
print("─" * 50)
print()
print("Paste a URL, or copy and paste the posting text")
print("directly (works for Instagram, Threads, DMs,")
print("anything). Then press Enter twice when done.")
print()

lines = []
while True:
    line = input()
    if line == "" and lines:
        break
    lines.append(line)

posting_input = "\n".join(lines).strip()

if not posting_input:
    print("Nothing entered. Exiting.")
    sys.exit(1)

# URL or raw text?
if posting_input.startswith("http"):
    print("\nFetching posting…")
    fetched = _fetch_posting(posting_input)
    posting_text = fetched if fetched else posting_input
else:
    posting_text = posting_input

print()
to = input("Recipient email address: ").strip()
if not to:
    print("No email address entered. Exiting.")
    sys.exit(1)

print()
print("Writing personalised opening…")
opening, subject = generate_opening_and_subject(posting_text)

print()
print(f"Subject : {subject}")
print(f"Opening : {opening}")
print()

confirm = input("Looks good? Press Enter to create draft, or type 'edit' to write your own opening: ").strip().lower()
if confirm == "edit":
    opening = input("Your opening (1–2 sentences): ").strip()
    role_override = input("Subject line role (e.g. 'lead, short film'): ").strip()
    if role_override:
        subject = f"Roze Logtenberg – {role_override}"

msg = _build_message(to, subject, opening)
_create_gmail_draft(msg)
print()
