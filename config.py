"""
Simple configuration for Term Sheet Reconciliation
"""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Core fields to extract (works for both datasets)
CORE_EXTRACTION_FIELDS = [
    "isin",
    "issuer",
    "coupon_rate",
    "currency",
    "issue_amount",
    "face_value",
    "issue_date",
    "maturity_date"
]

# Comparison tolerances
NUMERIC_TOLERANCE = 0.001  # 0.1% tolerance
SIMILARITY_THRESHOLD = 0.85
DATE_TOLERANCE_DAYS = 0  # 0 days - for exact match

# Output settings
OUTPUT_DIR = "outputs"
