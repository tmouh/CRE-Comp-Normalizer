"""
Claude API extraction logic.
Sends PDF bytes or plain text to Claude and returns a raw dict matching the schema.
"""

import base64
import json
import re
import anthropic

from config import MODEL, MAX_TOKENS
from schema import schema_template_json, FIELD_NAMES

SYSTEM_PROMPT = """You are a commercial real estate data extraction specialist.
Your job is to read broker offering memoranda, email blasts, and marketing materials
and extract structured property and financial data into a precise JSON format.

RULES:
1. Extract data EXACTLY as stated in the document. Do not calculate or derive fields.
2. Numeric fields: return a raw number only — no $, commas, %, or units.
   Example: "$5,000,000" → 5000000 | "4.9%" → 0.049 | "5,000 SF" → 5000
3. Percentages become decimals: 4.9% → 0.049, 5.7% → 0.057
4. Boolean fields: return true, false, or null if not mentioned.
5. If a field is not present in the document, return null. NEVER invent or estimate.
6. Standardize property_type to exactly one of:
   Multifamily | Mixed-Use | Retail | Office | Industrial | Other
7. Standardize state to two-letter uppercase code (e.g. "NY", "NJ").
8. sale_status: use "Asking" unless document states "In Contract" or "Closed".
9. vacancy fields are negative dollar amounts (e.g. -6179 not 6179).
10. For fields_missing: return an array of field names (strings) that are null.
11. For confidence_score: return "High" if >85% of fields populated,
    "Medium" if 50-85%, "Low" if <50%.
12. Return ONLY valid JSON — no markdown code fences, no prose, no explanation."""

USER_PROMPT_PDF = """Extract all available data from this commercial real estate document
and return it as a single JSON object matching EXACTLY this schema (all keys required,
use null for missing values):

{schema}

Focus especially on:
- The "Property Snapshot" or summary box for property details
- The income/expense table for all financial fields (current and pro forma)
- Unit rent roll for residential/commercial SF and unit counts
- Broker names, firm, and phone numbers in headers/footers
- Zoning flags: Landmark, Opportunity Zone, IH/MIH

Document source: {filename}

Return the JSON object now."""

USER_PROMPT_TEXT = """Extract all available data from this broker email/blast
and return it as a single JSON object matching EXACTLY this schema (all keys required,
use null for missing values):

{schema}

The text below was pasted from a broker email or marketing blast:

---
{text}
---

Return the JSON object now."""


def _parse_json(raw: str) -> dict:
    """Attempt to parse JSON, stripping markdown fences if present."""
    cleaned = raw.strip()
    # Strip ```json ... ``` or ``` ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def _validate_keys(data: dict) -> dict:
    """Ensure all schema keys are present; fill any missing ones with None."""
    for field in FIELD_NAMES:
        if field not in data:
            data[field] = None
    return data


def extract_from_pdf(
    pdf_bytes: bytes,
    filename: str,
    api_key: str,
) -> tuple[dict, int, int]:
    """
    Send a PDF to Claude and return (extracted_dict, input_tokens, output_tokens).
    Raises on unrecoverable API errors.
    """
    client = anthropic.Anthropic(api_key=api_key)
    b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")
    user_prompt = USER_PROMPT_PDF.format(
        schema=schema_template_json(),
        filename=filename,
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": b64,
                    },
                },
                {"type": "text", "text": user_prompt},
            ],
        }],
    )

    raw_text = response.content[0].text
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    try:
        data = _parse_json(raw_text)
    except json.JSONDecodeError:
        # Retry: ask for clean JSON only
        retry_response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": user_prompt},
                    ],
                },
                {"role": "assistant", "content": raw_text},
                {
                    "role": "user",
                    "content": "Your response was not valid JSON. Return only the raw JSON object, no markdown, no explanation.",
                },
            ],
        )
        raw_text = retry_response.content[0].text
        input_tokens += retry_response.usage.input_tokens
        output_tokens += retry_response.usage.output_tokens
        data = _parse_json(raw_text)

    return _validate_keys(data), input_tokens, output_tokens


def extract_from_text(
    text: str,
    source_label: str,
    api_key: str,
) -> tuple[dict, int, int]:
    """
    Send pasted text to Claude and return (extracted_dict, input_tokens, output_tokens).
    """
    client = anthropic.Anthropic(api_key=api_key)
    user_prompt = USER_PROMPT_TEXT.format(
        schema=schema_template_json(),
        text=text,
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        temperature=0,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = response.content[0].text
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    try:
        data = _parse_json(raw_text)
    except json.JSONDecodeError:
        retry_response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": raw_text},
                {
                    "role": "user",
                    "content": "Your response was not valid JSON. Return only the raw JSON object, no markdown, no explanation.",
                },
            ],
        )
        raw_text = retry_response.content[0].text
        input_tokens += retry_response.usage.input_tokens
        output_tokens += retry_response.usage.output_tokens
        data = _parse_json(raw_text)

    return _validate_keys(data), input_tokens, output_tokens
