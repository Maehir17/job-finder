from .base import Job, get_json, http
from companies import GREENHOUSE


def fetch() -> list[Job]:
    session = http()
    jobs: list[Job] = []
    for slug in GREENHOUSE:
        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
        try:
            data = get_json(session, url)
        except Exception as e:
            print(f"  greenhouse/{slug}: skipped ({e})")
            continue
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
                    date_posted=(j.get("updated_at") or "")[:10],
                    native_id=str(j.get("id", "")),
                )
            )
    return jobs
