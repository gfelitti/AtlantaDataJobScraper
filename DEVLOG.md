# JobScraper Dev Log

## Working State
**Session:** 5 | **Date:** 2026-03-19

### Active Task
Title filter overhaul + cron fix + email recipients + company sponsorship hardcode.

- [x] Fix cron python path (`/usr/local/bin/python3`)
- [x] Overhaul KEYWORDS: remove broad standalone terms, add MSBA-aligned compound terms
- [x] Hardcode citizen_gc_only for Coca-Cola, Children's Healthcare of Atlanta, Delta
- [x] Add cleanup_titles.py — deactivates DB jobs that no longer pass filter
- [x] Add 4 email recipients (Eugene, Sissy, Sneha, Siyao)
- [x] Create .env with export vars for deploy
- [x] Deploy to jobscraper2
- [x] Run cleanup_titles — 40 deactivated, 97 active, 0 remaining to clean

### Key Files (current shape)
**`scraper/filters.py`** (MODIFIED)
KEYWORDS now uses specific compound terms only — no standalone "analyst", "analytics", "data". Added: data science, product analytics, & analytics, and analytics, data product manager, supply chain analytics, data consultant, analytics consultant. CITIZEN_GC_ONLY_COMPANIES constant for 3 confirmed no-sponsorship companies.

**`scraper/runner.py`** (MODIFIED)
Imports CITIZEN_GC_ONLY_COMPANIES; overrides auth_label to citizen_gc_only before DB write if company is in the set.

**`scraper/summarizer.py`** (MODIFIED)
Prompt updated with company override note for Coca-Cola, Children's Healthcare of Atlanta, Delta.

**`cleanup_titles.py`** (NEW)
Deactivates active jobs whose title no longer passes is_data_role(). Supports --dry-run. Run after every filter change.

**`.env`** (NEW, gitignored)
Deploy vars with export prefix. Use: `source .env && ./deploy_lightsail.sh`.

### Decisions (active)
- Removed from KEYWORDS: "analyst", "analytics", "data" (standalone), "research scientist", "business analyst", "product manager", "senior analyst", "senior consultant", "product analyst", "product associate", "revenue operations analyst" — all too broad without data qualifier
- CITIZEN_GC_ONLY_COMPANIES overrides both regex and Claude label — hiring team confirmed, no description language needed
- cleanup_titles.py uses is_data_role() directly — automatically reflects any KEYWORDS change

### Next Steps
1. Monitor 7am UTC cron run tomorrow — verify email sent to all 5 recipients
2. Run cleanup_titles after any future filter change

### Watch Out
- Claude overrides regex for `work_authorization` — `migrate_work_authorization.py` does NOT fix jobs that already have a Claude-generated label
- cleanup_titles only deactivates; use manual reactivation query for false positives
- mark_inactive and cleanup_titles write to same deactivated_at field — can't distinguish them by timestamp alone

---
---

## Backlog

### In Progress
- [ ] Fix Coca-Cola R-134645-1 misclassification manually on Lightsail (citizen_gc_only → opt_accepted; Claude override, regex doesn't match)

### Pending
- [ ] **Autonomous agent pipeline** — evolve JobScraper from a scrape+display tool into a full agentic job search system. Three new layers on top of the existing scraper:
  1. **Evaluator** — Claude scores each new job (0–10) against a fixed candidate profile (target roles, stack, seniority, sponsorship). Same call as summary, zero extra cost. Replaces manual filtering in the frontend.
  2. **CV generator** — for jobs above score threshold, Claude generates a tailored CV/cover letter as PDF using the job description + candidate profile as context. One file per application.
  3. **Auto-apply** — Playwright fills ATS forms (Workday, Greenhouse, iCIMS, Avature already scraped) using the generated CV + stored EEO answers. HITL gate before submit: user reviews, then approves or skips.
  Architecture reference: Career-Ops (Reddit r/SideProject, 2026-03-17) — 12 independent skill files, dedup TSV, real browser session (non-headless) to avoid bot detection.
- [ ] **Acuity Insurance** — UltiPro/UKG Pro, requires Playwright (POST endpoint, React SPA). Deferred to next session.
- [ ] **Deactivated_at frontend display** — show badge/date when a job was deactivated in the UI
- [ ] **EY descriptions** — validate that descriptions are now being fetched correctly after playwright_fetch fix
- [ ] **`migrate_work_authorization.py` gap** — script overwrites Claude labels blindly with regex. For jobs where Claude set `citizen_gc_only` but regex finds no matching pattern (Claude hallucinated), the script currently makes things worse if run after Claude has already populated the field. Fix: add a `--fix-claude-overrides` mode that only updates jobs where Claude label != regex label AND regex returns `not_specified` or `opt_accepted`.

### Done
- [x] Risk 1: expand role keyword filter + exclusion list
- [x] Risk 2: expand Atlanta suburb location terms
- [x] Work authorization classifier (4-label regex + Claude)
- [x] Years experience (DB column + Claude extraction + backfill script)
- [x] `deactivated_at` timestamp column
- [x] State Farm scraper
- [x] `migrate_work_authorization.py`
- [x] `backfill_years_experience.py`
- [x] Frontend filters: work_authorization dropdown + years_experience slider

---

## Open Questions

### Q1 — Coca-Cola sponsorship language
**Job:** [Senior Manager, Software Engineer, Data Platform Segmentation](https://coke.wd1.myworkdayjobs.com/en-US/coca-cola-careers/job/US---GA---Atlanta/Senior-Manager--Software-Engineer--Data-Platform-Segmentation_R-134645-1)
**Question:** Does "The Coca-Cola Company will not offer sponsorship for employment status (including H1-B)" + "all applicants must be currently authorized to work in the United States" mean OPT is accepted?
**Context:** OPT holders ARE currently authorized — they don't require future sponsorship. Our classifier correctly calls this `opt_accepted`. But Claude called it `citizen_gc_only`. Need to decide: is our interpretation correct, or does this boilerplate actually exclude OPT holders?
**Status:** Open

---

## Session Archive

### Session 5 — 2026-03-19: Title filter overhaul + cron fix
**What we did:** Fixed cron python path, rewrote KEYWORDS to remove broad standalone terms, hardcoded citizen_gc_only for 3 companies, added cleanup_titles.py, added 5 email recipients, created .env for deploy, deployed and cleaned DB (97 active jobs, 0 remaining noise).
**Files:** scraper/filters.py, scraper/runner.py, scraper/summarizer.py, cleanup_titles.py, Dockerfile, .env
**Decisions:** No standalone "analyst"/"analytics"/"data" — compound terms only. Company sponsorship confirmed by hiring team overrides description parsing.

### Session 4 — 2026-03-17: Cron debug + manual run
**What we did:** Diagnosed python-dotenv missing from cron environment (wrong python3 binary). Hotfixed container directly. Manual run confirmed working — 22 inserted, email received.
**Files:** Dockerfile (cron path fix committed in session 5)
**Decisions:** Always --no-cache on docker build.

### Session 1 — 2026-02-XX: Initial build
**What we did:** Built scraper, Workday + Google + AWS + Microsoft + State Farm ATS support, SQLite DB, Next.js frontend, daily email digest via Resend/SendGrid, Docker + Lightsail deploy.
**Files:** scraper/, frontend/, main.py, Dockerfile, start.sh
**Decisions:** Single container (Python + Node), persistent /data volume on Lightsail, cron at 7 AM UTC.

### Session 2 — 2026-03-14: Work auth + years experience
**What we did:** Added `deactivated_at`, fixed EY descriptions, expanded role/location filters, added 4-label `classify_work_authorization()` classifier, added `years_experience` to Claude summarizer, migration scripts, frontend filters, backfill scripts.
**Files:** scraper/filters.py, scraper/runner.py, scraper/summarizer.py, scraper/db.py, migrate_work_authorization.py, backfill_years_experience.py, frontend/
**Decisions:** OPT = current authorization, not sponsorship needed; citizen_gc_only only on explicit OPT exclusion or citizenship required.

### Session 3 — 2026-03-15: Filter false positives
**What we did:** Diagnosed post-deploy email with non-Atlanta and non-data-role jobs. Root causes: assume_atlanta bypassing is_atlanta() for Google/State Farm; broad keywords (analyst, research scientist) matching wrong roles. Fixed config.py and filters.py.
**Files:** scraper/config.py, scraper/filters.py
**Decisions:** Remove assume_atlanta from Google and State Farm; add 9 exclusion keywords.

---

## Mistakes & Lessons

### 2026-03-14 — Migration scripts not in Dockerfile
**What happened:** `migrate_work_authorization.py` and `backfill_years_experience.py` not copied in Dockerfile; `python3: can't open file` on Lightsail.
**Root cause:** Dockerfile only had COPY for scraper/, main.py, match_cv.py.
**How we fixed it:** Added explicit COPY lines for all 3 scripts.
**Lesson:** Any new root-level .py script needs a COPY line in Dockerfile.

### 2026-03-14 — Claude overrides regex, migration can't fix it
**What happened:** `migrate_work_authorization.py` re-ran regex on all jobs, but jobs with existing Claude summaries keep Claude's label (runner.py overrides regex with Claude). Migration had no effect on those jobs.
**Root cause:** Runner gives Claude label priority; migration only writes regex result unconditionally.
**Lesson:** Migration script needs to be aware of whether Claude label exists and whether to override it.

### 2026-03-15 — assume_atlanta masks non-Atlanta results
**What happened:** Google returned Cambridge MA, State Farm returned Bloomington IL — both passed location filter because assume_atlanta=True bypassed is_atlanta().
**Root cause:** assume_atlanta was a shortcut for APIs that filter at query time, but those APIs aren't strict.
**Lesson:** Only use assume_atlanta when the API genuinely guarantees Atlanta-only results AND returns no location metadata.
