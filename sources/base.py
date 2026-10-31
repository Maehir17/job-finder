import concurrent.futures as cf
import hashlib
import re
from dataclasses import dataclass

import requests

_NORM = re.compile(r"[^a-z0-9]")

_UA = "job-finder/1.0 (+https://github.com)"


def http() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": _UA, "Accept": "application/json"})
    return s


def get_json(session: requests.Session, url: str, timeout: int = 30):
    r = session.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch_boards(slugs, fetch_one, workers: int = 16) -> list:
    # Poll many company boards in parallel; fetch_one(slug) returns list[Job]
    # and handles its own errors so one bad board can't sink the batch.
    jobs = []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for result in ex.map(fetch_one, slugs):
            jobs.extend(result)
    return jobs


@dataclass
class Job:
    source: str
    company: str
    title: str
    url: str
    location: str = ""
    category: str = ""
    date_posted: str = ""
    native_id: str = ""
    description: str = ""   # JD text when the source provides it cheaply
    board: str = ""         # ATS board slug, for on-demand JD fetches

    @property
    def uid(self) -> str:
        # Content-based: the same role (same company + title) is one id, no
        # matter the location, source, or posting id. Collapses duplicates and
        # keeps a role from being emailed more than once.
        c = _NORM.sub("", (self.company or "").lower())
        t = _NORM.sub("", (self.title or "").lower())
        return hashlib.sha1(f"{c}|{t}".encode()).hexdigest()[:16]
