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
