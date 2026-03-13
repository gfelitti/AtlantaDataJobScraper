"""
State Farm scraper using the hidden /api/jobs endpoint.
No authentication or Playwright required.
"""

import html as _html
import logging
import re
from typing import Iterator

import requests

logger = logging.getLogger(__name__)

_BASE_URL = "https://jobs.statefarm.com/api/jobs"
_JOB_URL = "https://jobs.statefarm.com/jobs/{slug}"

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:148.0) Gecko/20100101 Firefox/148.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://jobs.statefarm.com/",
})

PAGE_SIZE = 10
TIMEOUT = 30


def _strip_html(text: str) -> str:
    text = _html.unescape(text or "")
    return re.sub(r"<[^>]+>", " ", text).strip()


def _fetch_page(state: str, brand: str, page: int) -> dict:
    params = {
        "page": page,
        "sortBy": "relevance",
        "descending": "false",
        "internal": "false",
        "state": state,
        "brand": brand,
    }
    resp = _SESSION.get(_BASE_URL, params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def scrape(company: dict) -> Iterator[dict]:
    """
    Yield normalized job dicts for State Farm Careers.

    Expected company dict keys:
        name, ats, state, brand
    """
    company_name = company["name"]
    state = company.get("state", "Georgia")
    brand = company.get("brand", "State Farm")

    page = 1
    total = None

    while True:
        try:
            data = _fetch_page(state, brand, page)
        except requests.HTTPError as exc:
            logger.error("[%s] HTTP %s at page=%d", company_name, exc.response.status_code, page)
            break
        except requests.RequestException as exc:
            logger.error("[%s] Request error at page=%d: %s", company_name, page, exc)
            break

        if total is None:
            total = data.get("totalCount", 0)
            logger.debug("[%s] total=%d", company_name, total)

        jobs = data.get("jobs", [])
        if not jobs:
            break

        for job_wrapper in jobs:
            j = job_wrapper.get("data", {})
            slug = j.get("slug", "")
            title = j.get("title", "")
            city = j.get("city", "")
            job_state = j.get("state", "")
            location = f"{city}, {job_state}" if city and job_state else city or job_state
            description = _strip_html(j.get("description", "")) or None
            apply_url = j.get("apply_url", "")
            url = apply_url or (_JOB_URL.format(slug=slug) if slug else "")
            posted_date = (j.get("posted_date") or "")[:10] or None  # ISO 8601, truncate to date

            yield {
                "company": company_name,
                "job_id": slug,
                "title": title,
                "location": location,
                "url": url,
                "posted_date": posted_date,
                "description": description,
            }

        page += 1
        if (page - 1) * PAGE_SIZE >= total:
            break
