import re

from filters import is_recent, is_us

# Product / project / program management, strategy, and marketing titles.
_PM_TITLE = re.compile(
    r"\b(product manager|product management|associate product manager|\bapm\b|"
    r"product owner|program manager|program management|project manager|"
    r"project management|technical program manager|\btpm\b|chief of staff|"
    r"business operations|biz ops|business operations? (associate|analyst)|"
    r"strateg(y|ic)|corporate development|management consult(ant|ing)|"
    r"strategy (and|&) operations|"
    # marketing family
    r"marketing|brand|growth|communications|public relations|\bpr\b|"
    r"social media|content|demand generation|\bseo\b|market research)\b",
    re.I,
)

# Adjacent-but-not-wanted roles that can share a keyword (e.g. "manager").
_PM_EXCLUDE = re.compile(
    r"\b(sales|account executive|account manager|engineer|engineering|"
    r"software|developer|customer success|customer support|"
    r"recruit(er|ing)?|talent|human resources|\bhr\b|payroll|benefits|"
    r"accounting|controller|office manager|facilities|clinical|nurse|"
    r"construction|warehouse|store manager|retail|"
    r"product designer|graphic design|\bdesigner\b|data scientist|"
    r"analytics engineer|\bqa\b|quality assurance)\b",
    re.I,
)

# Seniority that disqualifies an entry-level role. Note: "manager" is NOT here
# because product/program/project titles legitimately contain it.
_PM_SENIOR = re.compile(
    r"\b(senior|sr\.?|staff|principal|lead|director|head of|\bvp\b|"
    r"vice president|group product manager|\bgpm\b|distinguished|expert)\b|"
    r"\b(ii|iii|iv|v)\b|\b\d+\+?\s*years?\b",
    re.I,
)

# Entry-level signals for full-time roles (boards list every level otherwise).
_PM_ENTRY = re.compile(
    r"\b(associate|analyst|\bapm\b|new[\s-]?grad(uate)?|entry[\s-]?level|"
    r"early[\s-]?career|rotational|university (grad|hire|program)?|campus|"
    r"recent grad(uate)?|junior|jr\.?|coordinator|college grad(uate)?|"
    r"new college grad|specialist|assistant)\b",
    re.I,
)

_INTERN = re.compile(r"\b(intern|internship|co[\s-]?op|summer (analyst|associate))\b", re.I)
# Non-full-time markers that disqualify a full-time role (intern handled apart).
_NON_FT = re.compile(r"\b(part[\s-]?time|contract(or)?|temporary|seasonal|fellowship)\b", re.I)

# New York + SF Bay Area (whole metro, not just SF). Applies to every recipient
# (non-SWE) role, full-time and internship alike.
_METRO = re.compile(
    r"\b(new york|nyc|new york city|manhattan|brooklyn|"
    r"san francisco|bay area|silicon valley|\bsf\b|"
    r"san jose|oakland|berkeley|palo alto|mountain view|menlo park|sunnyvale|"
    r"santa clara|cupertino|redwood city|san mateo|foster city|milpitas|"
    r"south san francisco|emeryville|fremont|san bruno|burlingame|campbell|"
    r"los gatos|san carlos|belmont|hayward|alameda|newark, ca)\b",
    re.I,
)

# Curated set of well-known employers, matched case-insensitively as whole words.
GOOD_COMPANIES = {
    # big tech
    "google", "alphabet", "meta", "facebook", "amazon", "apple", "microsoft",
    "netflix", "nvidia", "salesforce", "adobe", "oracle", "ibm", "uber", "lyft",
    "airbnb", "linkedin", "pinterest", "snap", "reddit", "dropbox", "block",
    "square", "paypal", "stripe", "coinbase", "doordash", "instacart",
    "databricks", "snowflake", "datadog", "atlassian", "servicenow", "workday",
    "intuit", "cisco", "qualcomm", "twilio", "zoom", "robinhood", "plaid",
    "ramp", "brex", "notion", "figma", "canva", "openai", "anthropic",
    "scale ai", "palantir", "roblox", "unity", "twitch", "discord", "spotify",
    "tiktok", "bytedance", "samsara", "confluent", "hashicorp", "gitlab",
    "github", "mongodb", "cloudflare", "okta", "crowdstrike", "splunk", "box",
    "asana", "airtable", "retool", "vercel", "amplitude", "rippling", "gusto",
    "deel", "flexport", "chime", "affirm", "sofi", "nubank", "wise", "toast",
    "faire", "whatnot", "mercury", "carta", "benchling", "anduril", "spacex",
    "tesla", "rivian", "lucid motors", "waymo", "cruise", "nuro", "zipline",
    # consulting / strategy
    "mckinsey", "bain", "boston consulting group", "bcg", "deloitte", "pwc",
    "ernst & young", "kpmg", "accenture", "oliver wyman", "kearney",
    "zs associates", "booz allen", "capgemini",
    # finance
    "goldman sachs", "morgan stanley", "jpmorgan", "blackrock", "citadel",
    "two sigma", "jane street", "bridgewater", "point72", "capital one",
    "american express", "visa", "mastercard", "bloomberg", "fidelity",
    "charles schwab", "citigroup", "blackstone", "betterment", "bilt",
    # consumer / media
    "disney", "warner bros", "nbcuniversal", "nike", "peloton", "etsy",
    "squarespace", "wayfair", "chewy", "grubhub", "starbucks", "warby parker",
    "glossier", "compass", "riskified", "yext", "cockroach labs", "dataminr",
    # chicago-notable
    "mcdonald's", "morningstar", "sprout social", "enova", "discover",
    "tovala", "cameo", "project44", "vivid seats", "tempus",
    # nyc-notable
    "oscar health", "justworks", "attentive", "alloy", "doubleverify",
}

_GOOD_RE = re.compile(
    r"\b(" + "|".join(sorted((re.escape(c) for c in GOOD_COMPANIES), key=len, reverse=True)) + r")\b",
    re.I,
)


def is_metro(location: str) -> bool:
    return bool(_METRO.search(location or ""))


def is_good_company(company: str) -> bool:
    return bool(_GOOD_RE.search(company or ""))


def is_pm_relevant(job, max_age_days: int) -> bool:
    t = job.title or ""
    if not _PM_TITLE.search(t):
        return False
    if _PM_EXCLUDE.search(t):
        return False
    if not is_recent(job.date_posted, max_age_days):
        return False
    # Every recipient (non-SWE) role must be in New York or the SF Bay Area,
    # in the US (guards against e.g. "San Jose, Costa Rica").
    if not is_metro(job.location) or not is_us(job.location):
        return False
    if _INTERN.search(t):
        # Internships also limited to curated top companies.
        return is_good_company(job.company)
    # Full-time: entry-level and genuinely full-time.
    if _NON_FT.search(t):
        return False
    if _PM_SENIOR.search(t):
        return False
    return bool(_PM_ENTRY.search(t))
