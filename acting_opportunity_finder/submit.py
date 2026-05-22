"""
Acting submission email draft generator.

Creates a Gmail draft with personalised opening, two headshots attached,
and Spotlight profile link — ready to review and send.

Usage:
    # With a URL (script fetches the posting):
    python -m acting_opportunity_finder.submit \\
        --to filmmaker@example.com \\
        --role "Elena, lead" \\
        --url https://www.instagram.com/p/XXXXX/

    # With a pasted description:
    python -m acting_opportunity_finder.submit \\
        --to filmmaker@example.com \\
        --role "lead role" \\
        --description "Looking for a female actress 26-35 for a psychological thriller..."

    # Without Claude API (uses standard opening):
    python -m acting_opportunity_finder.submit \\
        --to filmmaker@example.com \\
        --no-ai
"""

import argparse
import imaplib
import os
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .profile import PROFILE

SPOTLIGHT_URL = "https://app.spotlight.com/9310-6724-9673"
HEADSHOTS_DIR = Path(__file__).parent / "headshots"

# Email body — follows her voice: no warm-up, specific credits, plain sign-off
_BODY_TEMPLATE = """{opening}

Bilingual Dutch-English actress based in London. Royal Central School of Speech and Drama (Acting Diploma, 2024), with ongoing Meisner training. Most recent work: four-star reviewed two-hander at The Cockpit Theatre — "crafting a powerful and passionate performance" — and a Best Actress nomination at the Couch Film Festival for the short film Day Off.

Full profile and CV: {spotlight}

Two headshots attached. Showreel available on request.

Roze Logtenberg
{email}
Represented by SIDONALD LTD"""


def _fetch_posting(url: str) -> str:
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=12,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Strip nav/footer noise — main content only
        for tag in soup(["nav", "footer", "header", "script", "style"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as exc:
        print(f"Could not fetch posting: {exc}")
        return ""


def _generate_opening(posting_info: str, role: str) -> str:
    """Claude writes a personalised 1–2 sentence opening in Roze's voice."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _fallback_opening(role)

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        prompt = f"""Write the opening 1–2 sentences of an acting self-submission email from Roze Logtenberg.

The casting posting:
{posting_info or f'Role: {role}'}

About Roze: Bilingual Dutch-English actress based in London. Trained at CSSD (Meisner-based). Strong in emotional, grounded, specific work — comedy and drama. Recent four-star review at The Cockpit, Best Actress nomination (Couch Film Festival). Firearms trained for screen. Represented by SIDONALD LTD.

Rules:
- 1–2 sentences only — nothing else
- Reference something specific about THIS project or role
- No sycophancy: never "I'd be thrilled", "I'm so excited", "I'd love to"
- No preamble: don't start with "I'm writing" or "I came across"
- Start in the action — direct, warm, confident
- Sound like a person, not a form letter"""

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception as exc:
        print(f"Claude API call failed ({exc}) — using standard opening.")
        return _fallback_opening(role)


def _fallback_opening(role: str) -> str:
    if role:
        return f"I'm submitting for {role} — it looks like the kind of specific, character-driven work I'm drawn to."
    return "I'd like to put myself forward for this."


def _build_message(to: str, subject: str, body: str) -> MIMEMultipart:
    msg = MIMEMultipart()
    msg["From"] = PROFILE["email"]
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    for headshot in sorted(HEADSHOTS_DIR.glob("*.jpg")):
        with open(headshot, "rb") as f:
            img = MIMEImage(f.read(), _subtype="jpeg")
            img.add_header("Content-Disposition", "attachment", filename=headshot.name)
            msg.attach(img)

    return msg


def _create_gmail_draft(msg: MIMEMultipart) -> bool:
    """Append message to Gmail Drafts via IMAP — no OAuth needed."""
    sender = PROFILE["email"]
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "")

    if not app_password:
        _print_fallback(msg)
        return False

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(sender, app_password)

        # Find the Drafts folder (name varies by account language)
        drafts_folder = "[Gmail]/Drafts"
        status, folders = mail.list()
        if status == "OK":
            for folder_bytes in folders:
                if b"\\Drafts" in folder_bytes:
                    # Extract folder name from response like: (\Drafts) "/" "[Gmail]/Drafts"
                    parts = folder_bytes.decode().split('"/" ')
                    if len(parts) >= 2:
                        drafts_folder = parts[-1].strip().strip('"')
                    break

        mail.append(drafts_folder, r"\Draft", None, msg.as_bytes())
        mail.logout()

        print(f"\nDraft created in Gmail ✓")
        print(f"To: {msg['To']}")
        print(f"Subject: {msg['Subject']}")
        print(f"Open Gmail → Drafts to review and send.")
        return True

    except imaplib.IMAP4.error as exc:
        print(f"\nIMAP error: {exc}")
        print("Check that IMAP is enabled in Gmail Settings → See all settings → Forwarding and POP/IMAP.")
        _print_fallback(msg)
        return False
    except Exception as exc:
        print(f"\nFailed to create draft: {exc}")
        _print_fallback(msg)
        return False


def _print_fallback(msg: MIMEMultipart):
    """Print the email to terminal when no Gmail connection is available."""
    print(f"\n{'─' * 60}")
    print(f"To: {msg['To']}")
    print(f"Subject: {msg['Subject']}")
    print(f"{'─' * 60}")
    for part in msg.get_payload():
        if hasattr(part, "get_content_type") and part.get_content_type() == "text/plain":
            print(part.get_payload(decode=True).decode("utf-8"))
    print(f"{'─' * 60}")
    headshots = list(HEADSHOTS_DIR.glob("*.jpg"))
    print(f"Attachments: {', '.join(h.name for h in headshots)}")


def main():
    parser = argparse.ArgumentParser(description="Generate an acting submission email draft")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--role", default="", help="Role name for the subject line")
    parser.add_argument("--url", default="", help="URL of the casting posting")
    parser.add_argument("--description", default="", help="Paste the casting description directly")
    parser.add_argument("--no-ai", action="store_true", help="Skip Claude API — use standard opening")
    args = parser.parse_args()

    # Build posting context for personalisation
    posting_info = ""
    if args.url:
        print(f"Fetching posting…")
        posting_info = _fetch_posting(args.url)
        if not posting_info:
            posting_info = args.url
    elif args.description:
        posting_info = args.description

    # Generate personalised opening
    if args.no_ai:
        opening = _fallback_opening(args.role)
    else:
        print("Writing personalised opening…")
        opening = _generate_opening(posting_info, args.role)

    print(f"\nOpening line: {opening}\n")

    body = _BODY_TEMPLATE.format(
        opening=opening,
        spotlight=SPOTLIGHT_URL,
        email=PROFILE["email"],
    )

    role_label = args.role or "Self-Submission"
    subject = f"Roze Logtenberg – {role_label}"

    msg = _build_message(args.to, subject, body)
    _create_gmail_draft(msg)


if __name__ == "__main__":
    main()
