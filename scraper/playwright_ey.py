"""
Playwright-based EY career scraper.
Portal: careers.ey.com
Pagination: startrow URL parameter (step=25)
"""

import logging
import re

from bs4 import BeautifulSoup
from playwright.sync_api import Browser

logger = logging.getLogger(__name__)

TIMEOUT = 30_000
PAGE_SIZE = 25
BASE_URL = "https://careers.ey.com"
SEARCH_URL = "https://careers.ey.com/careers/search"


def _parse_jobs(html: str, company_name: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    jobs = []
    seen = set()

    for link in soup.select("a.jobTitle-link"):
        href = link.get("href", "")
        title = link.get_text(strip=True)
        if not title or not href:
            continue

        # Job ID: last numeric path segment
        job_id = ""
        for part in reversed(href.rstrip("/").split("/")):
            if part.isdigit():
                job_id = part
                break
        if not job_id or job_id in seen:
            continue
        seen.add(job_id)

        full_url = BASE_URL + href if href.startswith("/") else href

        location = ""
        row = link.find_parent("tr") or link.find_parent("li")
        if row:
            loc_el = row.select_one("span.jobLocation")
            if loc_el:
                location = loc_el.get_text(strip=True)

        jobs.append({
            "company": company_name,
            "job_id": job_id,
            "title": title,
            "location": location,
            "url": full_url,
            "posted_date": None,
        })

    return jobs


def _get_total(html: str) -> int | None:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text(" ", strip=True)
    # "Results 1 – 25 of 215"
    match = re.search(r"of\s+(\d+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def scrape(browser: Browser, company: dict, search_text: str = "data") -> list[dict]:
    """
    Scrape EY careers portal.
    Expected company dict keys: name
    """
    company_name = company["name"]
    all_jobs = []
    startrow = 0
    total = None
    page = browser.new_page()

    try:
        # Accept cookie banner on first load
        first_url = f"{SEARCH_URL}?query={search_text}&location=Atlanta%2C+GA&startrow=0"
        try:
            page.goto(first_url, wait_until="networkidle", timeout=TIMEOUT)
        except Exception:
            page.goto(first_url, wait_until="load", timeout=TIMEOUT)
            page.wait_for_timeout(5000)
        try:
            page.click('button:has-text("Accept")', timeout=3000)
            page.wait_for_timeout(1000)
        except Exception:
            pass

        while True:
            url = f"{SEARCH_URL}?query={search_text}&location=Atlanta%2C+GA&startrow={startrow}"
            try:
                page.goto(url, wait_until="networkidle", timeout=TIMEOUT)
            except Exception as e:
                logger.warning("[%s] networkidle timeout at startrow=%d: %s", company_name, startrow, e)
                try:
                    page.goto(url, wait_until="load", timeout=TIMEOUT)
                    page.wait_for_timeout(5000)
                except Exception as e2:
                    logger.error("[%s] Navigation failed: %s", company_name, e2)
                    break

            html = page.content()

            if total is None:
                total = _get_total(html)
                if total is not None:
                    logger.debug("[%s] total=%d", company_name, total)

            jobs = _parse_jobs(html, company_name)
            logger.debug("[%s] startrow=%d parsed=%d", company_name, startrow, len(jobs))

            if not jobs:
                break

            all_jobs.extend(jobs)
            startrow += PAGE_SIZE

            if total is not None and startrow >= total:
                break

    finally:
        page.close()

    return all_jobs
