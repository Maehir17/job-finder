import os

from .base import Job, http

# Broad career-site coverage via the Apify "fantastic-jobs" index (the same one
# jobsweep uses), spanning 50+ ATS platforms. That actor is pay-per-result and
# the free credit is small, so we do NOT trigger new runs here. Instead we read
# the last completed run's cached dataset, which is free. Trigger a fresh paid
# sweep manually when the budget allows (see _run_sweep below), then this picks
# up the new results automatically.
_TOKEN = os.environ.get("APIFY_TOKEN", "")
_ACTOR = "fantastic-jobs~career-site-job-listing-api"
_LAST_ITEMS = f"https://api.apify.com/v2/acts/{_ACTOR}/runs/last/dataset/items"

_session = http()


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
    # Read the last successful sweep's results (cached, no new charge).
    if not _TOKEN:
        return []
    headers = {"Authorization": f"Bearer {_TOKEN}", "Accept": "application/json"}
    try:
        r = _session.get(
            _LAST_ITEMS,
            params={"status": "SUCCEEDED", "clean": "true"},
            headers=headers,
            timeout=60,
        )
        r.raise_for_status()
        rows = r.json()
    except Exception:
        return []
    if not isinstance(rows, list):
        return []
    return [_to_job(row) for row in rows if isinstance(row, dict)]
