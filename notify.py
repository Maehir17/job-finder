import smtplib
from collections import defaultdict
from email.message import EmailMessage
from html import escape

import config
from sources.base import Job


def _send(subject: str, html: str) -> None:
    if not config.GMAIL_USER or not config.GMAIL_APP_PASSWORD:
        raise RuntimeError("GMAIL_USER / GMAIL_APP_PASSWORD not set")
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config.GMAIL_USER
    msg["To"] = config.NOTIFY_EMAIL
    msg.set_content("This digest requires an HTML-capable email client.")
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
        smtp.starttls()
        smtp.login(config.GMAIL_USER, config.GMAIL_APP_PASSWORD)
        smtp.send_message(msg)


def send_digest(new_jobs: list[Job]) -> None:
    by_company: dict[str, list[Job]] = defaultdict(list)
    for j in new_jobs:
        by_company[j.company or "Unknown"].append(j)

    rows = []
    for company in sorted(by_company, key=str.lower):
        rows.append(f'<h3 style="margin:18px 0 6px">{escape(company)}</h3><ul style="margin:0">')
        for j in by_company[company]:
            meta = " · ".join(x for x in (j.location, j.date_posted, j.source) if x)
            rows.append(
                f'<li style="margin:4px 0"><a href="{escape(j.url)}">{escape(j.title)}</a>'
                f'<br><span style="color:#666;font-size:12px">{escape(meta)}</span></li>'
            )
        rows.append("</ul>")

    html = (
        f'<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:640px">'
        f"<h2>{len(new_jobs)} new entry-level SWE posting(s)</h2>"
        + "".join(rows)
        + "</div>"
    )
    _send(f"[Job Finder] {len(new_jobs)} new entry-level SWE role(s)", html)


def send_bootstrap(count: int) -> None:
    html = (
        '<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif">'
        f"<h2>Job Finder is live</h2><p>Tracking <b>{count}</b> current entry-level "
        "SWE postings. From now on you'll only be emailed about <b>new</b> ones.</p></div>"
    )
    _send(f"[Job Finder] Tracking {count} roles, setup complete", html)
