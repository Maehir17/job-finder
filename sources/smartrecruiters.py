from urllib.parse import quote

from filters import is_software_title

from .base import Job, fetch_boards, get_json, http
from companies import SMARTRECRUITERS

_session = http()

# Server-side keyword filters keep us from pulling entire (sometimes huge)
# boards, while covering the software and product/strategy/marketing trackers.
_QUERIES = ["software", "product manager", "program manager", "strategy", "marketing"]
_LIMIT = 100

# SmartRecruiters tags each posting with an experience level; trust it to admit
# early-career roles even when the title lacks an explicit entry-level word.
_ENTRY_LEVELS = {"entry_level", "associate", "student_entry_level"}
_SKIP_EMPLOYMENT = {"intern", "internship", "temporary", "contractor", "contract"}


def _to_job(j: dict, slug: str) -> Job | None:
    emp = (j.get("typeOfEmployment") or {}).get("id", "").lower()
    if emp in _SKIP_EMPLOYMENT:
        return None
    loc = j.get("location") or {}
    # Skip non-US early to cut noise; is_us also guards downstream.
    if (loc.get("country") or "").lower() not in ("us", "usa", ""):
        return None
    company = (j.get("company") or {}).get("identifier", slug)
    level = (j.get("experienceLevel") or {}).get("id", "").lower()
    title = (j.get("name") or "").strip()
    # Only trust the entry-level tag to skip the SWE title-entry gate when the
    # title is genuinely software; otherwise "ATS" keeps non-software "engineer"
    # roles (surfaced by the broader queries) out of the software tracker.
    is_entry_sw = level in _ENTRY_LEVELS and is_software_title(title)
    return Job(
        source="SmartRecruiters",
        company=(j.get("company") or {}).get("name", slug),
        title=title,
        url=f"https://jobs.smartrecruiters.com/{company}/{j.get('id','')}",
        location=loc.get("fullLocation") or ", ".join(
            x for x in (loc.get("city"), loc.get("region")) if x
        ),
        category="Software" if is_entry_sw else "ATS",
        date_posted=(j.get("releasedDate") or "")[:10],
        native_id=str(j.get("id", "")),
    )


def _fetch_one(slug: str) -> list[Job]:
    by_id: dict[str, Job] = {}
    for q in _QUERIES:
        url = (
            f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
            f"?q={quote(q)}&limit={_LIMIT}"
        )
        try:
            data = get_json(_session, url)
        except Exception:
            continue
        for j in data.get("content", []):
            job = _to_job(j, slug)
            if job:
                by_id[job.native_id] = job
    return list(by_id.values())


def fetch() -> list[Job]:
    return fetch_boards(SMARTRECRUITERS, _fetch_one)
