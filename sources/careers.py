import os
from datetime import datetime, timezone

from .base import Job, http

# Broad career-site sweep via the Apify "fantastic-jobs" index (the same one
# jobsweep uses): reads companies' own ATS boards across 50+ platforms rather
# than our fixed slug list. Pay-per-result and the free tier is limited, so it
# runs only a few times a day (not on every 15-min cron) — see _is_sweep_time.
_TOKEN = os.environ.get("APIFY_TOKEN", "")
_ACTOR = "fantastic-jobs~career-site-job-listing-api"
_URL = f"https://api.apify.com/v2/acts/{_ACTOR}/run-sync-get-dataset-items"

# UTC hours at which to sweep (one per hour; the cron fires every 15 min).
_SWEEP_HOURS = {
    int(h) for h in os.environ.get("APIFY_SWEEP_HOURS", "7,13,19").split(",")
    if h.strip().isdigit()
}
_DEMO = os.environ.get("DEMO", "").lower() in ("1", "true", "yes")

_session = http()

# One track per tracker. Rows are billed, so exclude obvious misses at source
# and keep limits modest; job-finder's own filters do the fine-grained work.
_TRACKS = [
    {
        "limit": 100,
        "timeRange": "24h",
        "descriptionType": "text",
        "removeAgency": True,
        "titleSearch": [
            "software engineer", "software developer", "data engineer",
            "data scientist", "machine learning", "backend", "frontend",
            "full stack", "devops", "site reliability",
        ],
        "titleExclusionSearch": [
            "senior", "staff", "principal", "lead", "manager", "director",
            "vp", "intern", "contract",
        ],
    },
    {
        "limit": 100,
        "timeRange": "24h",
        "descriptionType": "text",
        "removeAgency": True,
        "titleSearch": [
            "product manager", "associate product manager", "program manager",
            "project manager", "strategy", "business operations", "marketing",
            "brand", "communications",
        ],
        # Interns kept here on purpose: the PM tracker wants internships too.
        "titleExclusionSearch": [
            "senior", "staff", "principal", "lead", "director", "vp",
            "sales", "account executive",
        ],
    },
]


def _is_sweep_time() -> bool:
    now = datetime.now(timezone.utc)
    return now.hour in _SWEEP_HOURS and now.minute < 15


def _to_job(row: dict) -> Job:
    locs = row.get("locations_derived") or row.get("locations") or []
    if isinstance(locs, str):
        locs = [locs]
    location = "; ".join(str(x) for x in locs[:3] if x) if isinstance(locs, list) else ""
    return Job(
        source="Careers",
        company=str(row.get("organization") or "").strip(),
        title=str(row.get("title") or "").strip(),
        url=str(row.get("url") or "").strip(),
        location=location,
        category="ATS",
        date_posted=str(row.get("date_posted") or "")[:10],
        native_id=str(row.get("id") or row.get("url") or ""),
        description=str(row.get("description_text") or "")[:4000],
    )


def fetch() -> list[Job]:
    # Dormant without a token; otherwise only at the scheduled sweep times
    # (or on a manual demo run) to respect the pay-per-result budget.
    if not _TOKEN:
        return []
    if not (_is_sweep_time() or _DEMO):
        return []
    headers = {"Authorization": f"Bearer {_TOKEN}", "Accept": "application/json"}
    jobs: list[Job] = []
    for track in _TRACKS:
        try:
            r = _session.post(_URL, json=track, headers=headers, timeout=300)
            r.raise_for_status()
            rows = r.json()
        except Exception:
            continue
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict):
                    jobs.append(_to_job(row))
    return jobs
