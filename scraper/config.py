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
    {
        "name": "Cardlytics",
        "ats": "workday",
        "tenant": "cardlytics",
        "wday_suffix": "wd5",
        "site": "CardlyticsExternalCareerSite",
    },
    {
        "name": "Manhattan Associates",
        "ats": "workday",
        "tenant": "manh",
        "wday_suffix": "wd5",
        "site": "External",
    },
    {
        "name": "Global Payments",
        "ats": "workday",
        "tenant": "tsys",
        "wday_suffix": "wd1",
        "site": "TSYS",
    },
    {
        "name": "Warner Bros. Discovery",
        "ats": "workday",
        "tenant": "warnerbros",
        "wday_suffix": "wd5",
        "site": "global",
    },
    {
        "name": "UPS",
        "ats": "workday",
        "tenant": "hcmportal",
        "wday_suffix": "wd5",
        "site": "Search",
    },
    {
        "name": "Fiserv",
        "ats": "workday",
        "tenant": "fiserv",
        "wday_suffix": "wd5",
        "site": "EXT",
    },
    {
        "name": "NCR Atleos",
        "ats": "workday",
        "tenant": "ncratleos",
        "wday_suffix": "wd1",
        "site": "ext_atleos_us",
    },
    {
        "name": "Salesforce",
        "ats": "workday",
        "tenant": "salesforce",
        "wday_suffix": "wd12",
        "site": "External_Career_Site",
    },
    {
        "name": "RaceTrac",
        "ats": "workday",
        "tenant": "racetrac",
        "wday_suffix": "wd5",
        "site": "SSC",
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
