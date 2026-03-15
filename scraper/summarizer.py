import json
import os

import anthropic

_CLIENT = None


def _client() -> anthropic.Anthropic:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
    return _CLIENT


SYSTEM = "Return ONLY valid JSON, no markdown, no explanation."

PROMPT = """Extract from this job posting and return a JSON object with exactly these fields:
- "experience": required years + key skills (string or null)
- "years_experience": minimum years of experience required as an integer (e.g. 3), or null if not specified
- "salary": salary or range (string or null)
- "responsibilities": top 3-4 bullets (array of strings)
- "benefits": key benefits (array of strings, empty if none)
- "arrangement": "remote", "hybrid", "onsite", or null
- "work_authorization": one of "sponsorship_provided", "opt_accepted", "citizen_gc_only", "not_specified"
  - "sponsorship_provided": company explicitly offers H-1B or visa sponsorship
  - "opt_accepted": company will NOT sponsor H-1B/visas but does NOT explicitly exclude OPT/CPT — candidates on OPT are currently authorized to work and do not require sponsorship, so they qualify. Examples: "will not offer sponsorship", "must be currently authorized to work", "does not sponsor employment visas"
  - "citizen_gc_only": explicitly excludes OPT/CPT, OR requires U.S. citizenship or permanent residency, OR requires unrestricted/permanent work authorization. Examples: "no OPT", "no CPT", "must be a U.S. citizen", "U.S. persons only", "unrestricted work authorization required"
  - "not_specified": no work authorization language found
  IMPORTANT: "will not sponsor" or "must be currently authorized" WITHOUT explicitly saying "no OPT/CPT" should be "opt_accepted", not "citizen_gc_only". OPT holders ARE currently authorized to work.

Job: {title} at {company}
---
{description}"""


def summarize(title: str, company: str, description: str) -> str | None:
    try:
        msg = _client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=SYSTEM,
            messages=[{"role": "user", "content": PROMPT.format(
                title=title, company=company, description=description[:8000]
            )}],
        )
        text = msg.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        json.loads(text)  # validate — raises if invalid
        return text
    except Exception:
        return None
