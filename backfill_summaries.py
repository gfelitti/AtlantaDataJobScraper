"""
Backfill summaries for jobs that have a description but no summary.
Usage: python3 backfill_summaries.py [--companies Fiserv Equifax] [--db jobs.db]
"""
import argparse
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from scraper.summarizer import summarize


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="jobs.db")
    parser.add_argument("--companies", nargs="+", default=None)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    query = """
        SELECT id, company, job_id, title, description
        FROM jobs
        WHERE (summary IS NULL OR summary = '')
          AND description IS NOT NULL
          AND description != ''
    """
    params = []
    if args.companies:
        placeholders = ",".join("?" * len(args.companies))
        query += f" AND company IN ({placeholders})"
        params = args.companies

    rows = conn.execute(query, params).fetchall()
    print(f"{len(rows)} jobs to summarize")

    ok = 0
    fail = 0
    for row in rows:
        summary = summarize(row["title"], row["company"], row["description"])
        if summary:
            conn.execute(
                "UPDATE jobs SET summary=? WHERE id=?",
                (summary, row["id"]),
            )
            conn.commit()
            ok += 1
            print(f"  [{ok+fail}/{len(rows)}] OK  — {row['company']}: {row['title']}")
        else:
            fail += 1
            print(f"  [{ok+fail}/{len(rows)}] FAIL — {row['company']}: {row['title']}")

    conn.close()
    print(f"\nDone: {ok} summarized, {fail} failed")


if __name__ == "__main__":
    main()
