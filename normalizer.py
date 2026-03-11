"""
Post-processing of raw Claude extraction results.
Handles type coercion, enum standardization, and confidence scoring.
"""

from datetime import date

from schema import (
    FIELD_NAMES, FLOAT_FIELDS, INT_FIELDS, BOOL_FIELDS,
    REQUIRED_FIELDS, CORE_FIELDS, empty_row,
)

PROPERTY_TYPE_MAP = {
    "multifamily":  "Multifamily",
    "multi-family": "Multifamily",
    "multi family": "Multifamily",
    "apartment":    "Multifamily",
    "mixed-use":    "Mixed-Use",
    "mixed use":    "Mixed-Use",
    "mixeduse":     "Mixed-Use",
    "retail":       "Retail",
    "office":       "Office",
    "industrial":   "Industrial",
    "warehouse":    "Industrial",
    "other":        "Other",
}

SALE_STATUS_MAP = {
    "asking":      "Asking",
    "active":      "Asking",
    "listed":      "Asking",
    "in contract": "In Contract",
    "contract":    "In Contract",
    "pending":     "In Contract",
    "closed":      "Closed",
    "sold":        "Closed",
}


def _coerce_float(val) -> float | None:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        cleaned = val.replace("$", "").replace(",", "").replace("%", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _coerce_int(val) -> int | None:
    f = _coerce_float(val)
    if f is None:
        return None
    return int(round(f))


def _coerce_bool(val) -> bool | None:
    if val is None:
        return None
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        lower = val.lower().strip()
        if lower in ("true", "yes", "y", "1"):
            return True
        if lower in ("false", "no", "n", "0"):
            return False
    if isinstance(val, (int, float)):
        return bool(val)
    return None


def _standardize_property_type(val: str | None) -> str | None:
    if not val:
        return None
    return PROPERTY_TYPE_MAP.get(val.lower().strip(), val)


def _standardize_sale_status(val: str | None) -> str | None:
    if not val:
        return "Asking"
    return SALE_STATUS_MAP.get(val.lower().strip(), val)


def _standardize_state(val: str | None) -> str | None:
    if not val:
        return None
    return val.strip().upper()[:2]


def _clamp_percentage(val: float | None) -> float | None:
    """Cap rates and GRMs sometimes come back as 4.9 instead of 0.049."""
    if val is None:
        return None
    # If value is > 1.0, assume it was given as a whole-number percent
    if val > 1.0:
        return val / 100.0
    return val


def _compute_confidence(row: dict) -> str:
    required_found = sum(1 for f in REQUIRED_FIELDS if row.get(f) is not None)
    core_found = sum(1 for f in CORE_FIELDS if row.get(f) is not None)
    total_found = sum(1 for v in row.values() if v is not None)

    if required_found == len(REQUIRED_FIELDS) and total_found >= 40:
        return "High"
    if required_found >= 4 and (core_found >= 10 or total_found >= 20):
        return "Medium"
    return "Low"


def normalize(raw: dict, filename: str) -> dict:
    """
    Take the raw dict from Claude, coerce all types, standardize enums,
    compute confidence, and return a clean row ready for the DataFrame.
    """
    row = empty_row()

    # Copy everything Claude returned
    for field in FIELD_NAMES:
        row[field] = raw.get(field)

    # --- Type coercions ---
    for field in FLOAT_FIELDS:
        row[field] = _coerce_float(row[field])

    for field in INT_FIELDS:
        row[field] = _coerce_int(row[field])

    for field in BOOL_FIELDS:
        row[field] = _coerce_bool(row[field])

    # --- Percentage sanity: cap rates / vacancy pct ---
    for pct_field in ("cap_rate_current", "cap_rate_proforma"):
        row[pct_field] = _clamp_percentage(row[pct_field])

    # --- Enum standardization ---
    row["property_type"] = _standardize_property_type(row.get("property_type"))
    row["sale_status"] = _standardize_sale_status(row.get("sale_status"))
    row["state"] = _standardize_state(row.get("state"))

    # --- Metadata ---
    row["source_file"] = filename
    row["extraction_date"] = date.today().isoformat()

    # --- Confidence ---
    # Claude self-reports; we also compute independently and take the worse
    claude_confidence = row.get("confidence_score") or ""
    computed = _compute_confidence(row)

    tier_rank = {"High": 2, "Medium": 1, "Low": 0, "Failed": -1}
    claude_rank = tier_rank.get(claude_confidence, 1)
    computed_rank = tier_rank.get(computed, 0)
    row["confidence_score"] = list(tier_rank.keys())[
        list(tier_rank.values()).index(min(claude_rank, computed_rank))
    ]

    # --- fields_missing: summarize null fields (excluding metadata) ---
    meta_fields = {"source_file", "extraction_date", "confidence_score", "fields_missing", "notes"}
    missing = [
        f for f in FIELD_NAMES
        if f not in meta_fields and row.get(f) is None
    ]
    # If Claude returned an array, use that; otherwise use our computed list
    raw_missing = raw.get("fields_missing")
    if isinstance(raw_missing, list):
        row["fields_missing"] = ", ".join(raw_missing)
    else:
        row["fields_missing"] = ", ".join(missing)

    return row
