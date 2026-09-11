# Job Finder

Finds full-time, entry-level software (and adjacent) job postings from many
sources, removes duplicates, and emails you only the new ones. Runs on GitHub
Actions every 4 hours.

## Sources

| Source | Covers | To extend |
|---|---|---|
| Community feeds (`sources/community.py`) | SimplifyJobs + vanshb03 new-grad repos, thousands of entry-level roles across all companies | nothing to do |
| Greenhouse / Lever / Ashby (`sources/*.py`) | Specific companies' job boards | add slugs in `companies.py` |

The community feeds cover the broad set. The ATS pollers add named companies and
are filtered for entry-level titles, since those boards list every role.

## How "only new roles" works

`state/seen.txt` holds every posting id seen so far and is committed back to the
repo after each run. New ids get emailed. The first run records all current
postings without emailing them and sends a one-time setup summary, so you don't
get thousands of existing jobs at once.

## Setup

1. Push this folder to a new GitHub repo.
2. Sign up at resend.com using the address you want alerts sent to, and create
   an API key with sending access. With no verified domain, Resend sends from
   `onboarding@resend.dev` to that same signup address.
3. In the repo, go to Settings > Secrets and variables > Actions and add:
   - `RESEND_API_KEY`: the key from Resend (starts with `re_`)
   - optional variable `NOTIFY_EMAIL` to change the recipient from the default
     `redacted@example.com`
   - optional variable `SENDER` if you verify your own domain in Resend
4. In the Actions tab, run job-finder once to bootstrap.

## Local testing

```bash
pip install -r requirements.txt
DRY_RUN=1 python main.py
```

This fetches, filters, and prints results without sending email or writing state.

## Tuning

- Which roles match: edit the regexes in `filters.py` (`_ENTRY`, `_SENIOR`,
  `_SOFTWARE`, `_NON_SOFTWARE`) and `ALLOWED_CATEGORIES`.
- Which companies: add or remove slugs in `companies.py`.
- Frequency: change the `cron` in `.github/workflows/job-finder.yml`.
