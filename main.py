import sys

import config
import notify
import storage
from profiles import active_profiles
from sources import (
    adzuna,
    ashby,
    community,
    greenhouse,
    lever,
    remoteok,
    remotive,
    smartrecruiters,
    themuse,
    usajobs,
    weworkremotely,
)

SOURCES = [
    ("community", community.fetch),
    ("greenhouse", greenhouse.fetch),
    ("lever", lever.fetch),
    ("ashby", ashby.fetch),
    ("smartrecruiters", smartrecruiters.fetch),
    ("remoteok", remoteok.fetch),
    ("remotive", remotive.fetch),
    ("themuse", themuse.fetch),
    ("weworkremotely", weworkremotely.fetch),
    ("usajobs", usajobs.fetch),
    ("adzuna", adzuna.fetch),
]


def gather():
    jobs = []
    for name, fetch in SOURCES:
        try:
            found = fetch()
            print(f"[{name}] fetched {len(found)}")
            jobs.extend(found)
        except Exception as e:
            print(f"[{name}] FAILED: {e}", file=sys.stderr)
    return jobs


def main() -> int:
    raw = gather()

    # Dedupe across sources by uid once; each profile filters this shared pool.
    seen_uid, deduped = set(), []
    for j in raw:
        if not j.url or j.uid in seen_uid:
            continue
        seen_uid.add(j.uid)
        deduped.append(j)

    for p in active_profiles():
        _run_profile(p, deduped)
    return 0


def _resolve_links(jobs) -> None:
    # Replace Adzuna redirector links with the real posting URL, for the small
    # set of jobs actually being emailed.
    for j in jobs:
        if j.source == "Adzuna":
            j.url = adzuna.resolve_url(j.url)


def _run_profile(p, deduped) -> None:
    relevant = [j for j in deduped if p.matches(j)]
    print(f"[{p.key}] relevant after filtering: {len(relevant)}")

    all_uids = {j.uid for j in relevant}
    seen = storage.load_seen(p.key)
    new = [j for j in relevant if j.uid not in seen]
    print(f"[{p.key}] new since last run: {len(new)}")

    if config.DRY_RUN:
        for j in new[:40]:
            print(f"  + [{j.source}] {j.company}: {j.title} ({j.location})")
        print(f"[{p.key}] DRY_RUN: no email sent, state unchanged")
        return

    if config.DEMO:
        # Sample digest to preview the format; leaves state untouched.
        sample = sorted(relevant, key=lambda j: j.date_posted or "", reverse=True)[:12]
        _resolve_links(sample)
        notify.send_digest(sample, p.to_email, p.hero_noun, p.subject_noun, p.resend_key)
        print(f"[{p.key}] DEMO: emailed {len(sample)} sample roles, state unchanged")
        return

    if storage.is_bootstrap(p.key):
        # First run: record everything silently so future roles trigger alerts.
        storage.save_seen(all_uids, p.key)
        notify.send_bootstrap(len(all_uids), p.to_email, p.subject_noun, p.resend_key)
        print(f"[{p.key}] bootstrap complete")
        return

    if new:
        _resolve_links(new)
        notify.send_digest(new, p.to_email, p.hero_noun, p.subject_noun, p.resend_key)
        # Union so a posting that reappears isn't re-alerted.
        storage.save_seen(seen | all_uids, p.key)
        print(f"[{p.key}] emailed {len(new)} new roles")
    else:
        print(f"[{p.key}] nothing new")


if __name__ == "__main__":
    raise SystemExit(main())
