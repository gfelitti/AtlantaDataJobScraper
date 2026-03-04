"""
Playwright-based Avature scraper for companies that require JavaScript rendering.
Used for: Delta.
"""
import logging
import re
from urllib.parse import urljoin

from playwright.sync_api import Browser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
TIMEOUT = 30_000
PAGE_SIZE = 25


def _parse_jobs(html: str, company_name: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    jobs = []
    seen = set()

    for link in soup.select('a[href*="JobDetail"]'):
        href = link.get("href", "")
        title = link.get_text(strip=True)

        # Skip social share links
        if not title or any(s in href for s in ("linkedin", "twitter", "facebook", "mailto", "_linked")):
            continue
        if title.startswith("Share "):
            continue

        full_url = urljoin(base_url, href)

        # Job ID: last numeric segment in the URL path
        job_id = ""
        path_parts = [p for p in href.rstrip("/").split("/") if p]
        for part in reversed(path_parts):
            if part.isdigit():
                job_id = part
                break
        if not job_id:
            job_id = path_parts[-1] if path_parts else href

        if job_id in seen:
            continue
        seen.add(job_id)

        # Location: extract from container text between title and ". Ref"
        location = ""
        container = link.find_parent("li") or link.find_parent("tr") or link.find_parent("div")
        if container:
            text = container.get_text(" ", strip=True)
            # Remove title prefix, then take text before ". Ref"
            after_title = text[len(title):].strip() if text.startswith(title) else text
            ref_idx = after_title.find(". Ref")
            if ref_idx > 0:
                location = after_title[:ref_idx].strip()

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
    match = re.search(r"(\d+)\s+(?:results?|jobs?|positions?)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r"of\s+(\d+)", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def scrape(browser: Browser, company: dict, search_text: str = "data") -> list[dict]:
    base_url = company["base_url"]
    company_name = company["name"]
    all_jobs = []
    start_index = 0
    total = None
    page = browser.new_page()

    try:
        while True:
            url = f"{base_url}?searchText={search_text}&startIndex={start_index}&num={PAGE_SIZE}"
            try:
                page.goto(url, wait_until="networkidle", timeout=TIMEOUT)
            except Exception as e:
                logger.error("[%s] Navigation error at startIndex=%d: %s", company_name, start_index, e)
                break

            html = page.content()
            jobs = _parse_jobs(html, company_name, base_url)

            if total is None:
                total = _get_total(html)
                if total is not None:
                    logger.debug("[%s] total=%d", company_name, total)

            if not jobs:
                break

            all_jobs.extend(jobs)
            start_index += len(jobs)

            if total is not None and start_index >= total:
                break
    finally:
        page.close()

    return all_jobs
