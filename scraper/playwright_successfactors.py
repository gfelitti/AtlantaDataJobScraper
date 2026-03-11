"""
Playwright-based SAP SuccessFactors scraper.
Used for: AGCO, Porsche North America, EY.

Career portal URL pattern:
  https://{sf_host}/portalcareer?company={sf_company_id}&career_company={sf_company_id}
    &lang=en_US&navBarLevel=JOB_SEARCH&SearchTerm={keyword}

Jobs load dynamically via JavaScript (JSF/AJAX). DOM landmarks:
  #job-table         — main listing container
  .jobTitle a        — job title link (href contains jobId=)
  .jobGeoLocation    — location text
"""

import logging
import re

from playwright.sync_api import Browser

logger = logging.getLogger(__name__)

TIMEOUT = 45_000
LOAD_WAIT = 8_000   # SF renders slowly after navigation
PAGE_WAIT = 5_000   # wait between pagination clicks


def _build_url(host: str, company_id: str, keyword: str) -> str:
    return (
        f"https://{host}/portalcareer"
        f"?company={company_id}&career_company={company_id}"
        f"&lang=en_US&navBarLevel=JOB_SEARCH&SearchTerm={keyword}"
    )


def _parse_jobs(page, company_name: str, host: str) -> list[dict]:
    jobs = []
    seen = set()

    links = page.query_selector_all('a[href*="jobId="]')
    for link in links:
        href = link.get_attribute("href") or ""
        if not href:
            continue

        job_id_match = re.search(r"jobId=([^&]+)", href)
        if not job_id_match:
            continue
        job_id = job_id_match.group(1)
        if job_id in seen:
            continue
        seen.add(job_id)

        title = link.inner_text().strip()
        if not title:
            continue

        full_url = href if href.startswith("http") else f"https://{host}{href}"

        # Location: look in .jobGeoLocation sibling, then fall back to row text
        location = ""
        try:
            container = link.evaluate_handle(
                "el => el.closest('.jobDisplay, tr, li, article') || el.parentElement.parentElement"
            )
            el = container.as_element()
            geo = el.query_selector(".jobGeoLocation")
            if geo:
                location = geo.inner_text().strip()
            else:
                row_text = el.inner_text()
                after_title = row_text.replace(title, "", 1).strip()
                loc_match = re.search(r"([A-Za-z][A-Za-z\s]+,\s*[A-Z]{2})\b", after_title)
                if loc_match:
                    location = loc_match.group(1).strip()
                elif after_title:
                    parts = [p.strip() for p in after_title.split("\n") if p.strip()]
                    if parts:
                        location = parts[0]
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
    """
    Scrape a SAP SuccessFactors career portal.

    Expected company dict keys:
        name, ats, sf_company_id, sf_host
    """
    company_name = company["name"]
    host = company["sf_host"]
    company_id = company["sf_company_id"]
    url = _build_url(host, company_id, search_text)

    all_jobs = []
    page = browser.new_page()

    try:
        # Initial navigation
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

        # Wait for job table to appear
        try:
            page.wait_for_selector("#job-table, .jobTitle, a[href*='jobId=']", timeout=LOAD_WAIT)
        except Exception:
            logger.warning("[%s] Job table did not appear — page may require login or returned no results", company_name)
            return []

        # Scrape pages
        while True:
            jobs = _parse_jobs(page, company_name, host)
            logger.debug("[%s] parsed=%d jobs", company_name, len(jobs))

            if not jobs:
                break

            all_jobs.extend(jobs)

            # Pagination: SuccessFactors uses "Next Page" or load-more patterns
            next_btn = (
                page.query_selector('a[title="Next Page"]')
                or page.query_selector('a[title="Next"]')
                or page.query_selector('button[title="Next Page"]')
                or page.query_selector('.sapMListShowMoreButton')  # load-more variant
            )
            if not next_btn:
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
