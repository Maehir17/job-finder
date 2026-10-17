from datetime import datetime, timezone

from .base import Job, get_json, http

# Curated new-grad aggregators, already scoped to early-career roles.
FEEDS = [
    ("Simplify", "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/.github/scripts/listings.json"),
    ("vanshb03", "https://raw.githubusercontent.com/vanshb03/New-Grad-2026/dev/.github/scripts/listings.json"),
    ("Keugene11", "https://raw.githubusercontent.com/Keugene11/New-Grad-Tech-Jobs/main/.github/scripts/listings.json"),
]

# Some feeds tag categories with short codes; map them to the strings the SWE
# filter recognizes (ALLOWED_CATEGORIES). Unknown values pass through unchanged.
_CAT = {
    "swe": "Software Engineering",
    "software": "Software Engineering",
    "data": "AI/ML/Data",
    "ml": "AI/ML/Data",
    "ai": "AI/ML/Data",
    "quant": "Quant",
}


def _iso(ts) -> str:
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).date().isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def fetch() -> list[Job]:
    session = http()
    jobs: list[Job] = []
    for source, url in FEEDS:
        data = get_json(session, url)
        for j in data:
            if not j.get("active", True) or not j.get("is_visible", True):
                continue
            locs = j.get("locations") or []
            cat = (j.get("category") or "").strip()
            jobs.append(
                Job(
                    source=source,
                    company=j.get("company_name", "").strip(),
                    title=j.get("title", "").strip(),
                    url=j.get("url", "").strip(),
                    location=", ".join(locs) if isinstance(locs, list) else str(locs),
                    category=_CAT.get(cat.lower(), cat),
                    date_posted=_iso(j.get("date_posted")),
                    native_id=str(j.get("id", "")),
                )
            )
    return jobs
