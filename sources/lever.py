from datetime import datetime, timezone

from .base import Job, fetch_boards, get_json, http
from companies import LEVER

_session = http()


def _iso(ms) -> str:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).date().isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def _fetch_one(slug: str) -> list[Job]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        data = get_json(_session, url)
    except Exception:
        return []
    jobs = []
    for j in data:
        cats = j.get("categories") or {}
        jobs.append(
            Job(
                source="Lever",
                company=slug,
                title=j.get("text", "").strip(),
                url=j.get("hostedUrl", ""),
                location=cats.get("location", ""),
                category="ATS",
                date_posted=_iso(j.get("createdAt")),
                native_id=str(j.get("id", "")),
                description=j.get("descriptionPlain") or j.get("description", ""),
                board=slug,
            )
        )
    return jobs


def fetch() -> list[Job]:
    return fetch_boards(LEVER, _fetch_one)
