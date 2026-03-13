"""
Microsoft careers scraper using the public pcsx/search API.
No authentication or Playwright required.
Page size is fixed at 10; paginates via `start` offset.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Iterator

import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://apply.careers.microsoft.com/api/pcsx/search"
_JOB_BASE = "https://apply.careers.microsoft.com"

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:148.0) Gecko/20100101 Firefox/148.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://apply.careers.microsoft.com/careers",
})

TIMEOUT = 30
_MAX_RETRIES = 5
_GA_TERMS = ("georgia", ", ga,", "atlanta")


def _ga_location(locations: list[str]) -> str:
    """Return the first GA location string, falling back to first entry."""
    for loc in locations:
        if any(t in loc.lower() for t in _GA_TERMS):
            return loc
    return locations[0] if locations else ""


def _is_data_center_role(title: str) -> bool:
    """Exclude physical data center operations roles."""
    lower = title.lower()
    return "datacenter" in lower or "data center" in lower


_RETRY_STATUSES = {403, 429}


def _fetch_page(location: str, start: int) -> dict:
    params = {
        "domain": "microsoft.com",
        "query": "",
        "location": location,
        "start": start,
        "sort_by": "distance",
        "filter_distance": 160,
        "filter_include_remote": 1,
        "hl": "en",
    }
    delay = 5
    for attempt in range(_MAX_RETRIES):
        resp = _SESSION.get(_BASE_URL, params=params, timeout=TIMEOUT)
        if resp.status_code in _RETRY_STATUSES and attempt < _MAX_RETRIES - 1:
            logger.warning("Microsoft %d at start=%d, retry %d/%d (wait %ds)",
                           resp.status_code, start, attempt + 1, _MAX_RETRIES, delay)
            time.sleep(delay)
            delay *= 2  # exponential backoff: 5, 10, 20, 40s
            continue
        resp.raise_for_status()
        return resp.json()["data"]


def scrape(company: dict) -> Iterator[dict]:
    """
    Yield normalized job dicts for Microsoft.

    Expected company dict keys:
        name, ats, location
    """
    company_name = company["name"]
    location = company.get("location", "United States, Georgia, Atlanta")

    start = 0
    total = None

    while True:
        try:
            data = _fetch_page(location, start)
        except requests.HTTPError as exc:
            logger.error("[%s] HTTP %s at start=%d", company_name, exc.response.status_code, start)
            break
        except requests.RequestException as exc:
            logger.error("[%s] Request error at start=%d: %s", company_name, start, exc)
            break

        if total is None:
            total = data.get("count", 0)
            logger.debug("[%s] total=%d", company_name, total)

        positions = data.get("positions", [])
        if not positions:
            break

        for p in positions:
            title = p.get("name", "")
            if _is_data_center_role(title):
                continue

            posted_ts = p.get("postedTs")
            posted_date = (
                datetime.fromtimestamp(posted_ts, tz=timezone.utc).date().isoformat()
                if posted_ts else None
            )

            yield {
                "company": company_name,
                "job_id": str(p.get("atsJobId") or p.get("id", "")),
                "title": title,
                "location": _ga_location(p.get("locations") or []),
                "url": _JOB_BASE + p["positionUrl"],
                "posted_date": posted_date,
            }

        start += len(positions)
        if start >= total:
            break
