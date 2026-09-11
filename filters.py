import re

# Full-time only: drop internships, co-ops, part-time, contract, seasonal.
_NOT_FULLTIME = re.compile(
    r"\b(intern|internship|co[\s-]?op|apprentice(ship)?|working student|"
    r"part[\s-]?time|contract(or)?|temporary|seasonal|fellowship|summer)\b",
    re.I,
)

# Seniority / level markers that disqualify a role as entry-level.
_SENIOR = re.compile(
    r"\b(senior|sr\.?|staff|principal|lead|manager|director|head|vp|"
    r"vice president|architect|expert|distinguished)\b|"
    r"\b(ii|iii|iv|v|vi)\b|"
    r"\bengineer\s*[2-9]\b|"
    r"\b\d+\+?\s*years?\b",
    re.I,
)

# Positive entry-level signals, required for raw ATS feeds.
_ENTRY = re.compile(
    r"\b(new[\s-]?grad(uate)?|entry[\s-]?level|early[\s-]?career|"
    r"university (grad|hire)|campus|recent grad(uate)?|college grad(uate)?|"
    r"graduate (software|engineer|program)|associate (software )?engineer|"
    r"junior|jr\.?)\b|"
    r"\bengineer\s+i\b|\bsoftware engineer i\b|\bswe\s+i\b",
    re.I,
)

# Software / adjacent role signal.
_SOFTWARE = re.compile(
    r"\b(software|engineer|developer|programmer|sde|swe|data (scientist|engineer|analyst)|"
    r"machine learning|\bml\b|\bai\b|backend|back[\s-]?end|frontend|front[\s-]?end|"
    r"full[\s-]?stack|devops|\bsre\b|platform|infrastructure|quant|"
    r"applied scientist|research engineer)\b",
    re.I,
)

# Engineering titles that are NOT software.
_NON_SOFTWARE = re.compile(
    r"\b(mechanical|electrical|civil|chemical|biomedical|industrial|aerospace|"
    r"materials|structural|environmental|manufacturing|optical|hardware|"
    r"sales|customer|field|solutions|network|test|validation|firmware)\b",
    re.I,
)

# Categories kept from community feeds (which tag each posting).
ALLOWED_CATEGORIES = {
    "Software", "Software Engineering", "AI/ML/Data", "Quant",
    "Data Science, AI & Machine Learning", "ATS",
}


def is_relevant(title: str, category: str, from_ats: bool) -> bool:
    t = title or ""
    if _NOT_FULLTIME.search(t):
        return False
    if _SENIOR.search(t):
        return False
    if category and category not in ALLOWED_CATEGORIES:
        return False
    # Applies to every source: curated feeds also carry mislabeled non-eng roles.
    if _NON_SOFTWARE.search(t):
        return False
    if not _SOFTWARE.search(t):
        return False
    if from_ats:
        # Raw ATS boards list every level, so require an entry-level signal too.
        if not _ENTRY.search(t):
            return False
    return True
