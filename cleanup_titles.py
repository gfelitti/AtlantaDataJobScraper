"""
cleanup_titles.py — mark active jobs as inactive if their title no longer
passes the current is_data_role() filter.

Usage:
    python3 cleanup_titles.py --db /data/jobs.db [--dry-run]
"""

import argparse
import sqlite3
from datetime import datetime, timezone

from scraper.filters import is_data_role

parser = argparse.ArgumentParser()
parser.add_argument("--db", required=True)
parser.add_argument("--dry-run", action="store_true")
args = parser.parse_args()

conn = sqlite3.connect(args.db)
conn.row_factory = sqlite3.Row

rows = conn.execute("SELECT company, job_id, title FROM jobs WHERE is_active = 1").fetchall()

to_deactivate = [(r["company"], r["job_id"], r["title"]) for r in rows if not is_data_role(r["title"])]

print(f"Active jobs: {len(rows)}")
print(f"To deactivate: {len(to_deactivate)}")

for company, job_id, title in to_deactivate:
    print(f"  [{company}] {title}")

if not args.dry_run and to_deactivate:
    now = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        "UPDATE jobs SET is_active = 0, deactivated_at = ? WHERE company = ? AND job_id = ?",
        [(now, company, job_id) for company, job_id, _ in to_deactivate],
    )
    conn.commit()
    print(f"\nDeactivated {len(to_deactivate)} jobs.")
elif args.dry_run:
    print("\nDry run — no changes made.")

conn.close()
