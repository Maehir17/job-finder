import concurrent.futures as cf
import hashlib
import re
from dataclasses import dataclass

import requests

_NORM = re.compile(r"[^a-z0-9]")

# Extract a stable job id from an ATS URL, so the same posting collapses across
# boards, sources and wrapper links. Falls back to the source's own id.
_ATS_ID = [
    ("gh", re.compile(r"greenhouse\.io/[^?#]*?/jobs/(\d+)")),
    ("gh", re.compile(r"[?&]gh_jid=(\d+)")),
    ("lv", re.compile(r"lever\.co/[^/]+/([0-9a-fA-F-]{20,})")),
    ("ash", re.compile(r"ashbyhq\.com/[^/]+/([0-9a-fA-F-]{20,})")),
    ("sr", re.compile(r"smartrecruiters\.com/[^/]+/(\d{6,})")),
    ("wk", re.compile(r"workable\.com/[^/]+/j/([A-Za-z0-9]+)")),
    ("wd", re.compile(r"myworkdayjobs\.com/.*_([A-Za-z]{0,3}-?\d{4,})(?:[/?#]|$)")),
]


def ats_id(url: str) -> str:
    u = url or ""
    for tag, rx in _ATS_ID:
        m = rx.search(u)
        if m:
            return f"{tag}:{m.group(1).lower()}"
    return ""

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

    top: bool = False       # set at send time: role is from a top company

    @property
    def uid(self) -> str:
        # Per-posting id: the ATS job id from the URL (same posting across
        # boards/wrappers is one id), else the source's own id, else content.
        aid = ats_id(self.url)
        if aid:
            return aid
        if self.native_id:
            return f"{self.source}:{self.native_id}"
        return "c:" + self.collapse_key

    @property
    def collapse_key(self) -> str:
        # Groups copies of the same role (company + title) within one digest.
        c = _NORM.sub("", (self.company or "").lower())
        t = _NORM.sub("", (self.title or "").lower())
        return hashlib.sha1(f"{c}|{t}".encode()).hexdigest()[:16]
