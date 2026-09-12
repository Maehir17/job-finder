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

# Drop postings older than this many days.
MAX_AGE_DAYS = int(os.environ.get("MAX_AGE_DAYS", "30"))
