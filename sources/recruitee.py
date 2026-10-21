from .base import Job, fetch_boards, get_json, http
from companies import RECRUITEE

_session = http()


def _fetch_one(slug: str) -> list[Job]:
    url = f"https://{slug}.recruitee.com/api/offers/"
    try:
        data = get_json(_session, url)
    except Exception:
        return []
    jobs = []
    for j in data.get("offers", []):
        jobs.append(
            Job(
                source="Recruitee",
                company=slug,
                title=(j.get("title") or "").strip(),
                url=j.get("careers_url", ""),
                location=j.get("location", ""),
                category="ATS",
                date_posted=(j.get("published_at") or "")[:10],
                native_id=str(j.get("id", "")),
            )
        )
    return jobs


def fetch() -> list[Job]:
    return fetch_boards(RECRUITEE, _fetch_one)
