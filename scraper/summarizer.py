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
  - "opt_accepted": OPT/CPT/F-1 accepted but no H-1B sponsorship mentioned
  - "citizen_gc_only": explicitly requires U.S. citizenship or green card, or states no sponsorship/OPT
  - "not_specified": no work authorization language found

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
