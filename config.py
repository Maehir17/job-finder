import os

# Resend API key (send-only), from env / GitHub Actions secrets.
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

# Resend's shared sender works without a verified domain, but only delivers to
# the account's own signup email. Override with a verified domain to send freely.
SENDER = os.environ.get("SENDER", "Job Finder <onboarding@resend.dev>")

# Where alerts are delivered (set via env / GitHub Actions secret).
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")

# When true, gather + filter + print but never send email or write state.
DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")

# When true, email a sample digest of the newest roles without changing state.
DEMO = os.environ.get("DEMO", "").lower() in ("1", "true", "yes")

# Drop postings older than this many days.
MAX_AGE_DAYS = int(os.environ.get("MAX_AGE_DAYS", "30"))

# Optional source API keys. Each source stays dormant until its keys are set.
USAJOBS_KEY = os.environ.get("USAJOBS_KEY", "")
USAJOBS_EMAIL = os.environ.get("USAJOBS_EMAIL", "")
ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")
THEMUSE_API_KEY = os.environ.get("THEMUSE_API_KEY", "")
