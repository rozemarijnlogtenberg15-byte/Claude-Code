"""
Acting submission email draft generator.

Creates a Gmail draft with personalised opening, headshots embedded in
the body, and Spotlight profile link — ready to review and send.

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
        --role "lead" \\
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

# ── Email templates ───────────────────────────────────────────────────────────

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<body style="font-family:Georgia,serif;max-width:580px;line-height:1.7;color:#111;margin:0;padding:0;">

<p>Hi,</p>

<p>{opening}</p>

<p>I'm Roze Logtenberg, bilingual Dutch-English actress based in London.
I trained at the Royal Central School of Speech and Drama, and I continue
to train in Meisner technique at a studio in London.</p>

<p>My most recent credits include a four-star reviewed two-hander at
The Cockpit Theatre — <em>"crafting a powerful and passionate performance
as a woman consumed by her grief"</em> (★★★★ Sam Waite) — and a Best Actress
nomination at the Couch Film Festival in Canada for the short film
<em>Day Off</em>.</p>

<p>Spotlight: <a href="{spotlight}">{spotlight}</a></p>

<p>
  <img src="cid:headshot1"
       alt="Roze Logtenberg"
       style="max-width:480px;width:100%;display:block;margin-bottom:14px;">
  <img src="cid:headshot2"
       alt="Roze Logtenberg"
       style="max-width:480px;width:100%;display:block;">
</p>

<p>Warmly,<br>Roze Logtenberg</p>

</body>
</html>"""

_PLAIN_TEMPLATE = """\
Hi,

{opening}

I'm Roze Logtenberg, bilingual Dutch-English actress based in London.
I trained at the Royal Central School of Speech and Drama, and I continue
to train in Meisner technique at a studio in London.

My most recent credits include a four-star reviewed two-hander at The
Cockpit Theatre — "crafting a powerful and passionate performance as a
woman consumed by her grief" (★★★★ Sam Waite) — and a Best Actress
nomination at the Couch Film Festival in Canada for the short film Day Off.

Spotlight: {spotlight}

Warmly,
Roze Logtenberg"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_posting(url: str) -> str:
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=12,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
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
        prompt = f"""Write 1–2 sentences to open an acting self-submission email from Roze Logtenberg.

The casting posting:
{posting_info or f"Role: {role}"}

About Roze: bilingual Dutch-English actress in London, trained at CSSD, Meisner-based. \
Recent: four-star review at The Cockpit Theatre, Best Actress nomination at Couch Film \
Festival for short film Day Off. Firearms trained for screen.

Rules:
- 1–2 sentences only — nothing else
- Reference something specific about THIS project or role
- No sycophancy: never "I'd be thrilled", "I'm so excited", "I'd love to"
- Don't start with "I'm writing" or "I came across your post"
- Start in the action — direct, warm, specific
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
        return (
            f"I'm putting myself forward for {role} — "
            "it reads like exactly the kind of specific, grounded work I'm looking for."
        )
    return "I'd like to put myself forward for this."


# ── Email assembly ────────────────────────────────────────────────────────────

def _build_message(to: str, subject: str, opening: str) -> MIMEMultipart:
    """
    Build a multipart/related message so the headshots display inline
    in the body rather than as attachments.
    """
    html_body = _HTML_TEMPLATE.format(opening=opening, spotlight=SPOTLIGHT_URL)
    plain_body = _PLAIN_TEMPLATE.format(opening=opening, spotlight=SPOTLIGHT_URL)

    # Root container: related allows CID image references
    root = MIMEMultipart("related")
    root["From"] = PROFILE["email"]
    root["To"] = to
    root["Subject"] = subject

    # Alternative container (plain + html) goes inside related
    alt = MIMEMultipart("alternative")
    root.attach(alt)
    alt.attach(MIMEText(plain_body, "plain", "utf-8"))
    alt.attach(MIMEText(html_body, "html", "utf-8"))

    # Embed headshots with CID references
    headshots = sorted(HEADSHOTS_DIR.glob("*.jpg"))
    cid_names = ["headshot1", "headshot2"]
    for path, cid in zip(headshots, cid_names):
        with open(path, "rb") as f:
            img = MIMEImage(f.read(), _subtype="jpeg")
        img.add_header("Content-ID", f"<{cid}>")
        img.add_header("Content-Disposition", "inline", filename=path.name)
        root.attach(img)

    return root


# ── Gmail draft via IMAP ──────────────────────────────────────────────────────

def _create_gmail_draft(msg: MIMEMultipart) -> bool:
    sender = PROFILE["email"]
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "")

    if not app_password:
        _print_fallback(msg)
        return False

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(sender, app_password)

        # Locate Drafts folder (name varies by account language)
        drafts_folder = "[Gmail]/Drafts"
        status, folders = mail.list()
        if status == "OK":
            for folder_bytes in folders:
                if b"\\Drafts" in folder_bytes:
                    parts = folder_bytes.decode().split('"/" ')
                    if len(parts) >= 2:
                        drafts_folder = parts[-1].strip().strip('"')
                    break

        mail.append(drafts_folder, r"\Draft", None, msg.as_bytes())
        mail.logout()

        print(f"\nDraft created in Gmail ✓")
        print(f"To: {msg['To']}")
        print(f"Subject: {msg['Subject']}")
        print("Open Gmail → Drafts to review and send.")
        return True

    except imaplib.IMAP4.error as exc:
        print(f"\nIMAP error: {exc}")
        print(
            "Make sure IMAP is enabled: Gmail Settings → "
            "See all settings → Forwarding and POP/IMAP → Enable IMAP"
        )
        _print_fallback(msg)
        return False
    except Exception as exc:
        print(f"\nFailed to create draft: {exc}")
        _print_fallback(msg)
        return False


def _print_fallback(msg: MIMEMultipart):
    print(f"\n{'─' * 60}")
    print(f"To: {msg['To']}")
    print(f"Subject: {msg['Subject']}")
    print(f"{'─' * 60}")
    # Recurse into parts to find plain text
    def find_plain(part):
        if part.get_content_type() == "text/plain":
            return part.get_payload(decode=True).decode("utf-8")
        if part.is_multipart():
            for sub in part.get_payload():
                result = find_plain(sub)
                if result:
                    return result
        return None
    plain = find_plain(msg)
    if plain:
        print(plain)
    print(f"{'─' * 60}")
    print("(Headshots would be embedded inline in the HTML version)")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate an acting submission email draft")
    parser.add_argument("--to", required=True, help="Recipient email address")
    parser.add_argument("--role", default="", help="Role name for the subject line")
    parser.add_argument("--url", default="", help="URL of the casting posting")
    parser.add_argument("--description", default="", help="Paste the casting description")
    parser.add_argument("--no-ai", action="store_true", help="Skip Claude — use standard opening")
    args = parser.parse_args()

    posting_info = ""
    if args.url:
        print("Fetching posting…")
        posting_info = _fetch_posting(args.url)
        if not posting_info:
            posting_info = args.url
    elif args.description:
        posting_info = args.description

    if args.no_ai:
        opening = _fallback_opening(args.role)
    else:
        print("Writing personalised opening…")
        opening = _generate_opening(posting_info, args.role)

    print(f"\nOpening: {opening}\n")

    role_label = args.role or "Self-Submission"
    subject = f"Roze Logtenberg – {role_label}"
    msg = _build_message(args.to, subject, opening)
    _create_gmail_draft(msg)


if __name__ == "__main__":
    main()
