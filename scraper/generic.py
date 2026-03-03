"""
Generic iCIMS scraper for ICE (Intercontinental Exchange).

LIMITATION: careers.ice.com uses iCIMS Jibe, a JavaScript-rendered Angular
app. Simple HTTP requests return the page shell without job data. This scraper
attempts to fetch the underlying iCIMS search endpoint; if JavaScript rendering
is required, it logs a warning and returns no results rather than silently failing.

Confirmed HTML structure from live inspection (when JS renders):
  - Each job row: <tr class="iCIMS_JobListingRow">
  - Title + link: <a title="ID - Title"><h3>Title</h3></a>
  - Location: text, format "US-GA-Atlanta"
  - Job ID: from title attribute, format "2026-12471"
  - Pagination: ?pr=N (0-indexed page number)
"""

import logging
import re
from typing import Iterator

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TIMEOUT = 30
ICIMS_SEARCH = "https://careers-ice.icims.com/jobs/search"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _make_session(main_url: str) -> requests.Session:
    """Hit the main careers page to establish session cookies."""
    session = requests.Session()
    session.headers.update(_HEADERS)
    try:
        session.get(main_url, timeout=TIMEOUT)
    except requests.RequestException:
        pass
    return session


def _parse_icims(html: str, company_name: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    jobs = []

    rows = soup.select("tr.iCIMS_JobListingRow")
    for row in rows:
        link_tag = row.find("a", title=True)
        if not link_tag:
            continue

        title_attr = link_tag.get("title", "")
        id_match = re.match(r"^(\d{4}-\d+)\s*-\s*(.+)$", title_attr)
        if id_match:
            job_id = id_match.group(1)
            title = id_match.group(2).strip()
        else:
            title = link_tag.get_text(strip=True)
            job_id = ""

        href = link_tag.get("href", "")
        full_url = href if href.startswith("http") else f"https://careers-ice.icims.com{href}"

        if not job_id and href:
            id_match2 = re.search(r"/jobs/(\d+)/", href)
            if id_match2:
                job_id = id_match2.group(1)

        location = ""
        text = row.get_text(" ", strip=True)
        loc_match = re.search(r"(US-[A-Z]{2}-[A-Za-z\s\-]+)", text)
        if loc_match:
            raw_loc = loc_match.group(1).strip()
            parts = raw_loc.split("-", 2)
            if len(parts) == 3:
                location = f"{parts[2]}, {parts[1]}"
            else:
                location = raw_loc

        jobs.append({
            "company": company_name,
            "job_id": job_id or full_url or title,
            "title": title,
            "location": location,
            "url": full_url,
            "posted_date": None,
        })

    return jobs


def _has_next_page(html: str) -> bool:
    soup = BeautifulSoup(html, "lxml")
    return bool(soup.find("a", string=re.compile(r"next", re.IGNORECASE)))


def _is_js_wall(html: str) -> bool:
    """
    Return True if the response is a JS shell with no renderable job data.
    iCIMS Jibe references 'iCIMS_JobListingRow' in JavaScript strings even
    when the DOM rows are absent — so check for the cookie wall text instead.
    """
    return "Please Enable Cookies" in html or (
        "iCIMS_JobsTable" in html
        and BeautifulSoup(html, "lxml").select_one("tr.iCIMS_JobListingRow") is None
    )


def scrape(company: dict, search_text: str = "data") -> Iterator[dict]:
    """Yield normalized job dicts for an iCIMS company."""
    company_name = company["name"]
    main_url = company["base_url"]

    session = _make_session(main_url)
    page = 0

    while True:
        try:
            resp = session.get(
                ICIMS_SEARCH,
                params={"ss": 1, "searchKeyword": search_text, "in_iframe": 1, "pr": page},
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            html = resp.text
        except requests.RequestException as exc:
            logger.error("[%s] Request error at page=%d: %s", company_name, page, exc)
            break

        if _is_js_wall(html):
            logger.warning(
                "[%s] iCIMS returned a JavaScript-rendered shell — job data requires a browser. "
                "Skipping. Consider adding Playwright support for this company.",
                company_name,
            )
            break

        jobs = _parse_icims(html, company_name)
        logger.debug("[%s] page=%d parsed=%d jobs", company_name, page, len(jobs))

        if not jobs:
            break

        yield from jobs

        if not _has_next_page(html):
            break

        page += 1
