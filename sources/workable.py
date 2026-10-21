from .base import Job, fetch_boards, http
from companies import WORKABLE

_session = http()


def _fetch_one(slug: str) -> list[Job]:
    url = f"https://apply.workable.com/api/v3/accounts/{slug}/jobs"
    try:
        r = _session.post(url, json={}, timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []
    jobs = []
    for j in data.get("results", []):
        loc = j.get("location") or {}
        where = ", ".join(x for x in (loc.get("city"), loc.get("region")) if x) or loc.get("country", "")
        code = j.get("shortcode", "")
        jobs.append(
            Job(
                source="Workable",
                company=slug,
                title=(j.get("title") or "").strip(),
                url=f"https://apply.workable.com/{slug}/j/{code}/" if code else "",
                location=where,
                category="ATS",
                date_posted=(j.get("published") or "")[:10],
                native_id=code or str(j.get("id", "")),
            )
        )
    return jobs


def fetch() -> list[Job]:
    return fetch_boards(WORKABLE, _fetch_one)
