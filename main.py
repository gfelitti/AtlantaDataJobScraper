"""
Atlanta Data Roles Job Scraper
Usage:
    python main.py --all
    python main.py --companies "Truist" "Equifax"
    python main.py --all --db /path/to/custom.db
    python main.py --all --verbose
"""

import argparse
import sys
from pathlib import Path

# Make `scraper` importable when running main.py directly from JobScraper/
sys.path.insert(0, str(Path(__file__).parent))

from scraper.config import COMPANIES
from scraper.db import init_db
from scraper.emailer import send_digest
from scraper.runner import run


def main() -> None:
    all_names = [c["name"] for c in COMPANIES]

    parser = argparse.ArgumentParser(
        description="Scrape Atlanta-area data-role job postings into a local SQLite DB."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--all",
        action="store_true",
        help="Scrape all configured companies.",
    )
    group.add_argument(
        "--companies",
        nargs="+",
        metavar="COMPANY",
        help=f"Space-separated company names. Available: {', '.join(all_names)}",
    )
    parser.add_argument(
        "--db",
        default=str(Path(__file__).parent / "jobs.db"),
        metavar="PATH",
        help="Path to the SQLite database file. (default: jobs.db in this directory)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each job as it is found.",
    )

    args = parser.parse_args()
    company_names = None if args.all else args.companies

    init_db(args.db)
    results = run(db_path=args.db, company_names=company_names, verbose=args.verbose)

    print("\n── Results ─────────────────────────────────────────")
    total_found = total_inserted = total_updated = total_deactivated = 0
    errors = []

    new_jobs_by_company: dict[str, list] = {}

    for company, stats in results.items():
        found = stats["found"]
        inserted = stats["inserted"]
        updated = stats["updated"]
        deactivated = stats["deactivated"]
        error = stats["error"]

        total_found += found
        total_inserted += inserted
        total_updated += updated
        total_deactivated += deactivated

        status = f"ERROR: {error}" if error else f"found={found} inserted={inserted} updated={updated} deactivated={deactivated}"
        print(f"  {company:<20} {status}")

        if error:
            errors.append(company)
        elif stats.get("new_jobs"):
            new_jobs_by_company[company] = stats["new_jobs"]

    print("─────────────────────────────────────────────────────")
    print(
        f"  TOTAL                found={total_found} inserted={total_inserted} "
        f"updated={total_updated} deactivated={total_deactivated}"
    )
    if errors:
        print(f"\n  Failed companies: {', '.join(errors)}")

    if new_jobs_by_company:
        send_digest(new_jobs_by_company)

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
