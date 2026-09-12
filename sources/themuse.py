import os

from .base import Job, get_json, http

_session = http()

# The Muse supports server-side level and category filters, so we can ask
# directly for entry-level software roles. Category maps to our own tag so the
# downstream filter does not also demand an entry-level word in the title.
_BASE = "https://www.themuse.com/api/public/jobs"
_CATEGORIES = ["Software Engineering", "Data Science", "Data and Analytics"]
_MAX_PAGES = 6
_API_KEY = os.environ.get("THEMUSE_API_KEY", "")


def _fetch_category(category: str) -> list[Job]:
    jobs = []
    for page in range(1, _MAX_PAGES + 1):
        url = (
            f"{_BASE}?category={category.replace(' ', '%20')}"
            f"&level=Entry%20Level&page={page}"
        )
        if _API_KEY:
            url += f"&api_key={_API_KEY}"
        try:
            data = get_json(_session, url)
        except Exception:
            break
        results = data.get("results") or []
        if not results:
            break
        for j in results:
            locs = [l.get("name", "") for l in (j.get("locations") or [])]
            jobs.append(
                Job(
                    source="TheMuse",
                    company=(j.get("company") or {}).get("name", ""),
                    title=(j.get("name") or "").strip(),
                    url=(j.get("refs") or {}).get("landing_page", ""),
                    location=", ".join(l for l in locs if l),
                    category="Software",
                    date_posted=(j.get("publication_date") or "")[:10],
                    native_id=str(j.get("id", "")),
                )
            )
        if page >= (data.get("page_count") or page):
            break
    return jobs


def fetch() -> list[Job]:
    jobs = []
    for category in _CATEGORIES:
        jobs.extend(_fetch_category(category))
    return jobs
