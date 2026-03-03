"""
Orchestrator: iterates over companies, dispatches to the correct scraper,
writes to DB, and runs the is_active sweep per company.
"""

import logging
import os
import sqlite3
from pathlib import Path
from typing import Callable, Iterator

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from . import avature, generic, workday
from .config import COMPANIES
from .db import get_conn, mark_inactive, update_description_summary, upsert_jobs_batch
from .filters import is_atlanta, is_data_role

logger = logging.getLogger(__name__)


def _scrape_company(company: dict) -> list[dict]:
    """Route to the right scraper and return all matching jobs."""
    ats = company["ats"]

    if ats == "workday":
        raw = list(workday.scrape(company))
    elif ats == "avature":
        raw = list(avature.scrape(company))
    elif ats == "generic":
        raw = list(generic.scrape(company))
    else:
        raise ValueError(f"Unknown ATS type: {ats!r}")

    return [job for job in raw if is_data_role(job["title"]) and is_atlanta(job["location"])]


def run(
    db_path: str,
    company_names: list[str] | None = None,
    verbose: bool = False,
) -> dict[str, dict]:
    """
    Run the scraper for the requested companies.

    Args:
        db_path: path to the SQLite database file
        company_names: subset of company names to scrape; None means all
        verbose: if True, log each job found

    Returns:
        dict mapping company name → {found, inserted, updated, deactivated, error}
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    targets = (
        [c for c in COMPANIES if c["name"] in company_names]
        if company_names
        else COMPANIES
    )

    if company_names:
        missing = set(company_names) - {c["name"] for c in targets}
        if missing:
            logger.warning("Unknown company names (skipped): %s", missing)

    results = {}

    for company in targets:
        name = company["name"]
        logger.info("Scraping %s ...", name)

        try:
            jobs = _scrape_company(company)
        except Exception as exc:
            logger.error("[%s] Scrape failed: %s", name, exc)
            results[name] = {"found": 0, "inserted": 0, "updated": 0, "deactivated": 0, "error": str(exc)}
            continue

        logger.info("[%s] %d data-role jobs found", name, len(jobs))

        if verbose:
            for job in jobs:
                logger.debug("  [%s] %s | %s", name, job["title"], job.get("location", ""))

        try:
            with get_conn(db_path) as conn:
                counts = upsert_jobs_batch(conn, jobs)
                seen_ids = {j["job_id"] for j in jobs}
                deactivated = mark_inactive(conn, name, seen_ids)
        except sqlite3.Error as exc:
            logger.error("[%s] DB error: %s", name, exc)
            results[name] = {"found": len(jobs), "inserted": 0, "updated": 0, "deactivated": 0, "error": str(exc)}
            continue

        new_job_ids = counts["inserted_ids"]
        new_jobs = [j for j in jobs if j["job_id"] in new_job_ids]

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if new_jobs and api_key and not api_key.startswith("sk-ant-...") and len(api_key) > 20:
            from playwright.sync_api import sync_playwright
            from . import playwright_fetch, summarizer
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    for job in new_jobs:
                        desc = playwright_fetch.fetch_description(browser, job["url"])
                        if desc:
                            summ = summarizer.summarize(job["title"], job["company"], desc)
                            with get_conn(db_path) as conn:
                                update_description_summary(conn, job["company"], job["job_id"], desc, summ or "")
                            if summ:
                                logger.info("[%s] summarized: %s", job["company"], job["title"])
                            else:
                                logger.warning("[%s] summary failed: %s", job["company"], job["title"])
                finally:
                    browser.close()

        results[name] = {
            "found": len(jobs),
            "inserted": counts["inserted"],
            "updated": counts["updated"],
            "deactivated": deactivated,
            "error": None,
        }
        logger.info(
            "[%s] inserted=%d updated=%d deactivated=%d",
            name,
            counts["inserted"],
            counts["updated"],
            deactivated,
        )

    return results
