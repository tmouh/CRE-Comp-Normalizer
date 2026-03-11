"""
Single source of truth for all comp database fields.
Every other module imports from here.
"""

import json
from collections import OrderedDict

# (field_name, python_type, description)
# python_type: str | int | float | bool | date_str
SCHEMA = OrderedDict([
    # --- Metadata ---
    ("source_file",             ("str",      "Original filename or 'pasted_text'")),
    ("extraction_date",         ("date_str", "Date extracted (YYYY-MM-DD)")),
    ("confidence_score",        ("str",      "High / Medium / Low / Failed")),
    ("fields_missing",          ("str",      "Comma-separated list of null fields")),
    ("notes",                   ("str",      "Analyst free-text notes")),

    # --- Broker ---
    ("broker_firm",             ("str",      "Brokerage name")),
    ("broker_name",             ("str",      "Lead broker(s) name")),
    ("broker_phone",            ("str",      "Broker phone number")),
    ("broker_email",            ("str",      "Broker email")),

    # --- Location ---
    ("address_full",            ("str",      "Full street address")),
    ("neighborhood",            ("str",      "Neighborhood / submarket")),
    ("city",                    ("str",      "City or borough")),
    ("state",                   ("str",      "Two-letter state code")),
    ("zip_code",                ("str",      "ZIP code")),

    # --- Property Characteristics ---
    ("property_type",           ("str",      "Multifamily | Mixed-Use | Retail | Office | Industrial | Other")),
    ("total_units",             ("int",      "Total units (residential + commercial)")),
    ("residential_units",       ("int",      "Number of residential units")),
    ("commercial_units",        ("int",      "Number of commercial/retail units")),
    ("total_sf",                ("int",      "Gross building square footage")),
    ("residential_sf",          ("int",      "Residential square footage")),
    ("commercial_sf",           ("int",      "Commercial square footage")),
    ("lot_sf",                  ("int",      "Lot area in square feet")),
    ("building_dimensions",     ("str",      "e.g. '20x70'")),
    ("lot_dimensions",          ("str",      "e.g. '20x100'")),
    ("stories",                 ("int",      "Number of stories")),
    ("year_built",              ("int",      "Year built")),
    ("zoning",                  ("str",      "Zoning designation(s)")),
    ("block",                   ("str",      "Tax block")),
    ("lot",                     ("str",      "Tax lot")),
    ("landmark",                ("bool",     "Landmark / historic district designation")),
    ("opportunity_zone",        ("bool",     "Located in Opportunity Zone")),
    ("ih_mih",                  ("bool",     "Subject to IH / MIH requirements")),

    # --- FAR / Zoning Metrics ---
    ("base_far",                ("float",    "Base floor area ratio")),
    ("air_rights_sf",           ("int",      "Unused/available air rights in SF")),

    # --- Pricing ---
    ("asking_price",            ("float",    "Asking price in dollars")),
    ("price_per_sf",            ("float",    "Asking price per SF")),
    ("price_per_unit",          ("float",    "Asking price per unit")),
    ("sale_status",             ("str",      "Asking | In Contract | Closed")),

    # --- Income: Current ---
    ("res_gpi_current",         ("float",    "Residential gross potential income (annual)")),
    ("comm_gpi_current",        ("float",    "Commercial gross potential income (annual)")),
    ("other_income_current",    ("float",    "Other income (annual)")),
    ("total_gpi_current",       ("float",    "Total gross income (annual)")),
    ("vacancy_current",         ("float",    "Vacancy/collection loss (annual, negative)")),
    ("egi_current",             ("float",    "Effective gross income (annual)")),
    ("total_expenses_current",  ("float",    "Total operating expenses (annual)")),
    ("noi_current",             ("float",    "Net operating income (annual)")),
    ("cap_rate_current",        ("float",    "Cap rate as decimal (e.g. 0.049)")),
    ("grm_current",             ("float",    "Gross rent multiplier")),

    # --- Income: Pro Forma ---
    ("res_gpi_proforma",        ("float",    "Residential GPI pro forma (annual)")),
    ("comm_gpi_proforma",       ("float",    "Commercial GPI pro forma (annual)")),
    ("other_income_proforma",   ("float",    "Other income pro forma (annual)")),
    ("total_gpi_proforma",      ("float",    "Total gross income pro forma (annual)")),
    ("vacancy_proforma",        ("float",    "Vacancy/collection loss pro forma (annual)")),
    ("egi_proforma",            ("float",    "Effective gross income pro forma (annual)")),
    ("total_expenses_proforma", ("float",    "Total expenses pro forma (annual)")),
    ("noi_proforma",            ("float",    "NOI pro forma (annual)")),
    ("cap_rate_proforma",       ("float",    "Cap rate pro forma as decimal")),
    ("grm_proforma",            ("float",    "GRM pro forma")),

    # --- Expense Line Items (Current) ---
    ("expense_taxes",           ("float",    "Property taxes (annual)")),
    ("expense_insurance",       ("float",    "Insurance (annual)")),
    ("expense_water_sewer",     ("float",    "Water and sewer (annual)")),
    ("expense_repairs_maint",   ("float",    "Repairs and maintenance (annual)")),
    ("expense_electric",        ("float",    "Common electric (annual)")),
    ("expense_super",           ("float",    "Super/janitor salary (annual)")),
    ("expense_management",      ("float",    "Management fee (annual)")),

    # --- Tax ---
    ("annual_taxes",            ("float",    "Annual property tax bill")),
    ("tax_class",               ("str",      "Tax class (e.g. '2A')")),
    ("tax_abatement",           ("str",      "Tax abatement type or 'None'")),
])

FIELD_NAMES = list(SCHEMA.keys())

# Fields that must be populated for High confidence
REQUIRED_FIELDS = [
    "address_full",
    "asking_price",
    "property_type",
    "total_units",
    "total_sf",
    "noi_current",
    "cap_rate_current",
]

# Fields commonly found even in sparse email blasts
CORE_FIELDS = [
    "address_full", "neighborhood", "city", "state",
    "property_type", "total_units", "residential_units", "commercial_units",
    "total_sf", "zoning",
    "asking_price", "price_per_sf", "price_per_unit",
    "noi_current", "cap_rate_current", "grm_current",
    "noi_proforma", "cap_rate_proforma",
    "annual_taxes", "broker_firm", "broker_name",
]

# Fields with float type (used for formatting in export)
FLOAT_FIELDS = [k for k, (t, _) in SCHEMA.items() if t == "float"]
INT_FIELDS = [k for k, (t, _) in SCHEMA.items() if t == "int"]
BOOL_FIELDS = [k for k, (t, _) in SCHEMA.items() if t == "bool"]

# Currency fields (for Excel formatting)
CURRENCY_FIELDS = [
    "asking_price", "price_per_sf", "price_per_unit",
    "res_gpi_current", "comm_gpi_current", "other_income_current", "total_gpi_current",
    "vacancy_current", "egi_current", "total_expenses_current", "noi_current",
    "res_gpi_proforma", "comm_gpi_proforma", "other_income_proforma", "total_gpi_proforma",
    "vacancy_proforma", "egi_proforma", "total_expenses_proforma", "noi_proforma",
    "expense_taxes", "expense_insurance", "expense_water_sewer", "expense_repairs_maint",
    "expense_electric", "expense_super", "expense_management",
    "annual_taxes",
]

PERCENT_FIELDS = ["cap_rate_current", "cap_rate_proforma"]


def empty_row() -> dict:
    """Return an ordered dict with all fields set to None."""
    return {field: None for field in FIELD_NAMES}


def schema_template_json() -> str:
    """
    Return a compact JSON string of {field: null} for injection into the Claude prompt.
    This anchors Claude to the exact field names and guarantees all keys are returned.
    """
    template = {field: None for field in FIELD_NAMES}
    return json.dumps(template, indent=2)
