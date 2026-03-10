"""
Playwright-based iCIMS scraper for companies that require JavaScript rendering.
Used for: Chick-fil-A, ICE.

Both sites use a custom iCIMS template with job links in an iframe,
using a[href*="/jobs/{id}/"] rather than the standard tr.iCIMS_JobListingRow.
"""
import logging
import re

from playwright.sync_api import Browser

logger = logging.getLogger(__name__)
TIMEOUT = 30_000


def _parse_jobs(frame, company_name: str, base_url: str) -> list[dict]:
    origin = "/".join(base_url.split("/")[:3])
    jobs = []

    links = frame.query_selector_all('a[href*="/jobs/"]')
    for link in links:
        href = link.get_attribute("href") or ""

        # Only job detail links: /jobs/{numeric_id}/
        if not re.search(r"/jobs/\d+/", href):
            continue

        id_match = re.search(r"/jobs/(\d+)/", href)
        job_id = id_match.group(1) if id_match else ""
        if not job_id:
            continue

        # Title: link text may be prefixed with a column header like "Position Title\n"
        raw_title = link.inner_text().strip()
        title = raw_title.split("\n")[-1].strip() if "\n" in raw_title else raw_title
        if not title:
            continue

        full_url = href if href.startswith("http") else f"{origin}{href}"

        # Location from closest table row or container
        location = ""
        try:
            parent = link.evaluate_handle(
                'el => el.closest("tr, li, article") || el.parentElement.parentElement'
            )
            parent_text = parent.as_element().inner_text()
            loc_match = re.search(r"([A-Za-z][A-Za-z\s]+,\s*[A-Z]{2})\b", parent_text)
            if loc_match:
                location = loc_match.group(1).strip()
        except Exception:
            pass

        jobs.append({
            "company": company_name,
            "job_id": job_id,
            "title": title,
            "location": location,
            "url": full_url,
            "posted_date": None,
        })

    return jobs


def scrape(browser: Browser, company: dict, search_text: str = "data") -> list[dict]:
    company_name = company["name"]
    search_url = company["base_url"]
    all_jobs = []
    page_num = 0
    page = browser.new_page()

    try:
        while True:
            outer_url = (
                f"{search_url}?ss=1&searchKeyword={search_text}"
                f"&pr={page_num}&mobile=false&width=1166&height=500"
                f"&bga=true&needsRedirect=false&jan1offset=-300&jun1offset=-240"
            )
            try:
                page.goto(outer_url, wait_until="networkidle", timeout=TIMEOUT)
            except Exception:
                try:
                    page.goto(outer_url, wait_until="load", timeout=TIMEOUT)
                    page.wait_for_timeout(3000)
                except Exception as e:
                    logger.error("[%s] Navigation error at page=%d: %s", company_name, page_num, e)
                    break

            # Jobs are in the first non-main iframe (frame index 1)
            frames = page.frames
            content_frame = frames[1] if len(frames) > 1 else page.main_frame

            jobs = _parse_jobs(content_frame, company_name, search_url)
            logger.debug("[%s] page=%d parsed=%d jobs", company_name, page_num, len(jobs))

            if not jobs:
                break

            all_jobs.extend(jobs)

            if not content_frame.query_selector("a[title='Next']"):
                break

            page_num += 1
    finally:
        page.close()

    return all_jobs
