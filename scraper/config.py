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
        "name": "Cisco",
        "ats": "workday",
        "tenant": "cisco",
        "wday_suffix": "wd5",
        "site": "Cisco_Careers",
    },
    {
        "name": "RaceTrac",
        "ats": "workday",
        "tenant": "racetrac",
        "wday_suffix": "wd5",
        "site": "SSC",
    },
    {
        "name": "Coca-Cola",
        "ats": "workday",
        "tenant": "coke",
        "wday_suffix": "wd1",
        "site": "coca-cola-careers",
    },
    {
        "name": "Inspire Brands",
        "ats": "workday",
        "tenant": "inspirebrands",
        "wday_suffix": "wd5",
        "site": "InspireCareers",
    },
    {
        "name": "Invesco",
        "ats": "workday",
        "tenant": "invesco",
        "wday_suffix": "wd1",
        "site": "IVZ",
    },
    {
        "name": "Veritiv",
        "ats": "workday",
        "tenant": "veritiv",
        "wday_suffix": "wd5",
        "site": "VeritivCareers",
    },
    {
        "name": "Assurant",
        "ats": "workday",
        "tenant": "assurant",
        "wday_suffix": "wd1",
        "site": "Assurant_Careers",
    },
    {
        "name": "Corpay",
        "ats": "workday",
        "tenant": "corpay",
        "wday_suffix": "wd103",
        "site": "Ext_001",
    },
    {
        "name": "Floor & Decor",
        "ats": "workday",
        "tenant": "flooranddecoroutlets",
        "wday_suffix": "wd1",
        "site": "FloorandDecorCareers",
    },
    {
        "name": "PulteGroup",
        "ats": "workday",
        "tenant": "pultegroup",
        "wday_suffix": "wd1",
        "site": "PGI",
    },
    {
        "name": "Stanley Black & Decker",
        "ats": "workday",
        "tenant": "sbdinc",
        "wday_suffix": "wd1",
        "site": "Stanley_Black_Decker_Career_Site",
    },
    {
        "name": "Circle K",
        "ats": "workday",
        "tenant": "circlek",
        "wday_suffix": "wd3",
        "site": "CircleKStoreJobs",
    },
    {
        "name": "Children's Healthcare of Atlanta",
        "ats": "workday",
        "tenant": "choa",
        "wday_suffix": "wd12",
        "site": "externalcareers",
    },
    # ── EY ───────────────────────────────────────────────────────────────
    {
        "name": "EY",
        "ats": "ey_playwright",
    },
    # ── Intuit ───────────────────────────────────────────────────────────
    {
        "name": "Intuit",
        "ats": "intuit_playwright",
    },
    # ── Avature (Playwright) ─────────────────────────────────────────────
    {
        "name": "Delta",
        "ats": "avature_playwright",
        "base_url": "https://delta.avature.net/en_US/careers/SearchJobs",
    },
    {
        "name": "Smurfit WestRock",
        "ats": "avature_playwright",
        "base_url": "https://smurfitwestrockta.avature.net/en_US/careers/SearchJobs",
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
    {
        "name": "Novelis",
        "ats": "icims_playwright",
        "base_url": "https://jobs-novelis.icims.com/jobs/search",
    },
    {
        "name": "Emory Healthcare",
        "ats": "icims_playwright",
        "base_url": "https://ehccareers-emory.icims.com/jobs/search",
    },
    {
        "name": "Emory University",
        "ats": "icims_playwright",
        "base_url": "https://staff-emory.icims.com/jobs/search",
        "assume_atlanta": True,
    },
]
