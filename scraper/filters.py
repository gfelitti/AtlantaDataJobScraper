"""
Pure keyword filters for data-related roles and Atlanta-area locations.
No side effects.
"""

import re

KEYWORDS = [
    # Core data/analytics
    "analyst",
    "analytics",
    "data engineer",
    "data scientist",
    "data architect",
    "data analyst",
    "data manager",
    "data quality",
    "data governance",
    "data steward",
    "data modeler",
    "database administrator",
    "database developer",
    # ML / AI
    "machine learning",
    "ml engineer",
    "ai engineer",
    "applied scientist",
    "research scientist",
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
    "reporting engineer",
    "insights analyst",
    "insights manager",
    "insights engineer",
    "tableau",
    "power bi",
    "looker",
    # Quantitative / Stats
    "quantitative",
    "statistician",
    "econometri",
    # Broad catch-all (last — lower priority)
    "data",
]

_EXCLUDE_KEYWORDS = [
    "data entry",
    "master data",
    "data capture",
    "data conversion",
    "data migration specialist",
    "data transcription",
    "data processor",
    "data input",
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


_SPONSORSHIP_PATTERNS = re.compile(
    r"no\s+(opt|cpt|stem[\s/]*opt|visa\s+sponsor)",
    re.IGNORECASE,
)

_AUTHORIZATION_PATTERNS = re.compile(
    r"(must|required)\s+.{0,60}(authorized|eligible)\s+to\s+work\s+in\s+the\s+u\.?s\.?"
    r"|without\s+(current\s+or\s+future\s+)?sponsorship"
    r"|sponsorship\s+(is\s+)?(not|unavailable|not\s+available)",
    re.IGNORECASE,
)


def has_sponsorship_restriction(description: str) -> bool:
    """Return True if the job description explicitly excludes visa sponsorship / OPT/CPT."""
    return bool(
        _SPONSORSHIP_PATTERNS.search(description)
        or _AUTHORIZATION_PATTERNS.search(description)
    )


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
