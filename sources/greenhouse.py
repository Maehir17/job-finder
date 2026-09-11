from .base import Job, fetch_boards, get_json, http
from companies import GREENHOUSE

_session = http()


def _fetch_one(slug: str) -> list[Job]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        data = get_json(_session, url)
    except Exception:
        return []
    jobs = []
    for j in data.get("jobs", []):
        loc = (j.get("location") or {}).get("name", "")
        jobs.append(
            Job(
                source="Greenhouse",
                company=j.get("company_name") or slug,
                title=j.get("title", "").strip(),
                url=j.get("absolute_url", ""),
                location=loc,
                category="ATS",
                date_posted=(j.get("first_published") or j.get("updated_at") or "")[:10],
                native_id=str(j.get("id", "")),
            )
        )
    return jobs


def fetch() -> list[Job]:
    return fetch_boards(GREENHOUSE, _fetch_one)
