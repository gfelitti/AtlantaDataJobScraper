"""
Workday scraper using the undocumented wday/cxs JSON endpoint.
No authentication or cookies required.
"""

import logging
from typing import Iterator

import requests

logger = logging.getLogger(__name__)

_SESSION = requests.Session()
_SESSION.headers.update(
    {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }
)

PAGE_SIZE = 20
TIMEOUT = 30


def _base_url(tenant: str, suffix: str, site: str) -> str:
    return (
        f"https://{tenant}.{suffix}.myworkdayjobs.com"
        f"/wday/cxs/{tenant}/{site}/jobs"
    )


def _job_url(tenant: str, suffix: str, site: str, external_path: str) -> str:
    """Build a human-readable URL for a single job posting."""
    return (
        f"https://{tenant}.{suffix}.myworkdayjobs.com"
        f"/en-US/{site}{external_path}"
    )


def _fetch_page(url: str, search_text: str, offset: int) -> dict:
    payload = {
        "searchText": search_text,
        "limit": PAGE_SIZE,
        "offset": offset,
        "appliedFacets": {},
    }
    resp = _SESSION.post(url, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def scrape(company: dict, search_text: str = "data") -> Iterator[dict]:
    """
    Yield normalized job dicts for a Workday company config.

    Expected company dict keys:
        name, ats, tenant, wday_suffix, site
    """
    tenant = company["tenant"]
    suffix = company["wday_suffix"]
    site = company["site"]
    company_name = company["name"]

    url = _base_url(tenant, suffix, site)
    offset = 0
    total = None

    while True:
        try:
            data = _fetch_page(url, search_text, offset)
        except requests.HTTPError as exc:
            logger.error("[%s] HTTP %s fetching offset=%d", company_name, exc.response.status_code, offset)
            break
        except requests.RequestException as exc:
            logger.error("[%s] Request error at offset=%d: %s", company_name, offset, exc)
            break

        job_postings = data.get("jobPostings", [])
        if total is None:
            total = data.get("total", 0)
            logger.debug("[%s] total=%d", company_name, total)

        if not job_postings:
            break

        for posting in job_postings:
            external_path = posting.get("externalPath", "")
            # externalPath is like /job/Atlanta-GA/Data-Analyst_REQ12345
            # Use the last underscore-separated token as the req ID; fall back to full path.
            job_id = external_path.rsplit("_", 1)[-1] if "_" in external_path else external_path
            title = posting.get("title", "")
            location_nodes = posting.get("locationsText", "")

            yield {
                "company": company_name,
                "job_id": job_id or external_path,
                "title": title,
                "location": location_nodes,
                "url": _job_url(tenant, suffix, site, external_path),
                "posted_date": posting.get("postedOn", None),
            }

        offset += len(job_postings)
        if offset >= total:
            break
