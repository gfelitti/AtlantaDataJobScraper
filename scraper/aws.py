"""
Amazon Jobs scraper using the public search.json API.
No authentication or Playwright required.
"""

import json
import logging
from datetime import datetime
from typing import Iterator

import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.amazon.jobs/en/search.json"
_JOB_BASE = "https://www.amazon.jobs"

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:148.0) Gecko/20100101 Firefox/148.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.amazon.jobs/en/search",
})

PAGE_SIZE = 100
TIMEOUT = 30


def _resolve_location(j: dict) -> str:
    """
    Return the GA location string for a job.
    The primary `location` field reflects the first/largest posting location,
    which may not be GA even though Atlanta is one of the job's locations.
    When the primary location is not in GA, scan the `locations` array for a GA entry.
    """
    if j.get("state") == "GA":
        return j.get("location", "")
    for loc_str in j.get("locations") or []:
        try:
            loc = json.loads(loc_str)
            if loc.get("region") == "GA":
                return loc.get("location", j.get("location", ""))
        except (json.JSONDecodeError, AttributeError):
            continue
    return j.get("location", "")


def _is_data_center_role(title: str) -> bool:
    """Return True for physical data center operations roles (not data/analytics)."""
    return "data center" in title.lower()


def _parse_date(raw: str | None) -> str | None:
    """Convert 'March 11, 2026' to '2026-03-11'. Returns None if unparseable."""
    if not raw:
        return None
    try:
        return datetime.strptime(raw.strip(), "%B %d, %Y").date().isoformat()
    except ValueError:
        return None


def _fetch_page(city: str, business_category: str, offset: int) -> dict:
    params = {
        "normalized_city_name[]": city,
        "business_category[]": business_category,
        "radius": "24km",
        "offset": offset,
        "result_limit": PAGE_SIZE,
        "sort": "relevant",
    }
    resp = _SESSION.get(_BASE_URL, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def scrape(company: dict) -> Iterator[dict]:
    """
    Yield normalized job dicts for an Amazon Jobs company config.

    Expected company dict keys:
        name, ats, city, business_category
    """
    company_name = company["name"]
    city = company.get("city", "Atlanta")
    business_category = company.get("business_category", "amazon-web-services")

    offset = 0
    total = None

    while True:
        try:
            data = _fetch_page(city, business_category, offset)
        except requests.HTTPError as exc:
            logger.error("[%s] HTTP %s at offset=%d", company_name, exc.response.status_code, offset)
            break
        except requests.RequestException as exc:
            logger.error("[%s] Request error at offset=%d: %s", company_name, offset, exc)
            break

        if total is None:
            total = data.get("hits", 0)
            logger.debug("[%s] total=%d", company_name, total)

        jobs = data.get("jobs", [])
        if not jobs:
            break

        for j in jobs:
            title = j.get("title", "")
            if _is_data_center_role(title):
                continue
            job_path = j.get("job_path", "")
            yield {
                "company": company_name,
                "job_id": str(j.get("id_icims") or j.get("id", "")),
                "title": title,
                "location": _resolve_location(j),
                "url": _JOB_BASE + job_path if job_path else "",
                "posted_date": _parse_date(j.get("posted_date")),
            }

        offset += len(jobs)
        if offset >= total:
            break
