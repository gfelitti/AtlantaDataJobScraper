# Atlanta Data Job Scraper

Scrapes data and analytics job postings from major Atlanta-area employers, stores them in a local SQLite database, and serves them through a Next.js web interface. Optionally generates AI-powered structured summaries for each posting using Claude Haiku.

## Companies tracked

Home Depot, Truist, Cox Enterprises, NCR Voyix, Equifax, Carter's, Genuine Parts, Chick-fil-A, Delta, ICE.

## Stack

- **Scraper:** Python 3.13, Playwright (Chromium), Anthropic SDK
- **ATS support:** Workday (CXS JSON API), Avature, iCIMS
- **Database:** SQLite
- **Frontend:** Next.js 15 (App Router), Tailwind CSS, better-sqlite3

## Project structure

```
scraper/
  config.py           # Company registry
  runner.py           # Orchestrator
  workday.py          # Workday scraper
  avature.py          # Avature scraper
  generic.py          # iCIMS scraper
  db.py               # SQLite helpers
  playwright_fetch.py # Headless browser for JS-rendered descriptions
  summarizer.py       # Claude Haiku structured summary
frontend/
  app/                # Next.js routes and components
  lib/db.ts           # SQLite read layer
  types/job.ts        # Job type
main.py               # CLI entry point
```

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

For AI summaries, copy `.env.example` to `.env` and set your Anthropic API key:

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

## Adding a company

Append an entry to `COMPANIES` in `scraper/config.py`:

```python
# Workday
{"name": "Company", "ats": "workday", "tenant": "slug", "wday_suffix": "wd1", "site": "SiteName"}

# Avature
{"name": "Company", "ats": "avature", "base_url": "https://company.avature.net/en_US/careers/SearchJobs"}

# iCIMS
{"name": "Company", "ats": "generic", "base_url": "https://careers.company.com/jobs"}
```

Jobs are filtered to data/analytics roles in the Atlanta area. Filters are in `scraper/filters.py`.
