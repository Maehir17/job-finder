import re
from datetime import datetime, timedelta, timezone

from .base import Job, fetch_boards, http
from companies import WORKDAY

_session = http()


def _wd_date(posted_on: str) -> str:
    # Workday's list endpoint has no date field; postedOn is prose like
    # "Posted Today" / "Posted 30+ Days Ago". Translate what we can.
    t = str(posted_on or "").lower()
    if not t:
        return ""
    today = datetime.now(timezone.utc).date()
    if "today" in t:
        return today.isoformat()
    if "yesterday" in t:
        return (today - timedelta(days=1)).isoformat()
    m = re.search(r"(\d+)\s*\+?\s*day", t)
    if m:
        return (today - timedelta(days=int(m.group(1)))).isoformat()
    m = re.search(r"(\d+)\s*\+?\s*month", t)
    if m:
        return (today - timedelta(days=30 * int(m.group(1)))).isoformat()
    return ""


def _fetch_one(entry) -> list[Job]:
    tenant, pod, site = entry
    base = f"https://{tenant}.{pod}.myworkdayjobs.com"
    url = f"{base}/wday/cxs/{tenant}/{site}/jobs"
    try:
        r = _session.post(url, json={"limit": 20, "offset": 0, "appliedFacets": {}}, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []
    jobs = []
    for j in data.get("jobPostings", []):
        path = j.get("externalPath") or ""
        jobs.append(
            Job(
                source="Workday",
                company=tenant,
                title=(j.get("title") or "").strip(),
                url=f"{base}/{site}{path}" if path else base,
                location=j.get("locationsText", ""),
                category="ATS",
                date_posted=_wd_date(j.get("postedOn", "")),
                native_id=path,
            )
        )
    return jobs


def fetch() -> list[Job]:
    return fetch_boards(WORKDAY, _fetch_one, workers=24)
