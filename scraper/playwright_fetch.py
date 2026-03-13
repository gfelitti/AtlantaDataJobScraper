import json
import re

from playwright.sync_api import Browser

SELECTORS = [
    # Workday
    "[data-automation-id='jobPostingDescription']",
    "section[data-automation-id='jobReqDescription']",
    "[data-automation-id='job-posting-details']",
    # iCIMS (Chick-fil-A, ICE) — content loads in a nested frame
    ".iCIMS_JobContent",
]


def _query_frames(page, selector: str) -> str | None:
    """Try selector on main frame first, then all child frames."""
    for frame in page.frames:
        el = frame.query_selector(selector)
        if el:
            text = el.inner_text().strip()
            if text:
                return text
    return None


def fetch_description(browser: Browser, url: str) -> str | None:
    page = browser.new_page()
    try:
        try:
            page.goto(url, wait_until="load", timeout=30_000)
        except Exception:
            pass  # page may still be usable even if load didn't fully complete
        # Give JS a moment to render dynamic content (iCIMS injects via script tags)
        page.wait_for_timeout(5_000)
        for sel in SELECTORS:
            text = _query_frames(page, sel)
            if text:
                return text
        # Fallback: JSON-LD JobPosting (Microsoft, etc.)
        try:
            html = page.content()
            m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
            if m:
                ld = json.loads(m.group(1))
                if ld.get("@type") == "JobPosting" and ld.get("description"):
                    return ld["description"]
        except Exception:
            pass
        return None
    except Exception:
        return None
    finally:
        page.close()
