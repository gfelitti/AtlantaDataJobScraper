# Atlanta Data Job Scraper

Scrapes data and analytics job postings from major Atlanta-area employers, stores them in a SQLite database, and serves them through a Next.js web interface. Generates AI-powered structured summaries for each posting using Claude Haiku. Includes a CV matching feature that ranks active jobs against your resume using Claude Opus.

## Companies tracked (25)

Cardlytics, Carter's, Chick-fil-A, Coca-Cola, Cox Enterprises, Delta, Equifax, Fiserv, Genuine Parts, Global Payments, Home Depot, ICE, Inspire Brands, Invesco, Manhattan Associates, NCR Atleos, NCR Voyix, Novelis, RaceTrac, Salesforce, Smurfit WestRock, Truist, UPS, Veritiv, Warner Bros. Discovery.

## Stack

- **Scraper:** Python 3.13, Playwright (Chromium), Anthropic SDK
- **ATS support:** Workday (CXS JSON API), Avature (Playwright), iCIMS (Playwright)
- **Database:** SQLite
- **Frontend:** Next.js 15 (App Router), Tailwind CSS, better-sqlite3

## Project structure

```
scraper/
  config.py           # Company registry
  runner.py           # Orchestrator
  workday.py          # Workday scraper
  avature.py          # Avature (Playwright) scraper
  generic.py          # iCIMS (Playwright) scraper
  db.py               # SQLite helpers
  playwright_fetch.py # Headless browser for JS-rendered descriptions
  summarizer.py       # Claude Haiku structured summary
frontend/
  app/                # Next.js routes and components
  lib/db.ts           # SQLite read layer
  types/job.ts        # Job type
main.py               # CLI entry point
match_cv.py           # CV matching CLI
```

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env` and set your Anthropic API key:

```bash
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

If no valid key is provided, the scraper runs normally and skips summarization.

## Running the scraper

```bash
# All companies
python3 main.py

# Specific company
python3 main.py --companies "Truist"

# Verbose output
python3 main.py --verbose
```

The database (`jobs.db`) is created automatically on first run.

## Running the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Click any row to expand and see the structured summary (experience, salary, responsibilities, benefits, work arrangement) when available.

## CV matching

Match your resume against all active jobs from the command line:

```bash
python3 match_cv.py path/to/cv.pdf --db jobs.db
```

Or upload your resume at [http://localhost:3000/match](http://localhost:3000/match) to get ranked results in the browser. Supports PDF and DOCX. Jobs are ranked by Claude Opus and only those scoring ≥ 6/10 are shown.

## Adding a company

Append an entry to `COMPANIES` in `scraper/config.py`:

```python
# Workday
{"name": "Company", "ats": "workday", "tenant": "slug", "wday_suffix": "wd1", "site": "SiteName"}

# Avature (Playwright)
{"name": "Company", "ats": "avature_playwright", "base_url": "https://company.avature.net/en_US/careers/SearchJobs"}

# iCIMS (Playwright)
{"name": "Company", "ats": "icims_playwright", "base_url": "https://careers.company.com/jobs"}
```

Jobs are filtered to data/analytics roles in the Atlanta area. Filters are in `scraper/filters.py`.
