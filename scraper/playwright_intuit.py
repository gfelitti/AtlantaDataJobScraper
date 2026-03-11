"""
Playwright-based Intuit career scraper.
Portal: jobs.intuit.com
Pagination: JS-click Next button
"""

import logging
import re

from playwright.sync_api import Browser

logger = logging.getLogger(__name__)

TIMEOUT = 30_000
LOAD_WAIT = 5_000
PAGE_WAIT = 3_000
BASE_URL = "https://jobs.intuit.com"
SEARCH_URL = "https://jobs.intuit.com/search-jobs"


def _parse_jobs(page, company_name: str, seen: set) -> list[dict]:
    jobs = []

    for link in page.query_selector_all('a[href^="/job/"]'):
        href = link.get_attribute("href") or ""
        path = href.split("?")[0]

        # Job ID: last numeric segment
        job_id = ""
        for part in reversed(path.rstrip("/").split("/")):
            if part.isdigit():
                job_id = part
                break
        if not job_id or job_id in seen:
            continue
        seen.add(job_id)

        # Title and location are newline-separated in the link text
        text = link.inner_text().strip()
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        title = lines[0] if lines else ""
        location = lines[1] if len(lines) > 1 else ""

        if not title:
            continue

        jobs.append({
            "company": company_name,
            "job_id": job_id,
            "title": title,
            "location": location,
            "url": BASE_URL + path,
            "posted_date": None,
        })

    return jobs


def scrape(browser: Browser, company: dict, search_text: str = "data") -> list[dict]:
    """
    Scrape Intuit careers portal.
    Expected company dict keys: name
    """
    company_name = company["name"]
    all_jobs = []
    seen: set = set()
    page = browser.new_page()

    try:
        url = f"{SEARCH_URL}?q={search_text}&l=Atlanta%2C+GA"
        try:
            page.goto(url, wait_until="networkidle", timeout=TIMEOUT)
        except Exception as e:
            logger.warning("[%s] networkidle timeout, retrying with load: %s", company_name, e)
            try:
                page.goto(url, wait_until="load", timeout=TIMEOUT)
                page.wait_for_timeout(LOAD_WAIT)
            except Exception as e2:
                logger.error("[%s] Navigation failed: %s", company_name, e2)
                return []

        try:
            page.wait_for_selector('a[href^="/job/"]', timeout=LOAD_WAIT)
        except Exception:
            logger.warning("[%s] No jobs found on initial load", company_name)
            return []

        while True:
            jobs = _parse_jobs(page, company_name, seen)
            logger.debug("[%s] parsed=%d new jobs this page", company_name, len(jobs))

            if not jobs:
                break

            all_jobs.extend(jobs)

            # Pagination: find Next link and check if disabled
            next_btn = page.query_selector('a.next, a[aria-label="Next page"]')
            if not next_btn:
                break

            aria_disabled = next_btn.get_attribute("aria-disabled") or ""
            classes = next_btn.get_attribute("class") or ""
            if aria_disabled == "true" or "disabled" in classes:
                break

            try:
                next_btn.click()
                page.wait_for_timeout(PAGE_WAIT)
            except Exception as e:
                logger.error("[%s] Pagination error: %s", company_name, e)
                break

    finally:
        page.close()

    return all_jobs
