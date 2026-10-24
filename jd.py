import concurrent.futures as cf
import re

from sources.base import Job, get_json, http

_session = http()

# Explicit early-career language in a JD.
_NEW_GRAD = re.compile(
    r"\b(new[\s-]?grad(uate)?|recent grad(uate)?|entry[\s-]?level|early[\s-]?career|"
    r"currently (pursuing|enrolled)|final year|rising senior|graduating|"
    r"expected graduation|class of 20\d\d|0[\s-]*(?:to|-|–)\s*[12]\s*years|"
    r"campus|university (grad|hire|program)|no prior experience|"
    r"0\+?\s*years)\b",
    re.I,
)

# Any "N years of experience" requirement in the JD.
_YEARS = re.compile(r"(\d{1,2})\s*\+?\s*(?:to|-|–)?\s*(?:\d{1,2})?\s*years?", re.I)

# A JD asking for this many years is not new-grad, even if the title looked entry.
_MAX_YEARS = 2


def _min_years_required(text: str) -> int | None:
    # Smallest "N years" figure mentioned; None if experience isn't quantified.
    nums = [int(m.group(1)) for m in _YEARS.finditer(text)]
    return min(nums) if nums else None


def new_grad_ok(text: str) -> bool:
    if not text:
        return True  # no JD to judge; keep (title gate already applied)
    if _NEW_GRAD.search(text):
        return True
    years = _min_years_required(text)
    if years is not None and years > _MAX_YEARS:
        return False
    return True


# Software signals in a JD body.
_SW_SIGNAL = re.compile(
    r"\b(python|java|javascript|typescript|c\+\+|c#|golang|\bgo\b|rust|kotlin|"
    r"swift|ruby|scala|sql|react|angular|vue|node|\bapi\b|backend|back[\s-]?end|"
    r"frontend|front[\s-]?end|full[\s-]?stack|microservice|kubernetes|docker|"
    r"aws|azure|\bgcp\b|cloud|software (development|engineering)|writing code|"
    r"coding|algorithms|data structures|ci/cd|\bgit\b|rest|graphql|"
    r"distributed systems|web (app|application|service)|mobile app|"
    r"machine learning|data pipeline|\betl\b|databases?)\b",
    re.I,
)

# Clear hardware / physical-engineering signals.
_HW_SIGNAL = re.compile(
    r"\b(pcb|circuit|solder|schematic|fpga|verilog|vhdl|\brtl\b|asic|"
    r"analog design|rf design|antenna|oscilloscope|signal integrity|\bcad\b|"
    r"solidworks|mechanical design|hydraulic|pneumatic|hvac|cnc|machining|"
    r"wafer|lithograph|semiconductor fab|microcontroller|soldering|"
    r"power systems|electrical wiring|printed circuit)\b",
    re.I,
)


def is_software_jd(text: str) -> bool:
    # Conservative: only reject when the JD reads clearly hardware with no
    # software signal. Unreadable JDs fall through to the title filter (keep).
    if not text:
        return True
    if _HW_SIGNAL.search(text) and not _SW_SIGNAL.search(text):
        return False
    return True


def _fetch_description(job: Job) -> str:
    if job.description:
        return job.description
    try:
        if job.source == "Greenhouse" and job.board and job.native_id:
            url = f"https://boards-api.greenhouse.io/v1/boards/{job.board}/jobs/{job.native_id}"
            return get_json(_session, url).get("content", "") or ""
        if job.source == "SmartRecruiters" and job.board and job.native_id:
            url = f"https://api.smartrecruiters.com/v1/companies/{job.board}/postings/{job.native_id}"
            data = get_json(_session, url)
            secs = ((data.get("jobAd") or {}).get("sections") or {})
            return " ".join(
                (secs.get(k) or {}).get("text", "")
                for k in ("jobDescription", "qualifications", "additionalInformation")
            )
        if job.source == "Workday" and job.url:
            m = re.match(r"https://([^.]+)\.(wd\d+)\.myworkdayjobs\.com/([^/]+)(/.*)", job.url)
            if m:
                tn, pod, site, path = m.groups()
                detail = f"https://{tn}.{pod}.myworkdayjobs.com/wday/cxs/{tn}/{site}{path}"
                data = get_json(_session, detail)
                return (data.get("jobPostingInfo") or {}).get("jobDescription", "") or ""
    except Exception:
        return ""
    return ""


def keep_new_grad(jobs: list[Job], workers: int = 12) -> list[Job]:
    # Fetch each JD (where needed) in parallel, then keep only postings whose
    # description reads as new-grad / graduating, not experienced hires.
    if not jobs:
        return jobs
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        texts = list(ex.map(_fetch_description, jobs))
    return [j for j, t in zip(jobs, texts) if new_grad_ok(t)]


def keep_software(jobs: list[Job], workers: int = 12) -> list[Job]:
    # Read each JD and drop roles whose description reads as clearly
    # non-software (hardware, electrical, mechanical) despite the title.
    if not jobs:
        return jobs
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        texts = list(ex.map(_fetch_description, jobs))
    return [j for j, t in zip(jobs, texts) if is_software_jd(t)]
