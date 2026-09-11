from datetime import datetime, timezone

from .base import Job, get_json, http
from companies import LEVER


def _iso(ms) -> str:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=timezone.utc).date().isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def fetch() -> list[Job]:
    session = http()
    jobs: list[Job] = []
    for slug in LEVER:
        url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
        try:
            data = get_json(session, url)
        except Exception as e:
            print(f"  lever/{slug}: skipped ({e})")
            continue
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
                )
            )
    return jobs
