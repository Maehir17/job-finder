import sys
from datetime import datetime, timezone

import config
import notify
import storage
from filters import age_days
from profiles import active_profiles
from sources import (
    adzuna,
    ashby,
    breezy,
    careers,
    community,
    greenhouse,
    lever,
    recruitee,
    remoteok,
    remotive,
    smartrecruiters,
    themuse,
    usajobs,
    weworkremotely,
    workable,
    workday,
)

SOURCES = [
    ("community", community.fetch),
    ("greenhouse", greenhouse.fetch),
    ("lever", lever.fetch),
    ("ashby", ashby.fetch),
    ("smartrecruiters", smartrecruiters.fetch),
    ("workday", workday.fetch),
    ("workable", workable.fetch),
    ("recruitee", recruitee.fetch),
    ("breezy", breezy.fetch),
    ("careers", careers.fetch),
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


def _score(p, j) -> int:
    s = 100 if p.is_top(j.company) else 0
    a = age_days(j.date_posted)
    if a is not None:
        s += max(0, 14 - a)
    return s


def _collapse(jobs):
    # Group copies of the same role (company + title) into one, merging their
    # locations, so a role posted in several cities shows up once.
    groups, order = {}, []
    for j in jobs:
        k = j.collapse_key
        if k not in groups:
            groups[k] = j
            order.append(k)
            j._locs = [j.location] if j.location else []
        elif j.location and j.location not in groups[k]._locs and len(groups[k]._locs) < 5:
            groups[k]._locs.append(j.location)
    reps = []
    for k in order:
        rep = groups[k]
        locs = [l for l in rep._locs if l]
        if len(locs) > 1:
            rep.location = "; ".join(locs[:3]) + (f" +{len(locs) - 3} more" if len(locs) > 3 else "")
        reps.append(rep)
    return reps


def _prepare_digest(p, jobs):
    # Collapse duplicates, tag top companies, and rank best-first.
    jobs = _collapse(jobs)
    for j in jobs:
        j.top = p.is_top(j.company)
    jobs.sort(key=lambda j: _score(p, j), reverse=True)
    return jobs


def _run_profile(p, deduped) -> None:
    relevant = [j for j in deduped if p.matches(j)]
    # Optional second pass (e.g. reading JDs to confirm new-grad intent).
    before = len(relevant)
    relevant = p.verify(relevant)
    if len(relevant) != before:
        print(f"[{p.key}] JD check dropped {before - len(relevant)}")
    print(f"[{p.key}] relevant after filtering: {len(relevant)}")

    all_uids = {j.uid for j in relevant}
    seen = storage.load_seen(p.key)
    new = [j for j in relevant if j.uid not in seen]
    print(f"[{p.key}] new since last run: {len(new)}")
    from collections import Counter
    print(f"[{p.key}] relevant by source: {dict(Counter(j.source for j in relevant))}")
    print(f"[{p.key}] new by source: {dict(Counter(j.source for j in new))}")

    if config.DRY_RUN:
        for j in new[:40]:
            print(f"  + [{j.source}] {j.company}: {j.title} ({j.location})")
        print(f"[{p.key}] DRY_RUN: no email sent, state unchanged")
        return

    today = datetime.now(timezone.utc).date().isoformat()

    if config.DEMO:
        # Sample digest to preview the format; leaves state untouched.
        sample = sorted(relevant, key=lambda j: j.date_posted or "", reverse=True)[:30]
        sample = _prepare_digest(p, p.email_filter(sample))[:12]
        _resolve_links(sample)
        notify.send_digest(sample, p.to_email, p.hero_noun, p.subject_noun, p.resend_key)
        print(f"[{p.key}] DEMO: emailed {len(sample)} sample roles, state unchanged")
        return

    if storage.is_bootstrap(p.key):
        # First run: record everything silently so future roles trigger alerts.
        storage.save_seen({u: today for u in all_uids}, p.key, config.SEEN_TTL_DAYS)
        notify.send_bootstrap(len(all_uids), p.to_email, p.subject_noun, p.resend_key)
        print(f"[{p.key}] bootstrap complete")
        return

    if not new:
        # Still refresh timestamps of open roles so they don't expire early.
        for j in relevant:
            if j.uid in seen:
                seen[j.uid] = today
        storage.save_seen(seen, p.key, config.SEEN_TTL_DAYS)
        print(f"[{p.key}] nothing new")
        return

    # Fresh roles (posted today/yesterday) go out immediately; anything older
    # is batched and only sent on the hourly flush, so you don't get a trickle
    # of tiny emails for non-urgent roles.
    fresh = [j for j in new if (age_days(j.date_posted) or 99) <= 1]
    older = [j for j in new if (age_days(j.date_posted) or 99) > 1]
    flush = datetime.now(timezone.utc).minute < 15  # once per hour

    batch = p.email_filter(fresh + (older if flush else []))
    to_send = _prepare_digest(p, batch)
    _resolve_links(to_send)
    if to_send:
        notify.send_digest(to_send, p.to_email, p.hero_noun, p.subject_noun, p.resend_key)

    # Refresh open roles already in memory; add the ones we handled this run.
    # Fresh is handled now; older only once flushed, so unflushed older roles
    # stay unseen and roll into the next hourly batch.
    for j in relevant:
        if j.uid in seen:
            seen[j.uid] = today
    for j in fresh:
        seen[j.uid] = today
    if flush:
        for j in older:
            seen[j.uid] = today
    storage.save_seen(seen, p.key, config.SEEN_TTL_DAYS)
    print(f"[{p.key}] sent {len(to_send)} (fresh {len(fresh)}, older {len(older)}, flush={flush})")


if __name__ == "__main__":
    raise SystemExit(main())
