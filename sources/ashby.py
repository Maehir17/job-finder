from .base import Job, get_json, http
from companies import ASHBY


def fetch() -> list[Job]:
    session = http()
    jobs: list[Job] = []
    for slug in ASHBY:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{slug}"
        try:
            data = get_json(session, url)
        except Exception as e:
            print(f"  ashby/{slug}: skipped ({e})")
            continue
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
