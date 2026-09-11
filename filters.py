import re
from datetime import datetime, timezone

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
    r"sales|customer|field|solutions|network|test|validation|firmware|"
    r"nuclear|brake|suspension|water|wastewater|rail|fluids|vehicle|"
    r"mechanisms|launch|propulsion|thermal|avionics|antenna|packaging|"
    r"formulations|characterization|geotechnical|traffic|transportation|"
    r"water resources|process|production|controls|guidance|navigation|"
    r"mining|petroleum|drilling|welding|piping|hvac)\b",
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


# US state names, checked case-insensitively.
_US_STATE_NAMES = re.compile(
    r"\b(alabama|alaska|arizona|arkansas|california|colorado|connecticut|"
    r"delaware|florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|"
    r"kentucky|louisiana|maine|maryland|massachusetts|michigan|minnesota|"
    r"mississippi|missouri|montana|nebraska|nevada|new hampshire|new jersey|"
    r"new mexico|new york|north carolina|north dakota|ohio|oklahoma|oregon|"
    r"pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|"
    r"utah|vermont|virginia|washington|west virginia|wisconsin|wyoming|"
    r"district of columbia|washington,?\s*d\.?c\.?)\b",
    re.I,
)

# State abbreviations, checked case-sensitively (avoids matching "or", "in", "me").
_US_STATE_ABBR = re.compile(
    r"\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|"
    r"MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|"
    r"VA|WA|WV|WI|WY|DC|USA?)\b"
)

_US_COUNTRY = re.compile(r"\b(united states|u\.?s\.?a?\.?)\b", re.I)

# Well-known US metros that often appear without a state qualifier.
_US_CITIES = re.compile(
    r"\b(new york city|nyc|san francisco|los angeles|chicago|boston|seattle|"
    r"austin|denver|atlanta|miami|dallas|houston|philadelphia|phoenix|"
    r"san diego|san jose|silicon valley|bay area|washington)\b",
    re.I,
)

# Explicit non-US signals: countries and major foreign cities.
_NON_US = re.compile(
    r"\b(canada|toronto|vancouver|montreal|ottawa|waterloo|"
    r"united kingdom|england|london|manchester|edinburgh|dublin|ireland|"
    r"germany|berlin|munich|frankfurt|france|paris|spain|madrid|barcelona|"
    r"portugal|lisbon|netherlands|amsterdam|belgium|brussels|switzerland|"
    r"zurich|geneva|sweden|stockholm|norway|oslo|denmark|copenhagen|finland|"
    r"helsinki|poland|warsaw|krakow|austria|vienna|italy|rome|milan|"
    r"india|bangalore|bengaluru|hyderabad|mumbai|delhi|pune|chennai|gurgaon|"
    r"noida|china|beijing|shanghai|shenzhen|hong kong|singapore|japan|tokyo|"
    r"korea|seoul|australia|sydney|melbourne|new zealand|brazil|sao paulo|"
    r"mexico|mexico city|argentina|buenos aires|colombia|bogota|chile|"
    r"israel|tel aviv|united arab emirates|dubai|abu dhabi|egypt|cairo|"
    r"south africa|nigeria|kenya|philippines|manila|indonesia|jakarta|"
    r"vietnam|hanoi|thailand|bangkok|malaysia|kuala lumpur|taiwan|taipei|"
    r"emea|apac|latam|romania|bucharest|ukraine|kyiv|czech|prague|hungary|"
    r"budapest|greece|athens|turkey|istanbul|remote\s*[-,]?\s*(europe|uk|"
    r"canada|india|apac|emea|latam))\b",
    re.I,
)


def is_us(location: str) -> bool:
    loc = (location or "").strip()
    if not loc:
        return False
    low = loc.lower()
    # Bare "remote" with no foreign qualifier counts as US-eligible.
    if low in ("remote", "remote us", "us remote", "remote - us", "remote (us)"):
        return True
    if _NON_US.search(loc):
        return False
    if _US_COUNTRY.search(loc):
        return True
    if _US_STATE_NAMES.search(loc):
        return True
    if _US_CITIES.search(loc):
        return True
    if _US_STATE_ABBR.search(loc):
        return True
    # "Remote" appearing alongside other text, with no foreign signal above.
    if re.search(r"\bremote\b", loc, re.I):
        return True
    return False


def is_recent(date_posted: str, max_age_days: int) -> bool:
    if not date_posted:
        return False
    try:
        posted = datetime.strptime(date_posted[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return False
    age = (datetime.now(timezone.utc).date() - posted).days
    # Keep anything within the window; age < 0 is future-dated (clock skew), keep it too.
    return age <= max_age_days
