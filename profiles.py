from dataclasses import dataclass
from typing import Callable

import config
import jd
from filters import is_recent, is_relevant, is_us
from pm_filters import is_pm_relevant
from sources.base import Job


def _identity(jobs: list[Job]) -> list[Job]:
    return jobs


@dataclass
class Profile:
    key: str                       # identifier; also the state file suffix
    to_email: str                  # recipient address
    hero_noun: str                 # e.g. "software" -> "N new software roles"
    subject_noun: str              # e.g. "entry-level SWE"
    matches: Callable[[Job], bool]
    resend_key: str                # Resend API key this profile sends with
    # Second pass over the matched roles (e.g. JD checks that need the network).
    verify: Callable[[list[Job]], list[Job]] = _identity


def _swe_match(j: Job) -> bool:
    return (
        is_relevant(j.title, j.category, from_ats=(j.category == "ATS"))
        and is_us(j.location)
        and is_recent(j.date_posted, config.MAX_AGE_DAYS)
    )


def _pm_match(j: Job) -> bool:
    return is_pm_relevant(j, config.MAX_AGE_DAYS)


def active_profiles() -> list[Profile]:
    # A profile is active only when it has a recipient configured, so the PM
    # tracker stays dormant until NOTIFY_EMAIL_PM is set.
    profiles = []
    if config.NOTIFY_EMAIL:
        profiles.append(Profile("swe", config.NOTIFY_EMAIL, "software", "entry-level SWE",
                                _swe_match, config.RESEND_API_KEY))
    if config.NOTIFY_EMAIL_PM:
        profiles.append(Profile("pm", config.NOTIFY_EMAIL_PM, "product, strategy & marketing",
                                "product / strategy / marketing", _pm_match,
                                config.RESEND_API_KEY_PM or config.RESEND_API_KEY,
                                verify=jd.keep_new_grad))
    return profiles
