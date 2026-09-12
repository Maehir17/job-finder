from .base import Job, get_json, http

_session = http()

# Software-only category endpoint; still list every level, so filter downstream.
_URL = "https://remotive.com/api/remote-jobs?category=software-dev"


def fetch() -> list[Job]:
    try:
        data = get_json(_session, _URL)
    except Exception:
        return []
    jobs = []
    for j in data.get("jobs", []):
        if (j.get("job_type") or "").lower() not in ("", "full_time"):
            continue
        jobs.append(
            Job(
                source="Remotive",
                company=(j.get("company_name") or "").strip(),
                title=(j.get("title") or "").strip(),
                url=(j.get("url") or "").strip(),
                location=(j.get("candidate_required_location") or "").strip() or "Remote",
                category="ATS",
                date_posted=(j.get("publication_date") or "")[:10],
                native_id=str(j.get("id", "")),
            )
        )
    return jobs
