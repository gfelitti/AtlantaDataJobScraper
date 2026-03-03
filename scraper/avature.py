"""
Avature scraper for Delta Air Lines.
Parses HTML search results from delta.avature.net.
Paginates via the `startIndex` query parameter.
"""

import logging
import re
from typing import Iterator
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

PAGE_SIZE = 25
TIMEOUT = 30

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _fetch_page(base_url: str, search_text: str, start_index: int) -> str:
    params = {
        "searchText": search_text,
        "startIndex": start_index,
        "num": PAGE_SIZE,
    }
    resp = requests.get(base_url, params=params, headers=_HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.text


def _parse_jobs(html: str, company_name: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    jobs = []

    # Avature renders job listings as <li> items within a job listing ul/section.
    # Common selectors across Avature tenants:
    items = soup.select("li.job-listing, li[class*='job'], article.job-listing")

    if not items:
        # Fallback: look for any <li> containing an <h3> with a job title link
        items = [li for li in soup.select("li") if li.find("h3")]

    for item in items:
        title_tag = item.find("h3") or item.find("h2")
        if not title_tag:
            continue

        link_tag = title_tag.find("a") or item.find("a")
        title = title_tag.get_text(strip=True)
        href = link_tag["href"] if link_tag and link_tag.get("href") else ""
        full_url = urljoin(base_url, href) if href else ""

        # Job ID: extract from URL path (e.g., /en_US/careers/JobDetail/Title/12345)
        job_id = ""
        if href:
            parts = [p for p in href.rstrip("/").split("/") if p]
            # Last numeric segment is usually the job ID
            for part in reversed(parts):
                if part.isdigit():
                    job_id = part
                    break
            if not job_id:
                job_id = parts[-1] if parts else href

        # Location: look for common location indicators
        location = ""
        loc_tag = item.select_one(".location, .job-location, [class*='location']")
        if loc_tag:
            location = loc_tag.get_text(strip=True)
        else:
            # Look for text patterns like "Atlanta, GA"
            text = item.get_text(" ", strip=True)
            loc_match = re.search(r"([A-Za-z\s]+,\s*[A-Z]{2})", text)
            if loc_match:
                location = loc_match.group(1).strip()

        jobs.append({
            "company": company_name,
            "job_id": job_id or full_url or title,
            "title": title,
            "location": location,
            "url": full_url,
            "posted_date": None,
        })

    return jobs


def _is_js_wall(html: str) -> bool:
    """Return True if Avature is blocking the request with a JS verification page."""
    return "JavaScript is disabled" in html or "verify that you're not a robot" in html


def _get_total(html: str) -> int | None:
    """Try to parse total job count from the page."""
    soup = BeautifulSoup(html, "lxml")
    # Avature often shows "X results" or "Showing 1-25 of X"
    text = soup.get_text(" ", strip=True)
    match = re.search(r"(\d+)\s+(?:results?|jobs?|positions?)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"of\s+(\d+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def scrape(company: dict, search_text: str = "data") -> Iterator[dict]:
    """Yield normalized job dicts for an Avature company."""
    base_url = company["base_url"]
    company_name = company["name"]

    start_index = 0
    total = None

    while True:
        try:
            html = _fetch_page(base_url, search_text, start_index)
        except requests.RequestException as exc:
            logger.error("[%s] Request error at startIndex=%d: %s", company_name, start_index, exc)
            break

        if _is_js_wall(html):
            logger.warning(
                "[%s] Avature returned a JavaScript verification page — job data requires a browser. "
                "Skipping. Consider adding Playwright support for this company.",
                company_name,
            )
            break

        jobs = _parse_jobs(html, company_name, base_url)

        if total is None:
            total = _get_total(html)
            if total is not None:
                logger.debug("[%s] total=%d", company_name, total)

        if not jobs:
            logger.debug("[%s] No jobs parsed at startIndex=%d — stopping", company_name, start_index)
            break

        yield from jobs

        start_index += len(jobs)
        if total is not None and start_index >= total:
            break
        if len(jobs) < PAGE_SIZE:
            # Last page
            break
