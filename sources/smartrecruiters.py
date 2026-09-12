from .base import Job, fetch_boards, get_json, http
from companies import SMARTRECRUITERS

_session = http()

# Server-side keyword filter keeps us from pulling entire (sometimes huge) boards.
_QUERY = "software"
_LIMIT = 100

# SmartRecruiters tags each posting with an experience level; trust it to admit
# early-career roles even when the title lacks an explicit entry-level word.
_ENTRY_LEVELS = {"entry_level", "associate", "student_entry_level"}
_SKIP_EMPLOYMENT = {"intern", "internship", "temporary", "contractor", "contract"}


def _fetch_one(slug: str) -> list[Job]:
    url = (
        f"https://api.smartrecruiters.com/v1/companies/{slug}/postings"
        f"?q={_QUERY}&limit={_LIMIT}"
    )
    try:
        data = get_json(_session, url)
    except Exception:
        return []
    jobs = []
    for j in data.get("content", []):
        emp = (j.get("typeOfEmployment") or {}).get("id", "").lower()
        if emp in _SKIP_EMPLOYMENT:
            continue
        loc = j.get("location") or {}
        # Skip non-US early to cut noise; is_us also guards downstream.
        if (loc.get("country") or "").lower() not in ("us", "usa", ""):
            continue
        company = (j.get("company") or {}).get("identifier", slug)
        level = (j.get("experienceLevel") or {}).get("id", "").lower()
        jobs.append(
            Job(
                source="SmartRecruiters",
                company=(j.get("company") or {}).get("name", slug),
                title=(j.get("name") or "").strip(),
                url=f"https://jobs.smartrecruiters.com/{company}/{j.get('id','')}",
                location=loc.get("fullLocation") or ", ".join(
                    x for x in (loc.get("city"), loc.get("region")) if x
                ),
                # Trust SmartRecruiters' own level tag for entry roles; otherwise
                # fall back to ATS rules (title must signal entry-level).
                category="Software" if level in _ENTRY_LEVELS else "ATS",
                date_posted=(j.get("releasedDate") or "")[:10],
                native_id=str(j.get("id", "")),
            )
        )
    return jobs


def fetch() -> list[Job]:
    return fetch_boards(SMARTRECRUITERS, _fetch_one)
