from .base import Job, get_json, http

_session = http()

# RemoteOK returns a JSON array whose first element is legal/metadata, not a job.
_URL = "https://remoteok.com/api"


def fetch() -> list[Job]:
    try:
        data = get_json(_session, _URL)
    except Exception:
        return []
    jobs = []
    for j in data:
        if not isinstance(j, dict) or not j.get("id") or not j.get("position"):
            continue
        jobs.append(
            Job(
                source="RemoteOK",
                company=(j.get("company") or "").strip(),
                title=(j.get("position") or "").strip(),
                url=j.get("url") or j.get("apply_url", ""),
                location=(j.get("location") or "").strip() or "Remote",
                # Treat like a raw board: require an entry-level title signal downstream.
                category="ATS",
                date_posted=(j.get("date") or "")[:10],
                native_id=str(j.get("id", "")),
            )
        )
    return jobs
