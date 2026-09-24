import os

from .base import Job, http

# Adzuna aggregates listings from many boards. Free tier needs an app id + key.
# Dormant until both are set. country=us keeps results US-based.
_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")
_BASE = "https://api.adzuna.com/v1/api/jobs/us/search"
_QUERIES = [
    "software engineer", "software developer", "data engineer",
    "product manager", "program manager", "strategy", "marketing",
]
_MAX_PAGES = 5
_session = http()


def _fetch_query(what: str) -> list[Job]:
    jobs = []
    for page in range(1, _MAX_PAGES + 1):
        try:
            data = _session.get(
                f"{_BASE}/{page}",
                params={
                    "app_id": _APP_ID,
                    "app_key": _APP_KEY,
                    "what": what,
                    "max_days_old": 30,
                    "results_per_page": 50,
                    "content-type": "application/json",
                },
                timeout=30,
            ).json()
        except Exception:
            break
        results = data.get("results") or []
        if not results:
            break
        for j in results:
            jobs.append(
                Job(
                    source="Adzuna",
                    company=(j.get("company") or {}).get("display_name", ""),
                    title=(j.get("title") or "").strip(),
                    url=j.get("redirect_url", ""),
                    location=(j.get("location") or {}).get("display_name", ""),
                    category="ATS",
                    date_posted=(j.get("created") or "")[:10],
                    native_id=str(j.get("id", "")),
                )
            )
    return jobs


def fetch() -> list[Job]:
    if not _APP_ID or not _APP_KEY:
        return []
    jobs = []
    for q in _QUERIES:
        jobs.extend(_fetch_query(q))
    return jobs


def resolve_url(url: str) -> str:
    # Adzuna links go through their redirector; follow it to the real posting.
    # Best-effort: keep the original URL if resolution fails.
    if "adzuna" not in url:
        return url
    try:
        r = _session.head(url, allow_redirects=True, timeout=15)
        final = r.url
        if "adzuna" in final:  # HEAD sometimes not followed; try GET
            r = _session.get(url, allow_redirects=True, timeout=15, stream=True)
            final = r.url
            r.close()
        return final or url
    except Exception:
        return url
