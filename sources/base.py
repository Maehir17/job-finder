import concurrent.futures as cf
import hashlib
from dataclasses import dataclass

import requests

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

    @property
    def uid(self) -> str:
        # Prefer the source's own id; otherwise hash the URL.
        key = self.native_id or self.url or f"{self.company}|{self.title}"
        return f"{self.source}:{hashlib.sha1(key.encode()).hexdigest()[:16]}"
