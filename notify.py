import re
from datetime import datetime, timezone
from html import escape
from urllib.parse import quote

import requests

import config
from sources.base import Job

_ACCENT = "#4f46e5"
_INK = "#14161b"
_MUTED = "#6b7280"
_FAINT = "#9aa1ad"
_LINE = "#eef1f4"
_PAGE = "#eceff3"
_BORDER = "#e6e9ee"
_TILE = "#eceef2"
_FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"

# Favicon service: always returns an image (a globe when the domain is unknown),
# so rows never show a broken image; the guessed domain just may be generic.
_LOGO = "https://www.google.com/s2/favicons?domain={}&sz=128"
_CORP = re.compile(
    r"\b(inc|llc|corp|corporation|ltd|co|group|holdings|technologies|technology|labs|the)\b",
    re.I,
)


def _domain(company: str) -> str:
    c = (company or "").strip()
    if not c:
        return ""
    if "." in c and " " not in c:  # already a domain, e.g. "Study.com"
        return c.lower()
    c = _CORP.sub("", c)
    slug = re.sub(r"[^a-z0-9]", "", c.lower())
    return f"{slug}.com" if slug else ""


def _initials(company: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", company or "")
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def _age(date_posted: str) -> tuple[str, int]:
    try:
        d = datetime.strptime(date_posted[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return "", 999
    days = (datetime.now(timezone.utc).date() - d).days
    return ("today" if days <= 0 else f"{days}d"), days


def _send(subject: str, html: str, to: str, api_key: str) -> None:
    if not api_key:
        raise RuntimeError("Resend API key not set")
    r = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": config.SENDER,
            "to": [to],
            "subject": subject,
            "html": html,
        },
        timeout=30,
    )
    r.raise_for_status()


def _row(j: Job) -> str:
    role = escape(j.title)
    company = escape(j.company or "Unknown")
    location = escape(j.location or "")
    meta = f"{company} &middot; {location}" if location else company
    age_label, days = _age(j.date_posted)
    url = escape(j.url)
    logo = _LOGO.format(quote(_domain(j.company)))
    initials = escape(_initials(j.company))
    dot = (
        '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;'
        'background:#0e9f6e;margin-right:7px;vertical-align:middle"></span>'
        if days <= 2
        else ""
    )
    edge = f"border-top:1px solid {_LINE}"
    return (
        f"<tr>"
        f'<td style="padding:13px 6px 13px 22px;{edge};width:30px;vertical-align:middle">'
        f'<img src="{logo}" width="30" height="30" alt="{initials}" '
        f'style="width:30px;height:30px;border-radius:8px;border:1px solid {_TILE};'
        f'background:#fff;object-fit:contain;display:block"></td>'
        f'<td style="padding:13px 10px;{edge};vertical-align:middle">'
        f'<div style="font-size:16px;font-weight:600;color:{_INK}">{dot}{role}</div>'
        f'<div style="font-size:14px;color:{_MUTED};margin-top:3px">{meta}</div></td>'
        f'<td style="padding:13px 8px;{edge};vertical-align:middle;font-size:13px;'
        f'color:{_FAINT};white-space:nowrap">{age_label}</td>'
        f'<td style="padding:13px 22px 13px 8px;{edge};vertical-align:middle;white-space:nowrap">'
        f'<a href="{url}" style="background:{_ACCENT};color:#fff;text-decoration:none;'
        f'font-size:14px;font-weight:600;padding:9px 16px;border-radius:8px;'
        f'display:inline-block">Apply</a></td>'
        f"</tr>"
    )


def send_digest(new_jobs: list[Job], to: str, hero_noun: str = "software",
                subject_noun: str = "entry-level SWE",
                api_key: str = "") -> None:
    # Freshest first; postings without a date sort to the bottom.
    jobs = sorted(new_jobs, key=lambda j: j.date_posted or "", reverse=True)
    n = len(jobs)
    s = "" if n == 1 else "s"
    rows = "".join(_row(j) for j in jobs)
    date = datetime.now(timezone.utc).strftime("%a &middot; %b %-d")

    html = f"""\
<div style="margin:0;padding:26px 14px;background:{_PAGE};font-family:{_FONT}">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto">
    <tr><td style="background:#fff;border:1px solid {_BORDER};border-radius:16px;overflow:hidden">

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="padding:16px 22px;border-bottom:1px solid {_LINE};vertical-align:middle">
            <span style="display:inline-block;width:32px;height:32px;border-radius:9px;background:{_ACCENT};color:#fff;text-align:center;line-height:32px;font-weight:700;font-size:14px;vertical-align:middle">JF</span>
            <span style="font-size:19px;font-weight:700;color:{_INK};vertical-align:middle;margin-left:10px">Job Finder</span>
          </td>
          <td style="padding:16px 22px;border-bottom:1px solid {_LINE};text-align:right;vertical-align:middle">
            <span style="font-size:13px;color:{_MUTED};background:{_PAGE};padding:6px 11px;border-radius:999px;white-space:nowrap">{date}</span>
          </td>
        </tr>
      </table>

      <div style="padding:20px 22px 4px">
        <span style="font-size:34px;font-weight:800;color:{_ACCENT};vertical-align:middle">{n}</span>
        <span style="font-size:21px;font-weight:600;color:{_INK};vertical-align:middle;margin-left:8px">new {hero_noun} role{s}</span>
        <div style="font-size:15px;color:{_MUTED};margin-top:6px">Entry-level &middot; United States &middot; posted recently</div>
      </div>

      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px">
        {rows}
      </table>

      <div style="padding:16px 22px 20px;border-top:1px solid {_LINE}">
        <div style="font-size:13px;color:{_MUTED};line-height:1.5">Sourced from Greenhouse, Lever, Ashby, SmartRecruiters, Adzuna, and curated new-grad feeds.</div>
        <div style="font-size:13px;color:{_FAINT};margin-top:7px">Checked every 15 minutes.</div>
      </div>

    </td></tr>
  </table>
</div>"""
    _send(f"[Job Finder] {n} new {subject_noun} role{s}", html, to, api_key)


def send_bootstrap(count: int, to: str, subject_noun: str = "entry-level SWE",
                   api_key: str = "") -> None:
    html = f"""\
<div style="margin:0;padding:26px 14px;background:{_PAGE};font-family:{_FONT}">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;margin:0 auto">
    <tr><td style="background:#fff;border:1px solid {_BORDER};border-radius:16px;padding:26px 24px">
      <div>
        <span style="display:inline-block;width:32px;height:32px;border-radius:9px;background:{_ACCENT};color:#fff;text-align:center;line-height:32px;font-weight:700;font-size:14px;vertical-align:middle">JF</span>
        <span style="font-size:19px;font-weight:700;color:{_INK};vertical-align:middle;margin-left:10px">Job Finder is live</span>
      </div>
      <p style="font-size:16px;color:{_INK};line-height:1.55;margin:16px 0 0">
        Tracking <b>{count}</b> current {subject_noun} roles. From now on you'll only be
        emailed about <b>new</b> ones, checked every 15 minutes.
      </p>
    </td></tr>
  </table>
</div>"""
    _send(f"[Job Finder] Tracking {count} roles, setup complete", html, to, api_key)
