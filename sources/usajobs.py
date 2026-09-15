import os

from .base import Job, http

# Official US government jobs API. Free, but requires an API key and the
# registered email in the User-Agent header. Dormant until both are set.
_KEY = os.environ.get("USAJOBS_KEY", "")
_EMAIL = os.environ.get("USAJOBS_EMAIL", "")
_URL = "https://data.usajobs.gov/api/search"
_KEYWORDS = ["software engineer", "software developer", "data engineer"]


def _session():
    s = http()
    s.headers.update({
        "Host": "data.usajobs.gov",
        "User-Agent": _EMAIL,
        "Authorization-Key": _KEY,
    })
    return s


def fetch() -> list[Job]:
    if not _KEY or not _EMAIL:
        return []
    s = _session()
    jobs = []
    for kw in _KEYWORDS:
        try:
            data = s.get(
                _URL,
                params={"Keyword": kw, "ResultsPerPage": 250, "WhoMayApply": "public"},
                timeout=30,
            ).json()
        except Exception:
            continue
        items = (data.get("SearchResult") or {}).get("SearchResultItems") or []
        for it in items:
            d = it.get("MatchedObjectDescriptor") or {}
            locs = [l.get("LocationName", "") for l in (d.get("PositionLocation") or [])]
            jobs.append(
                Job(
                    source="USAJOBS",
                    company=d.get("OrganizationName", ""),
                    title=(d.get("PositionTitle") or "").strip(),
                    url=d.get("PositionURI", ""),
                    location=", ".join(l for l in locs if l),
                    category="ATS",
                    date_posted=(d.get("PublicationStartDate") or "")[:10],
                    native_id=str(d.get("PositionID", "")),
                )
            )
    return jobs
