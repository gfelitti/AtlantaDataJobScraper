"""
Company registry and keyword configuration.
Add a new company by appending one dict to COMPANIES.

Workday dict keys: name, ats, tenant, wday_suffix, site
Avature dict keys: name, ats, base_url
Generic dict keys: name, ats, base_url
"""

COMPANIES: list[dict] = [
    # ── Workday ──────────────────────────────────────────────────────────
    {
        "name": "Home Depot",
        "ats": "workday",
        "tenant": "homedepot",
        "wday_suffix": "wd5",
        "site": "CareerDepot",
    },
    {
        "name": "Truist",
        "ats": "workday",
        "tenant": "truist",
        "wday_suffix": "wd1",
        "site": "Careers",
    },
    {
        "name": "Cox Enterprises",
        "ats": "workday",
        "tenant": "cox",
        "wday_suffix": "wd1",
        "site": "Cox_External_Career_Site_1",
    },
    {
        "name": "NCR Voyix",
        "ats": "workday",
        "tenant": "ncr",
        "wday_suffix": "wd1",
        "site": "ext_us",
    },
    {
        "name": "Equifax",
        "ats": "workday",
        "tenant": "equifax",
        "wday_suffix": "wd5",
        "site": "External",
    },
    {
        "name": "Carter's",
        "ats": "workday",
        "tenant": "carters",
        "wday_suffix": "wd1",
        "site": "CartersCareers",
    },
    {
        "name": "Genuine Parts",
        "ats": "workday",
        "tenant": "genpt",
        "wday_suffix": "wd1",
        "site": "Careers",
    },
    # ── Avature (Playwright) ─────────────────────────────────────────────
    {
        "name": "Delta",
        "ats": "avature_playwright",
        "base_url": "https://delta.avature.net/en_US/careers/SearchJobs",
    },
    # ── iCIMS (Playwright) ───────────────────────────────────────────────
    {
        "name": "Chick-fil-A",
        "ats": "icims_playwright",
        "base_url": "https://careers-chickfila.icims.com/jobs/search",
    },
    {
        "name": "ICE",
        "ats": "icims_playwright",
        "base_url": "https://careers-ice.icims.com/jobs/search",
    },
]
