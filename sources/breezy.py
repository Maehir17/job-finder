from .base import Job, fetch_boards, get_json, http
from companies import BREEZY

_session = http()


def _loc(loc) -> str:
    if not isinstance(loc, dict):
        return ""
    city = loc.get("city") or ""
    state = (loc.get("state") or {}).get("id") or ""
    country = (loc.get("country") or {}).get("name") or ""
    return ", ".join(x for x in (city, state or country) if x)


def _fetch_one(slug: str) -> list[Job]:
    url = f"https://{slug}.breezy.hr/json"
    try:
        data = get_json(_session, url)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    jobs = []
    for j in data:
        jobs.append(
            Job(
                source="Breezy",
                company=slug,
                title=(j.get("name") or "").strip(),
                url=j.get("url", ""),
                location=_loc(j.get("location")),
                category="ATS",
                date_posted=(j.get("published_date") or "")[:10],
                native_id=str(j.get("id") or j.get("friendly_id") or ""),
            )
        )
    return jobs


def fetch() -> list[Job]:
    return fetch_boards(BREEZY, _fetch_one)
