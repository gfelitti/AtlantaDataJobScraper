"""
Backfill years_experience for jobs that have a summary but no years_experience value.
Parses the existing summary JSON — no new Claude calls needed.
For jobs with summary but no years_experience field, falls back to calling Claude.

Usage: python3 backfill_years_experience.py [--db jobs.db] [--dry-run]
"""
import argparse
import json
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from scraper.summarizer import summarize


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="jobs.db")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("ALTER TABLE jobs ADD COLUMN years_experience INTEGER")
        conn.commit()
        print("Added years_experience column")
    except sqlite3.OperationalError:
        pass  # already exists

    rows = conn.execute("""
        SELECT id, company, title, description, summary
        FROM jobs
        WHERE (years_experience IS NULL)
          AND description IS NOT NULL AND description != ''
    """).fetchall()

    print(f"{len(rows)} jobs to process")

    from_summary = 0
    from_claude = 0
    null_count = 0
    fail_count = 0

    for i, row in enumerate(rows):
        years = None

        # First: try to extract from existing summary JSON (free)
        if row["summary"]:
            try:
                parsed = json.loads(row["summary"])
                raw = parsed.get("years_experience")
                if isinstance(raw, int) and raw >= 0:
                    years = raw
                    from_summary += 1
            except Exception:
                pass

        # Fallback: call Claude to re-summarize (costs tokens)
        if years is None and row["description"]:
            summ = summarize(row["title"], row["company"], row["description"])
            if summ:
                try:
                    raw = json.loads(summ).get("years_experience")
                    if isinstance(raw, int) and raw >= 0:
                        years = raw
                        from_claude += 1
                    else:
                        null_count += 1
                except Exception:
                    fail_count += 1
            else:
                fail_count += 1

        if not args.dry_run and years is not None:
            conn.execute("UPDATE jobs SET years_experience=? WHERE id=?", (years, row["id"]))
            if (i + 1) % 20 == 0:
                conn.commit()

        label = f"{years} yrs" if years is not None else "null"
        print(f"  [{i+1}/{len(rows)}] {label:8s} — {row['company']}: {row['title']}")

    if not args.dry_run:
        conn.commit()

    conn.close()
    print(f"\nDone {'(dry run) ' if args.dry_run else ''}:")
    print(f"  From existing summary : {from_summary}")
    print(f"  From new Claude call  : {from_claude}")
    print(f"  Null (not specified)  : {null_count}")
    print(f"  Failed                : {fail_count}")


if __name__ == "__main__":
    main()
