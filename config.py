"""
Configuration: API key loading and app-level constants.
"""

import os
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096

# Approximate cost per million tokens (claude-sonnet-4-6 as of early 2026)
COST_PER_M_INPUT = 3.00    # USD
COST_PER_M_OUTPUT = 15.00  # USD

# PDF size limit warning threshold
PDF_SIZE_WARN_MB = 20


def get_api_key(runtime_key: str = "") -> str:
    """
    Return API key: prefer runtime key from sidebar, fall back to .env.
    Returns empty string if neither is set.
    """
    if runtime_key and runtime_key.strip():
        return runtime_key.strip()
    return os.getenv("ANTHROPIC_API_KEY", "")


def estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """Return estimated USD cost for a single API call."""
    return (input_tokens / 1_000_000 * COST_PER_M_INPUT +
            output_tokens / 1_000_000 * COST_PER_M_OUTPUT)
