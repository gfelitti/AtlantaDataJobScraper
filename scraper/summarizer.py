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
- "salary": salary or range (string or null)
- "responsibilities": top 3-4 bullets (array of strings)
- "benefits": key benefits (array of strings, empty if none)
- "arrangement": "remote", "hybrid", "onsite", or null

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
        json.loads(text)  # validate — raises if invalid
        return text
    except Exception:
        return None
