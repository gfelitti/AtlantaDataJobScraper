"""
Email digest: sends an HTML summary of newly inserted jobs via Resend.

Required env vars:
    RESEND_API_KEY      — Resend API key
    EMAIL_FROM          — verified sender address
    RESEND_AUDIENCE_ID  — Resend Audience ID; recipients fetched from this list
"""

import logging
import os
from datetime import date

logger = logging.getLogger(__name__)


def _build_html(new_jobs_by_company: dict[str, list[dict]], run_date: str) -> str:
    total = sum(len(jobs) for jobs in new_jobs_by_company.values())

    rows_html = ""
    for company, jobs in sorted(new_jobs_by_company.items()):
        for job in jobs:
            location = job.get("location") or "—"
            posted = job.get("posted_date") or "—"
            url = job.get("url") or "#"
            title = job.get("title", "Untitled")
            rows_html += f"""
            <tr>
              <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0;font-weight:600;color:#1a1a1a">{company}</td>
              <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0">
                <a href="{url}" style="color:#2563eb;text-decoration:none">{title}</a>
              </td>
              <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0;color:#555;white-space:nowrap">{location}</td>
              <td style="padding:10px 12px;border-bottom:1px solid #f0f0f0;color:#888;white-space:nowrap">{posted}</td>
            </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>JobScraper Daily Digest</title>
</head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f5f5;padding:32px 0">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,.08)">

        <!-- Header -->
        <tr>
          <td style="background:#1e3a5f;padding:28px 32px">
            <p style="margin:0;font-size:13px;color:#93c5fd;letter-spacing:.05em;text-transform:uppercase">Atlanta Data Jobs</p>
            <h1 style="margin:6px 0 0;font-size:22px;color:#ffffff;font-weight:700">Daily Digest — {run_date}</h1>
          </td>
        </tr>

        <!-- Summary -->
        <tr>
          <td style="padding:20px 32px;border-bottom:2px solid #f0f0f0">
            <p style="margin:0;font-size:15px;color:#444">
              <strong style="color:#1e3a5f;font-size:28px">{total}</strong>
              &nbsp;new data role{'' if total == 1 else 's'} found across
              <strong>{len(new_jobs_by_company)}</strong> {'company' if len(new_jobs_by_company) == 1 else 'companies'}.
            </p>
          </td>
        </tr>

        <!-- Table -->
        <tr>
          <td style="padding:24px 32px">
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse">
              <thead>
                <tr style="background:#f8fafc">
                  <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.06em;border-bottom:2px solid #e2e8f0">Company</th>
                  <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.06em;border-bottom:2px solid #e2e8f0">Role</th>
                  <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.06em;border-bottom:2px solid #e2e8f0">Location</th>
                  <th style="padding:10px 12px;text-align:left;font-size:11px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.06em;border-bottom:2px solid #e2e8f0">Posted</th>
                </tr>
              </thead>
              <tbody>{rows_html}
              </tbody>
            </table>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:20px 32px;background:#f8fafc;border-top:1px solid #e2e8f0">
            <p style="margin:0;font-size:12px;color:#94a3b8;text-align:center">
              Atlanta Data Job Scraper &mdash; automated digest
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _get_audience_recipients(resend, api_key: str, audience_id: str) -> list[str]:
    """Fetch subscribed contacts from a Resend Audience."""
    resend.api_key = api_key
    try:
        response = resend.Contacts.list(audience_id=audience_id)
        contacts = response.get("data", [])
        emails = [c["email"] for c in contacts if not c.get("unsubscribed", False)]
        logger.info("Fetched %d subscribed contacts from audience %s", len(emails), audience_id)
        return emails
    except Exception as exc:
        logger.error("Failed to fetch audience contacts: %s", exc)
        return []


def send_digest(new_jobs_by_company: dict[str, list[dict]]) -> bool:
    """
    Send the daily digest email. Returns True on success.
    Recipients are fetched from RESEND_AUDIENCE_ID.
    Falls back to EMAIL_TO if RESEND_AUDIENCE_ID is not set.
    """
    api_key = os.environ.get("RESEND_API_KEY", "")
    email_from = os.environ.get("EMAIL_FROM", "")
    audience_id = os.environ.get("RESEND_AUDIENCE_ID", "")
    email_to_raw = os.environ.get("EMAIL_TO", "")

    if not all([api_key, email_from]):
        logger.info("Email digest skipped: RESEND_API_KEY / EMAIL_FROM not configured.")
        return False

    total = sum(len(jobs) for jobs in new_jobs_by_company.values())
    if total == 0:
        logger.info("Email digest skipped: no new jobs.")
        return False

    try:
        import resend
    except ImportError:
        logger.error("resend package not installed. Run: pip install resend")
        return False

    if audience_id:
        recipients = _get_audience_recipients(resend, api_key, audience_id)
    else:
        recipients = [e.strip() for e in email_to_raw.split(",") if e.strip()]

    if not recipients:
        logger.warning("Email digest skipped: no recipients.")
        return False

    run_date = date.today().strftime("%B %d, %Y")
    html = _build_html(new_jobs_by_company, run_date)
    subject = f"JobScraper: {total} new data role{'s' if total != 1 else ''} — {run_date}"

    try:
        resend.api_key = api_key
        resend.Emails.send({
            "from": email_from,
            "to": recipients,
            "subject": subject,
            "html": html,
        })
        logger.info("Digest sent to %d recipients", len(recipients))
        return True
    except Exception as exc:
        logger.error("Failed to send digest: %s", exc)
        return False
