"""
Orchestrator: iterates over companies, dispatches to the correct scraper,
writes to DB, and runs the is_active sweep per company.
"""

import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Callable, Iterator

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from . import aws, avature, generic, google, microsoft, statefarm, workday
from .config import COMPANIES
from .db import get_conn, mark_inactive, set_setting, update_description_summary, update_work_authorization, upsert_jobs_batch
from .filters import classify_work_authorization, is_atlanta, is_data_role

_VALID_AUTH_LABELS = {"sponsorship_provided", "opt_accepted", "citizen_gc_only", "not_specified"}

logger = logging.getLogger(__name__)

PLAYWRIGHT_ATS = {"icims_playwright", "avature_playwright", "successfactors_playwright", "ey_playwright", "intuit_playwright"}


def _scrape_company(company: dict, browser=None) -> list[dict]:
    """Route to the right scraper and return all matching jobs."""
    ats = company["ats"]

    if ats == "aws":
        raw = list(aws.scrape(company))
    elif ats == "google":
        raw = list(google.scrape(company))
    elif ats == "microsoft":
        raw = list(microsoft.scrape(company))
    elif ats == "workday":
        raw = list(workday.scrape(company))
    elif ats == "avature":
        raw = list(avature.scrape(company))
    elif ats == "statefarm":
        raw = list(statefarm.scrape(company))
    elif ats == "generic":
        raw = list(generic.scrape(company))
    elif ats == "icims_playwright":
        from . import playwright_icims
        raw = playwright_icims.scrape(browser, company)
    elif ats == "avature_playwright":
        from . import playwright_avature
        raw = playwright_avature.scrape(browser, company)
    elif ats == "successfactors_playwright":
        from . import playwright_successfactors
        raw = playwright_successfactors.scrape(browser, company)
    elif ats == "ey_playwright":
        from . import playwright_ey
        raw = playwright_ey.scrape(browser, company)
    elif ats == "intuit_playwright":
        from . import playwright_intuit
        raw = playwright_intuit.scrape(browser, company)
    else:
        raise ValueError(f"Unknown ATS type: {ats!r}")

    assume_atlanta = company.get("assume_atlanta", False)
    return [job for job in raw if is_data_role(job["title"]) and (assume_atlanta or is_atlanta(job["location"]))]


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

    with get_conn(db_path) as conn:
        set_setting(conn, "companies_monitored", str(len(COMPANIES)))

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    use_summaries = api_key and not api_key.startswith("sk-ant-...") and len(api_key) > 20
    needs_playwright = any(c["ats"] in PLAYWRIGHT_ATS for c in targets)

    logger.info("api_key present=%s len=%d", bool(api_key), len(api_key))

    browser = None
    playwright_ctx = None

    if needs_playwright or use_summaries:
        from playwright.sync_api import sync_playwright
        from . import playwright_fetch, summarizer
        playwright_ctx = sync_playwright().start()
        browser = playwright_ctx.chromium.launch(headless=True)

    results = {}

    try:
        for company in targets:
            name = company["name"]
            logger.info("Scraping %s ...", name)

            try:
                jobs = _scrape_company(company, browser=browser)
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

            # Also include existing jobs that have no description yet (e.g. from runs before
            # description extraction was implemented for this ATS type)
            if use_summaries:
                with get_conn(db_path) as conn:
                    no_desc_ids = {
                        row["job_id"]
                        for row in conn.execute(
                            "SELECT job_id FROM jobs WHERE company=? AND is_active=1 AND (description IS NULL OR description='')",
                            (name,),
                        ).fetchall()
                    }
            else:
                no_desc_ids = set()

            jobs_needing_desc = [j for j in jobs if j["job_id"] in new_job_ids | no_desc_ids]

            if jobs_needing_desc and use_summaries and browser:
                for job in jobs_needing_desc:
                    desc = job.get("description") or playwright_fetch.fetch_description(browser, job["url"])
                    if desc:
                        summ = summarizer.summarize(job["title"], job["company"], desc)
                        # Extract work_authorization from Claude's JSON; fall back to regex
                        auth_label = classify_work_authorization(desc)
                        if summ:
                            try:
                                claude_label = json.loads(summ).get("work_authorization", "")
                                if claude_label in _VALID_AUTH_LABELS:
                                    auth_label = claude_label
                            except Exception:
                                pass
                        with get_conn(db_path) as conn:
                            update_description_summary(conn, job["company"], job["job_id"], desc, summ or "")
                            update_work_authorization(conn, job["company"], job["job_id"], auth_label)
                        logger.info("[%s] work_authorization=%s: %s", job["company"], auth_label, job["title"])
                        if not summ:
                            logger.warning("[%s] summary failed: %s", job["company"], job["title"])

            results[name] = {
                "found": len(jobs),
                "inserted": counts["inserted"],
                "updated": counts["updated"],
                "deactivated": deactivated,
                "error": None,
                "new_jobs": [j for j in jobs if j["job_id"] in new_job_ids],
            }
            logger.info(
                "[%s] inserted=%d updated=%d deactivated=%d",
                name,
                counts["inserted"],
                counts["updated"],
                deactivated,
            )

    finally:
        if browser:
            browser.close()
        if playwright_ctx:
            playwright_ctx.stop()

    return results
