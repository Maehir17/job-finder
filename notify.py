from collections import defaultdict
from html import escape

import requests

import config
from sources.base import Job


def _send(subject: str, html: str) -> None:
    if not config.RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY not set")
    r = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {config.RESEND_API_KEY}"},
        json={
            "from": config.SENDER,
            "to": [config.NOTIFY_EMAIL],
            "subject": subject,
            "html": html,
        },
        timeout=30,
    )
    r.raise_for_status()


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
