import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .profile import PROFILE


def send_email(opportunities: list):
    recipient = PROFILE["email"]
    sender = os.environ.get("GMAIL_SENDER", recipient)
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "")
    date_str = datetime.now().strftime("%d %b %Y")

    if not opportunities:
        print(f"[{date_str}] No new matching opportunities found.")
        return

    subject = f"Acting Opportunities — {len(opportunities)} new in London ({date_str})"
    html = _html(opportunities, date_str)
    plain = _plain(opportunities, date_str)

    if not app_password:
        print(f"\n{'=' * 60}")
        print(plain)
        print(f"{'=' * 60}")
        print("\nTip: set GMAIL_APP_PASSWORD to receive this as an email.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender, app_password)
        smtp.sendmail(sender, recipient, msg.as_string())

    print(f"Email sent to {recipient} — {len(opportunities)} opportunities.")


def _html(opportunities: list, date_str: str) -> str:
    items = ""
    for opp in opportunities:
        snippet = opp.get("snippet", "")[:350]
        if len(opp.get("snippet", "")) > 350:
            snippet += "…"
        reasons = "; ".join(opp.get("reasons", []))
        source_badge = (
            f'<span style="background:#e8e8e8;padding:2px 8px;border-radius:10px;'
            f'font-size:12px;font-family:sans-serif;">{opp.get("source", "Web")}</span>'
        )
        items += f"""
        <div style="margin:24px 0;padding:18px;border-left:4px solid #222;background:#fafafa;">
          <p style="margin:0 0 8px 0;">{source_badge}</p>
          <h3 style="margin:0 0 6px 0;font-size:17px;line-height:1.3;">
            <a href="{opp['url']}" style="color:#111;text-decoration:none;">{opp['title']}</a>
          </h3>
          <p style="margin:0 0 10px 0;font-size:14px;color:#444;line-height:1.5;">{snippet}</p>
          <p style="margin:0 0 12px 0;font-size:12px;color:#777;font-style:italic;">{reasons}</p>
          <a href="{opp['url']}"
             style="display:inline-block;padding:9px 16px;background:#111;color:#fff;
                    text-decoration:none;font-size:13px;border-radius:4px;font-family:sans-serif;">
            View →
          </a>
        </div>"""

    return f"""<html>
<body style="font-family:Georgia,serif;max-width:660px;margin:0 auto;padding:24px 20px;color:#111;">
  <h1 style="font-size:22px;border-bottom:2px solid #111;padding-bottom:12px;margin-bottom:4px;">
    Acting Opportunities
  </h1>
  <p style="color:#666;font-size:13px;font-family:sans-serif;margin-top:6px;">
    {date_str} &nbsp;·&nbsp; {len(opportunities)} new match{"es" if len(opportunities) != 1 else ""}
    &nbsp;·&nbsp; London &nbsp;·&nbsp; Female / non-binary &nbsp;·&nbsp; Age 26–37
  </p>
  {items}
  <p style="margin-top:32px;font-size:11px;color:#aaa;font-family:sans-serif;">
    Results from the last 3 days. Filtered to London, female/non-binary or open casting,
    age range overlapping 26–37. Sorted by profile match score.
  </p>
</body>
</html>"""


def _plain(opportunities: list, date_str: str) -> str:
    lines = [
        f"ACTING OPPORTUNITIES — {date_str}",
        f"{len(opportunities)} new in London (female/non-binary, age 26–37)",
        "",
    ]
    for i, opp in enumerate(opportunities, 1):
        lines += [
            f"{i}. {opp['title']}",
            f"   Source : {opp.get('source', 'Unknown')}",
            f"   {opp.get('snippet', '')[:200]}",
            f"   Why    : {'; '.join(opp.get('reasons', []))}",
            f"   Link   : {opp['url']}",
            "",
        ]
    return "\n".join(lines)
