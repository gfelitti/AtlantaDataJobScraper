from playwright.sync_api import Browser

SELECTORS = [
    "[data-automation-id='jobPostingDescription']",
    "section[data-automation-id='jobReqDescription']",
    "[data-automation-id='job-posting-details']",
]


def fetch_description(browser: Browser, url: str) -> str | None:
    page = browser.new_page()
    try:
        page.goto(url, wait_until="networkidle", timeout=30_000)
        for sel in SELECTORS:
            el = page.query_selector(sel)
            if el:
                return el.inner_text().strip()
        return None
    except Exception:
        return None
    finally:
        page.close()
