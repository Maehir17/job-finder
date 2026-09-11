from .base import Job, fetch_boards, get_json, http
from companies import ASHBY

_session = http()


def _fetch_one(slug: str) -> list[Job]:
    url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
    try:
        data = get_json(_session, url)
    except Exception:
        return []
    jobs = []
    for j in data.get("jobs", []):
        if not j.get("isListed", True):
            continue
        if (j.get("employmentType") or "").lower() in ("intern", "temporary", "contract"):
            continue
        jobs.append(
            Job(
                source="Ashby",
                company=slug,
                title=j.get("title", "").strip(),
                url=j.get("jobUrl") or j.get("applyUrl", ""),
                location=j.get("location", ""),
                category="ATS",
                date_posted=(j.get("publishedAt") or "")[:10],
                native_id=str(j.get("id", "")),
            )
        )
    return jobs


def fetch() -> list[Job]:
    return fetch_boards(ASHBY, _fetch_one)
