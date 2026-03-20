"""
Pure keyword filters for data-related roles and Atlanta-area locations.
No side effects.
"""

import re

KEYWORDS = [
    # Core data roles
    "data engineer",
    "data scientist",
    "data science",
    "data analyst",
    "data analytics",
    "data architect",
    "data manager",
    "data quality",
    "data governance",
    "data modeler",
    "database administrator",
    "database developer",
    # ML / AI
    "machine learning",
    "ml engineer",
    "ai engineer",
    "applied scientist",
    "decision science",
    "deep learning",
    "computer vision",
    "nlp",
    "llm",
    "generative ai",
    # BI / Reporting
    "business intelligence",
    "bi developer",
    "bi engineer",
    "reporting analyst",
    "insights analyst",
    # Tools
    "tableau",
    "power bi",
    "looker",
    # Quantitative
    "quantitative analyst",
    "statistician",
    # MSBA-aligned roles
    "data product manager",
    "product analytics",
    "data & analytics",
    "supply chain analytics",
    "data consultant",
    "analytics consultant",
]

# Companies confirmed by hiring teams to not offer sponsorship.
# work_authorization is hardcoded to "citizen_gc_only" regardless of job description.
# Must match company names exactly as defined in config.py.
CITIZEN_GC_ONLY_COMPANIES = {
    "Coca-Cola",
    "Children's Healthcare of Atlanta",
    "Delta",
}

_EXCLUDE_KEYWORDS = [
    "data entry",
    "master data",
    "data capture",
    "data conversion",
    "data migration specialist",
    "data transcription",
    "data processor",
    "data input",
    # Non-data roles that match broad keywords (e.g. "analyst", "research scientist")
    "cybersecurity",
    "cyber security",
    "quality assurance",
    "user experience",
    "ux designer",
    "ui designer",
    "food scientist",
    "sweetener",
    "actuarial",
]


def is_data_role(title: str) -> bool:
    """Return True if the job title contains any data-role keyword (case-insensitive)
    and does not match any exclusion keyword."""
    lower = title.lower()
    if any(ex in lower for ex in _EXCLUDE_KEYWORDS):
        return False
    return any(kw in lower for kw in KEYWORDS)


# Atlanta metro area location terms (case-insensitive substring match)
_ATLANTA_TERMS = [
    "atlanta",
    "georgia",
    # North suburbs
    "alpharetta",
    "roswell, ga",
    "duluth, ga",
    "norcross, ga",
    "johns creek",
    "cumming, ga",
    "canton, ga",
    # East / Northeast
    "decatur",
    "tucker, ga",
    "stone mountain",
    "lawrenceville, ga",
    "gwinnett",
    # South
    "peachtree",
    "fayetteville, ga",
    "mcdonough, ga",
    "stockbridge, ga",
    # West / Northwest
    "marietta",
    "kennesaw",
    "smyrna, ga",
    "dunwoody",
    "sandy springs",
    "mableton",
    "austell, ga",
]


def parse_posted_date(raw: str | None) -> str | None:
    """
    Convert Workday relative dates to ISO format (YYYY-MM-DD).
    Examples: "Posted 5 Days Ago" -> "2026-02-27", "Posted 30+ Days Ago" -> "2026-02-02"
    Returns None if unparseable.
    """
    if not raw:
        return None
    from datetime import date, timedelta
    lower = raw.lower()
    if "today" in lower or "just posted" in lower:
        return date.today().isoformat()
    if "yesterday" in lower:
        return (date.today() - timedelta(days=1)).isoformat()
    m = re.search(r"(\d+)\+?\s+days?\s+ago", lower)
    if m:
        return (date.today() - timedelta(days=int(m.group(1)))).isoformat()
    return None


_SPONSORSHIP_PROVIDED = re.compile(
    r"(will|can|does|do)\s+(provide|offer|support)?\s*sponsor.{0,40}(visa|h[\s-]?1b|work\s+authoriz)"
    r"|(visa|h[\s-]?1b)\s+(sponsorship\s+)?(is\s+)?(available|provided|offered|supported)"
    r"|we\s+(do\s+)?sponsor\s+(h[\s-]?1b|visa|work)",
    re.IGNORECASE,
)

_OPT_ACCEPTED = re.compile(
    # Positive OPT signals
    r"(opt|cpt|stem[\s/]*opt|f[\s-]?1)\s+(is\s+)?(accepted|welcome|eligible|authorized|ok)"
    r"|(opt|cpt|stem[\s/]*opt|f[\s-]?1)\s+.{0,30}(welcome|accepted|eligible|authorized)"
    r"|(accept|welcome|consider)\s+.{0,30}(opt|cpt|f[\s-]?1)"
    # "No sponsorship but OPT OK" — company won't sponsor but doesn't exclude OPT
    r"|(will\s+not|does\s+not|cannot|unable\s+to)\s+.{0,20}(offer|provide)?\s*(sponsorship|sponsor\s+.{0,20}(visa|h[\s-]?1b|employment))"
    r"|must\s+not\s+require.{0,60}sponsorship"
    r"|(must|required)\s+.{0,60}(authorized|eligible)\s+to\s+work\s+in\s+the\s+u\.?s\.?"
    r"|without\s+(current\s+or\s+future\s+)?sponsorship"
    r"|sponsorship\s+(is\s+)?(not|unavailable|not\s+available)",
    re.IGNORECASE,
)

_CITIZEN_GC_ONLY = re.compile(
    # Explicit OPT/CPT exclusion
    r"no\s+(opt|cpt|stem[\s/]*opt)"
    # Citizenship / permanent residency required
    r"|u\.?s\.?\s+citizen(ship)?\s+(or\s+.{0,20})?(required|only|must)"
    r"|must\s+be\s+a\s+u\.?s\.?\s+citizen"
    r"|u\.?s\.?\s+persons?\s+only"
    # Unrestricted = permanent authorization (excludes OPT which is time-limited)
    r"|unrestricted\s+(u\.?s\.?\s+)?work\s+authoriz",
    re.IGNORECASE,
)


def classify_work_authorization(description: str) -> str:
    """
    Classify the work authorization stance of a job description.

    Returns one of:
        'sponsorship_provided' — company explicitly offers H-1B/visa sponsorship
        'opt_accepted'         — OPT/CPT accepted but no sponsorship mentioned
        'citizen_gc_only'      — explicitly excludes visa holders / OPT / sponsorship
        'not_specified'        — no work authorization language detected

    Order matters: citizen_gc_only is checked before sponsorship_provided to
    catch phrases like "unable to sponsor" before the general sponsorship pattern.
    """
    if not description:
        return "not_specified"
    if _CITIZEN_GC_ONLY.search(description):
        return "citizen_gc_only"
    if _SPONSORSHIP_PROVIDED.search(description):
        return "sponsorship_provided"
    if _OPT_ACCEPTED.search(description):
        return "opt_accepted"
    return "not_specified"


def has_sponsorship_restriction(description: str) -> bool:
    """Deprecated — use classify_work_authorization() instead."""
    return classify_work_authorization(description) == "citizen_gc_only"


def is_atlanta(location: str | None) -> bool:
    """
    Return True if the location is in the Atlanta metro area.
    Multi-location entries ("2 Locations", etc.) are treated as unknown and passed through.
    """
    if not location:
        return False
    loc = location.lower()
    # "2 Locations", "3 Locations", etc. — can't determine without extra API calls
    if re.search(r"\d+\s+locations?", loc):
        return True
    return any(term in loc for term in _ATLANTA_TERMS)
