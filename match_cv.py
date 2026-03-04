"""
Match your CV against active job listings.

Usage:
    python3 match_cv.py path/to/cv.pdf [--top 20] [--out results.md]
"""
import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


def read_cv(path: str) -> str:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(p)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if p.suffix.lower() == ".docx":
        from docx import Document
        doc = Document(p)
        return "\n".join(para.text for para in doc.paragraphs)
    return p.read_text()


def load_jobs(db_path: str) -> list[dict]:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """
        SELECT id, company, title, url, summary
        FROM jobs
        WHERE is_active = 1 AND summary IS NOT NULL
        ORDER BY company, title
        """
    ).fetchall()
    conn.close()
    return [
        {"id": r[0], "company": r[1], "title": r[2], "url": r[3], "summary": r[4]}
        for r in rows
    ]


SYSTEM = "You are a career advisor. Return ONLY valid JSON, no markdown, no explanation."

PROMPT = """Given the CV below, rank these job listings by fit. For each job return:
- "id": the job id (integer)
- "score": fit score 1-10
- "reason": one sentence explaining the fit

Return a JSON array sorted by score descending. Only include jobs with score >= 6.

=== CV ===
{cv}

=== JOBS ===
{jobs}"""


def rank_jobs(cv_text: str, jobs: list[dict]) -> list[dict]:
    jobs_text = "\n".join(
        f"[{j['id']}] {j['title']} @ {j['company']}\n{j['summary']}\n"
        for j in jobs
    )

    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4096,
        system=SYSTEM,
        messages=[{"role": "user", "content": PROMPT.format(
            cv=cv_text[:6000],
            jobs=jobs_text[:60000],
        )}],
    )
    text = msg.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    return json.loads(text)


def format_results(ranked: list[dict], jobs_by_id: dict, top: int) -> str:
    lines = [f"# CV Match Results — top {top} jobs\n"]
    for i, r in enumerate(ranked[:top], 1):
        job = jobs_by_id.get(r["id"])
        if not job:
            continue
        lines.append(
            f"## {i}. [{job['title']} @ {job['company']}]({job['url']})\n"
            f"**Score:** {r['score']}/10  \n"
            f"**Why:** {r['reason']}\n"
        )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("cv", help="Path to CV (PDF or .txt)")
    parser.add_argument("--top", type=int, default=20, help="Number of results to show")
    parser.add_argument("--out", default=None, help="Save results to this file")
    parser.add_argument("--db", default="jobs.db", help="Path to SQLite DB")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", dest="fmt")
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not set")

    if args.fmt == "json":
        cv_text = read_cv(args.cv)
        jobs = load_jobs(args.db)
        ranked = rank_jobs(cv_text, jobs)
        jobs_by_id = {j["id"]: j for j in jobs}
        results = []
        for i, r in enumerate(ranked[:args.top], 1):
            job = jobs_by_id.get(r["id"])
            if not job:
                continue
            results.append({
                "rank": i,
                "score": r["score"],
                "reason": r["reason"],
                "title": job["title"],
                "company": job["company"],
                "url": job["url"],
            })
        print(json.dumps(results))
        return

    print(f"Reading CV: {args.cv}")
    cv_text = read_cv(args.cv)
    print(f"  {len(cv_text)} chars extracted")

    print(f"Loading jobs from {args.db}...")
    jobs = load_jobs(args.db)
    print(f"  {len(jobs)} active jobs with summaries")

    print("Ranking with Claude Opus...")
    ranked = rank_jobs(cv_text, jobs)
    print(f"  {len(ranked)} jobs scored >= 6")

    jobs_by_id = {j["id"]: j for j in jobs}
    output = format_results(ranked, jobs_by_id, args.top)

    if args.out:
        Path(args.out).write_text(output)
        print(f"\nSaved to {args.out}")
    else:
        print("\n" + output)


if __name__ == "__main__":
    main()
