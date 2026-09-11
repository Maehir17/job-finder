import os

# Sending account credentials come from env / GitHub Actions secrets.
GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# Where alerts are delivered.
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "redacted@example.com")

# When true, gather + filter + print but never send email or write state.
DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")
