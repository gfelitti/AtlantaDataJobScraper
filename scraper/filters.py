"""
Pure keyword filters for data-related roles and Atlanta-area locations.
No side effects.
"""

import re

KEYWORDS = [
    "analyst",
    "analytics",
    "data engineer",
    "data scientist",
    "machine learning",
    "ml engineer",
    "ai engineer",
    "business intelligence",
    "bi developer",
    "data architect",
    "reporting analyst",
    "quantitative",
    "nlp",
    "data",
]


def is_data_role(title: str) -> bool:
    """Return True if the job title contains any data-role keyword (case-insensitive)."""
    lower = title.lower()
    return any(kw in lower for kw in KEYWORDS)


# Atlanta metro area location terms (case-insensitive substring match)
_ATLANTA_TERMS = [
    "atlanta",
    "georgia",
    "alpharetta",
    "marietta",
    "sandy springs",
    "decatur",
    "duluth, ga",
    "norcross, ga",
    "roswell, ga",
    "peachtree",
]


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
