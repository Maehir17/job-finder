import sys

import config
import notify
import storage
from filters import is_recent, is_relevant, is_us
from sources import ashby, community, greenhouse, lever

SOURCES = [
    ("community", community.fetch),
    ("greenhouse", greenhouse.fetch),
    ("lever", lever.fetch),
    ("ashby", ashby.fetch),
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

    # Dedupe across sources by uid, then keep only relevant roles.
    seen_uid, relevant = set(), []
    for j in raw:
        if not j.url or j.uid in seen_uid:
            continue
        seen_uid.add(j.uid)
        if not is_relevant(j.title, j.category, from_ats=(j.category == "ATS")):
            continue
        if not is_us(j.location):
            continue
        if not is_recent(j.date_posted, config.MAX_AGE_DAYS):
            continue
        relevant.append(j)

    print(f"relevant after filtering: {len(relevant)}")

    all_uids = {j.uid for j in relevant}
    seen = storage.load_seen()
    new = [j for j in relevant if j.uid not in seen]
    print(f"new since last run: {len(new)}")

    if config.DRY_RUN:
        for j in new[:40]:
            print(f"  + [{j.source}] {j.company}: {j.title} ({j.location})")
        print("DRY_RUN: no email sent, state unchanged")
        return 0

    if storage.is_bootstrap():
        # First run: record everything silently so future roles trigger alerts.
        storage.save_seen(all_uids)
        notify.send_bootstrap(len(all_uids))
        print("bootstrap complete")
        return 0

    if new:
        notify.send_digest(new)
        # Union so a posting that reappears isn't re-alerted.
        storage.save_seen(seen | all_uids)
        print(f"emailed {len(new)} new roles")
    else:
        print("nothing new")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
