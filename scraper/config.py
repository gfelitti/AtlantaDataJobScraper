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
        "name": "Chick-fil-A",
        "ats": "workday",
        "tenant": "cfa",
        "wday_suffix": "wd5",
        # NOTE: "Assignments" is the only confirmed public Workday site for CFA.
        # It may be scoped to Field Talent Staff postings, not corporate roles.
        "site": "Assignments",
    },
    # ── Avature ──────────────────────────────────────────────────────────
    {
        "name": "Delta",
        "ats": "avature",
        "base_url": "https://delta.avature.net/en_US/careers/SearchJobs",
    },
    # ── Generic (iCIMS) ──────────────────────────────────────────────────
    {
        "name": "ICE",
        "ats": "generic",
        "base_url": "https://careers.ice.com/jobs",
    },
]
