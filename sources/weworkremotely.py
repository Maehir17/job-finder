import re
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from .base import Job, http

_session = http()

# RSS feeds for the software-adjacent categories.
_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-front-end-programming-jobs.rss",
]


def _fetch_feed(url: str) -> list[Job]:
    try:
        r = _session.get(url, timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception:
        return []
    jobs = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        region = (item.findtext("region") or "").strip()
        try:
            date_posted = parsedate_to_datetime(item.findtext("pubDate")).date().isoformat()
        except (TypeError, ValueError):
            date_posted = ""
        # Titles come as "Company: Position"; split off the company prefix.
        company, _, position = title.partition(":")
        position = position.strip() or title
        # Derive a stable id from the listing URL.
        m = re.search(r"/listings/([^/?#]+)", link)
        native_id = m.group(1) if m else link
        jobs.append(
            Job(
                source="WeWorkRemotely",
                company=company.strip(),
                title=position,
                url=link,
                location=region or "Remote",
                category="ATS",
                date_posted=date_posted,
                native_id=native_id,
            )
        )
    return jobs


def fetch() -> list[Job]:
    jobs = []
    for url in _FEEDS:
        jobs.extend(_fetch_feed(url))
    return jobs
