"""
Google Careers scraper — parses job data embedded in page HTML.
No API key, auth, or Playwright required.
Paginates via ?page=N (20 jobs/page).
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Iterator

import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.google.com/about/careers/applications/jobs/results/"
_JOB_URL = "https://www.google.com/about/careers/applications/jobs/results/{}"

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:148.0) Gecko/20100101 Firefox/148.0",
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "en-US,en;q=0.9",
})

PAGE_SIZE = 20
TIMEOUT = 30

_DS1_RE = re.compile(
    r"AF_initDataCallback\(\{key: 'ds:1'.*?data:(.*?), sideChannel:.*?\}\);",
    re.S,
)


def _fetch_page(location: str, page: int) -> tuple[list, int]:
    """Return (jobs_list, total) for the given page number (1-indexed)."""
    params = {"location": location, "page": page}
    resp = _SESSION.get(_BASE_URL, params=params, timeout=TIMEOUT)
    resp.raise_for_status()

    m = _DS1_RE.search(resp.text)
    if not m:
        return [], 0

    data = json.loads(m.group(1))
    jobs = data[0] or []
    total = data[2] or 0
    return jobs, total


def _ga_location(locations_raw: list) -> str:
    """
    Return the GA location string from the locations array.
    Falls back to first entry if no GA location found.
    Each entry: [city_state_country, [full_addr], city, zip, state, country]
    """
    if not locations_raw:
        return ""
    for loc in locations_raw:
        if loc and len(loc) >= 6 and loc[4] == "GA":
            return loc[0]  # e.g. "Atlanta, GA, USA"
    return locations_raw[0][0] if locations_raw[0] else ""


def scrape(company: dict) -> Iterator[dict]:
    """
    Yield normalized job dicts for Google Careers.

    Expected company dict keys:
        name, ats, location
    """
    company_name = company["name"]
    location = company.get("location", "Atlanta, GA, USA")

    page = 1
    total = None

    while True:
        try:
            jobs, page_total = _fetch_page(location, page)
        except requests.HTTPError as exc:
            logger.error("[%s] HTTP %s at page=%d", company_name, exc.response.status_code, page)
            break
        except requests.RequestException as exc:
            logger.error("[%s] Request error at page=%d: %s", company_name, page, exc)
            break

        if total is None:
            total = page_total
            logger.debug("[%s] total=%d", company_name, total)

        if not jobs:
            break

        for j in jobs:
            ts = j[12][0] if j[12] else None
            posted_date = (
                datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
                if ts else None
            )
            yield {
                "company": company_name,
                "job_id": str(j[0]),
                "title": j[1],
                "location": _ga_location(j[9]),
                "url": _JOB_URL.format(j[0]),
                "posted_date": posted_date,
            }

        page += 1
        if (page - 1) * PAGE_SIZE >= total:
            break
