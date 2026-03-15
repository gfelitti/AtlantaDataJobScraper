"""
Backfill work_authorization for jobs that have a description but no label.
Uses regex classifier only — no Claude calls, no cost.

Usage: python3 migrate_work_authorization.py [--db jobs.db] [--dry-run]
"""
import argparse
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from scraper.filters import classify_work_authorization


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="jobs.db")
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing to DB")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("ALTER TABLE jobs ADD COLUMN work_authorization TEXT")
        conn.commit()
        print("Added work_authorization column")
    except sqlite3.OperationalError:
        pass  # already exists

    rows = conn.execute("""
        SELECT id, company, title, description
        FROM jobs
        WHERE (work_authorization IS NULL OR work_authorization = '')
          AND description IS NOT NULL
          AND description != ''
    """).fetchall()

    print(f"{len(rows)} jobs to classify")

    counts = {"sponsorship_provided": 0, "opt_accepted": 0, "citizen_gc_only": 0, "not_specified": 0}

    for row in rows:
        label = classify_work_authorization(row["description"])
        counts[label] += 1
        if not args.dry_run:
            conn.execute(
                "UPDATE jobs SET work_authorization=? WHERE id=?",
                (label, row["id"]),
            )
        if label != "not_specified":
            print(f"  [{label}] {row['company']}: {row['title']}")

    if not args.dry_run:
        conn.commit()

    conn.close()

    print(f"\nDone {'(dry run) ' if args.dry_run else ''}— {len(rows)} classified:")
    for label, count in counts.items():
        print(f"  {label}: {count}")


if __name__ == "__main__":
    main()
