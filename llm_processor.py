"""
Simple LLM processor using OpenAI for structured extraction
"""
import openai
import json
import logging
from typing import Optional
from data_models import TermSheetData
import config

logger = logging.getLogger(__name__)

class SimpleLLMProcessor:
    """Simple LLM processor using OpenAI API"""

    def __init__(self):
        if not config.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not found in environment")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)

    def extract_term_sheet_data(self, text: str, filename: str = "") -> Optional[TermSheetData]:
        """Extract structured data from term sheet text using OpenAI"""

        if not self.client:
            logger.error("OpenAI client not initialized")
            return None

        # TODO: move prompts to 'prompts.json' and read from there
        prompt = f"""
You are a financial document analyst. Extract key information from this bond/debt term sheet.

Document: {filename}

Extract the following fields and return them as a FLAT JSON object (not nested):

- isin: ISIN code (e.g., NO0010894330, INE008A08U84)
- issuer: Name of the issuing entity/company/bank
- issue_amount: Total issuance size (number only)
- face_value: Nominal/face value per bond unit (number only)
- notional_amount: Total notional amount (if specified, otherwise null)
- coupon_rate: Interest rate as decimal number (e.g., 9.25 for 9.25%)
- currency: Currency code (USD, INR, EUR, etc.)
- issue_date: Issue date in YYYY-MM-DD format
- maturity_date: Maturity date in YYYY-MM-DD format (null for perpetual)
- settlement_date: Settlement date in YYYY-MM-DD format
- payment_frequency: Interest payment frequency (e.g., "Semi-annual")
- day_count_convention: Day count method (e.g., "30/360")
- security_type: Security status (e.g., "Unsecured")
- seniority: Ranking (e.g., "Senior")
- tenor: Bond tenor/term (e.g., "5 years")

IMPORTANT:
1. Return a FLAT JSON object with these exact field names
2. Do NOT nest the fields under category headers
3. Use null for missing values
4. Extract only numbers for amounts and rates (no currency symbols or %)

Example format:
{{
    "isin": "NO0010894330",
    "issuer": "Company Name",
    "coupon_rate": 9.25,
    "currency": "USD",
    ...
}}

Document content:
{text[:12000]}
"""
        try:
            logger.info(f"Sending text to OpenAI for extraction: {len(text)} characters")

            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a financial document analyst specializing in bond term sheets. Extract information accurately and return valid JSON only. Be flexible in recognizing field names and their synonyms."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Changed from 0.1 to 0.0 for more consistent extraction
                max_tokens=1500
            )

            response_text = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response received: {len(response_text)} characters")

            # DEBUG: Log the raw response
            logger.debug(f"Raw OpenAI response:\n{response_text}")
            print(f"\n DEBUG - Raw OpenAI Response:\n{response_text}\n")

            # Parse JSON response
            if response_text.startswith('```json'):
                response_text = response_text.strip('```json').strip('```').strip()
            elif response_text.startswith('```'):
                response_text = response_text.strip('```').strip()

            try:
                data = json.loads(response_text)

                # FIX: Flatten nested structure if present
                if self._is_nested_structure(data):
                    logger.info("Detected nested structure, flattening...")
                    data = self._flatten_nested_json(data)
                    print(f"\n🔧 Flattened JSON:\n{json.dumps(data, indent=2)}\n")

                # DEBUG: Log parsed data
                logger.debug(f"Parsed JSON data: {data}")
                print(f"\n DEBUG - Parsed JSON:\n{json.dumps(data, indent=2)}\n")

                term_sheet_data = TermSheetData(**data)
                logger.info(f"Successfully extracted term sheet data")
                return term_sheet_data

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.debug(f"Response text: {response_text}")
                print(f"\n JSON Parse Error: {e}")
                print(f"Response was: {response_text}")
                return None

        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            print(f"\n API Error: {e}")
            return None

    def validate_extraction(self, data: TermSheetData, original_text: str) -> float:
        """Simple validation by checking if extracted values appear in original text"""

        if not data:
            return 0.0

        score = 0.0
        checks = 0

        # Check ISIN
        if data.isin and data.isin in original_text:
            score += 1
        checks += 1

        # Check issuer (partial match)
        if data.issuer:
            issuer_words = data.issuer.split()[:2]  # First 2 words
            if any(word.lower() in original_text.lower() for word in issuer_words if len(word) > 3):
                score += 1
        checks += 1

        # Check coupon rate
        if data.coupon_rate:
            coupon_patterns = [
                f"{data.coupon_rate}%",
                f"{data.coupon_rate:.2f}%",
                f"{data.coupon_rate:.1f}%",
                str(data.coupon_rate)
            ]
            if any(pattern in original_text for pattern in coupon_patterns):
                score += 1
        checks += 1

        # Check currency
        if data.currency and data.currency in original_text:
            score += 1
        checks += 1

        return score / checks if checks > 0 else 0.0
    
    def _is_nested_structure(self, data: dict) -> bool:
        """Check if JSON has nested category structure"""
        # Check if top-level keys are category names (all caps)
        category_keys = ['IDENTIFIERS', 'FINANCIAL TERMS', 'DATES', 'PAYMENT TERMS', 'BOND CHARACTERISTICS']
        return any(key in data for key in category_keys)

    def _flatten_nested_json(self, data: dict) -> dict:
        """Flatten nested JSON structure"""
        flattened = {}
        for key, value in data.items():
            if isinstance(value, dict):
                # Merge nested dictionaries into flat structure
                flattened.update(value)
            else:
                flattened[key] = value
        return flattened

def main():
    """Test the LLM processor"""

    processor = SimpleLLMProcessor()

    if not processor.client:
        print("❌ OpenAI API key not configured")
        print("Set OPENAI_API_KEY environment variable to test")
        return

    # Sample text from IDBI document
    sample_text = """
    Term Sheet
    Security Name: IDBI Omni Additional Tier 1 Bond 2014-15 Series II
    Issuer: IDBI Bank Limited
    Issue Size: Rs.1,500 Crores with an option to retain over subscription up to Rs.1,000 Crores
    Coupon Rate: 10.75% p.a.
    Face Value: Rs.10,00,000/- (Rupees Ten Lakh) per Bond
    Tenor: Perpetual
    Currency: INR
    """

    result = processor.extract_term_sheet_data(sample_text, "test_document.pdf")

    if result:
        print("✅ Extraction successful:")
        for field, value in result.dict().items():
            if value is not None:
                print(f"  {field}: {value}")

        # Test validation
        confidence = processor.validate_extraction(result, sample_text)
        print(f"\nValidation confidence: {confidence:.1%}")
    else:
        print("❌ Extraction failed")

if __name__ == "__main__":
    main()
