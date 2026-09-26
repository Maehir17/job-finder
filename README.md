# Job Finder

Finds job postings from many sources, removes duplicates, and emails only the
new ones. Runs on GitHub Actions every 15 minutes.

## Trackers

The pipeline fetches every source once, then runs one or more profiles over the
shared pool. Each profile has its own filters, recipient, and state file, and is
active only when its recipient is set (see `profiles.py`).

| Profile | Roles | Locations | Recipient secret |
|---|---|---|---|
| `swe` | Full-time entry-level software and adjacent | US | `NOTIFY_EMAIL` |
| `pm` | Entry-level product / project / strategy / marketing (full-time, JD-verified new-grad) plus internships at selected companies | New York, SF Bay Area (US) | `NOTIFY_EMAIL_PM` |

## Sources

| Source | Covers | To extend |
|---|---|---|
| Community feeds (`sources/community.py`) | SimplifyJobs + vanshb03 new-grad repos, thousands of entry-level roles across all companies | nothing to do |
| Greenhouse / Lever / Ashby (`sources/*.py`) | Specific companies' job boards | add slugs in `companies.py` |

The community feeds cover the broad set. The ATS pollers add named companies and
are filtered for entry-level titles, since those boards list every role.

## How "only new roles" works

Each profile keeps its own seen-ids file (`state/seen.txt`, `state/seen_pm.txt`)
committed back to the repo after each run. New ids get emailed. A profile's first
run records all current postings without emailing them and sends a one-time setup
summary, so you don't get thousands of existing jobs at once.

## Setup

1. Push this folder to a new GitHub repo.
2. Sign up at resend.com using the address you want alerts sent to, and create
   an API key with sending access. With no verified domain, Resend sends from
   `onboarding@resend.dev` to that same signup address.
3. In the repo, go to Settings > Secrets and variables > Actions and add:
   - `RESEND_API_KEY`: the key from Resend (starts with `re_`)
   - `NOTIFY_EMAIL`: recipient for the software tracker
   - `NOTIFY_EMAIL_PM`: recipient for the product/strategy tracker (optional; the
     tracker stays off until this is set)
   - optional variable `SENDER` if you verify your own domain in Resend
4. In the Actions tab, run job-finder once to bootstrap.

## Local testing

```bash
pip install -r requirements.txt
DRY_RUN=1 python main.py
```

This fetches, filters, and prints results without sending email or writing state.

## Tuning

- Which software roles match: edit the regexes in `filters.py`.
- Which product/strategy/marketing roles match, the metros, and the internship
  company list: edit `pm_filters.py`.
- Which companies' boards are polled: add or remove slugs in `companies.py`.
- Add or change a tracker: edit `profiles.py`.
- Frequency: change the `cron` in `.github/workflows/job-finder.yml`.
