# Assignment BNPP - Term Sheet Reconciliation System

A lightweight, generic solution for reconciling term sheet data with booking records using LLM-powered extraction.

## 🎯 Problem Statement

Automatically extract key financial data from PDF term sheets and reconcile against booking system records to identify matches and mismatches in bond instrument characteristics.

## ⚡ Key Features

- **Generic PDF Parsing**: Works with any term sheet format without hardcoding document structure
- **LLM-Powered Extraction**: Uses OpenAI GPT-4o for intelligent structured data extraction
- **Dynamic Field Mapping**: Automatically matches fields across different booking data formats
- **Flexible Comparison Logic**: Configurable tolerance for dates and numeric values
- **Field-by-Field Reconciliation**: Clear identification of mismatches with similarity scoring
- **Multiple Output Formats**: CSV and Markdown reports for different use cases

## 📋 Setup

### Prerequisites
- Python 3.10+
- OpenAI API key

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## 🚀 Usage

### Basic Command
```bash
python main.py <pdf_file> <booking_file>
```

### Parameters
- `pdf_file`: Path to the term sheet PDF
- `booking_file`: Path to the booking data JSON file

### Example Commands
```bash
# Example 1
python main.py data/Genel/Genel-Energy.pdf data/Genel/Genel_Energy_Trades.json

# Example 2
python main.py "data/IDBI/Term Sheet - INE008A08U84.pdf" data/IDBI/IDBI_Omni_Trades.json
```

## 📊 Fields Extracted

The system extracts the following bond characteristics from term sheets:

### Core Identifiers
- ISIN code
- Issuer name

### Financial Terms
- Issue amount (total size)
- Face value (per bond)
- Coupon rate
- Currency

### Dates
- Issue date
- Maturity date
- Settlement date

### Payment Terms
- Payment frequency (e.g., Semi-annual, Annual)
- Day count convention (e.g., 30/360, Actual/Actual)

### Bond Characteristics
- Security type (e.g., Unsecured, Secured)
- Seniority (e.g., Senior, Subordinated)
- Tenor (e.g., 5 years, Perpetual)

## 🔧 Configuration

### Settings (config.py)
```python
# Reconciliation tolerances
DATE_TOLERANCE_DAYS = 0      # 0 = exact date matching (recommended)
NUMERIC_TOLERANCE = 0.001    # 0.1% tolerance for numeric comparisons

# OpenAI configuration
OPENAI_MODEL = "gpt-4o"      # Model used for extraction
OPENAI_MAX_TOKENS = 1500     # Max tokens for response
```

### Field Mapping Strategy
The system uses intelligent field mapping to handle different naming conventions:
- Multiple possible names per field (e.g., `Coupon`, `CouponRate`, `InterestRate`)
- Automatic field discovery from booking data
- Graceful handling of missing fields

## 📈 Output Files

The system generates three types of outputs:

### 1. Extracted Text
- **File**: `<PDF_filename>_extracted_text.txt`
- **Content**: Raw extracted text from PDF for reference

### 2. CSV Report
- **File**: `outputs/reconciliation_<PDF>_<Booking>.csv`
- **Content**: Detailed field-by-field comparison data
- **Use Case**: Data analysis, import into other systems

### 3. Markdown Report
- **File**: `outputs/reconciliation_<PDF>_<Booking>.md`
- **Content**: Human-readable reconciliation results
- **Use Case**: Review, documentation, sharing with stakeholders

### 4. Console Output
- **Real-time progress** through all processing steps
- **Summary statistics** (total trades, perfect matches, success rate)
- **Detailed breakdown** of mismatches per trade

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PDF File      │───▶│ Generic PDF     │───▶│ OpenAI LLM      │
│ (Any format)    │    │ Extractor       │    │ Processor       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐             │
│ Reports         │◀───│ Reconciliation  │◀────────────┘
│ (CSV/Markdown)  │    │ Engine          │             
└─────────────────┘    └─────────────────┘             
                                ▲                       
                                │                       
                       ┌─────────────────┐              
                       │ Booking Data    │              
                       │ Processor       │              
                       │ (JSON)          │              
                       └─────────────────┘              
```

## 🔧 Technical Components

### Core Modules

| Module | Purpose | Key Features |
|--------|---------|--------------|
| `pdf_extractor.py` | PDF content extraction | PyMuPDF-based, table detection, text extraction |
| `llm_processor.py` | LLM data extraction | OpenAI API integration, structured JSON output, error handling |
| `booking_processor.py` | Booking data loading | JSON parsing, Pydantic validation |
| `reconciliation.py` | Field comparison | Dynamic field mapping, tolerance handling, similarity scoring |
| `report_generator.py` | Report generation | CSV/Markdown formatting, summary statistics |
| `data_models.py` | Data structures | Type-safe Pydantic models |
| `config.py` | Configuration | Centralized settings management |
| `main.py` | Orchestration | CLI interface, workflow coordination |

## 📐 Design Principles

### 1. Generic Document Handling
- No hardcoded assumptions about document structure
- Works with any term sheet format
- Relies on LLM intelligence for extraction

### 2. Dynamic Field Mapping
Instead of static mappings, the system:
- Inspects booking data structure at runtime
- Tries multiple field name variations
- Handles missing fields gracefully

Example:
```python
'face_value': ['NominalAmountPerBond', 'FaceValue', 'Denomination', 'ParValue']
```

### 3. Term Sheet vs Trade-Specific Data
**What we reconcile:**
- ✅ Bond instrument characteristics (from term sheet)
- ✅ Fields that should match across all trades

**What we don't reconcile:**
- ❌ Trade-specific position sizes (Notional amounts)
- ❌ Fields not present in term sheets

**Rationale:** This is a term sheet reconciliation system, not a trade booking validation system. Each booking may have different position sizes, which is normal and expected.

### 4. Configurable Tolerances
- **Date tolerance**: Set to 0 for exact matching (recommended for financial instruments)
- **Numeric tolerance**: 0.1% default for floating-point comparisons
- Easily adjustable in `config.py`

### 5. Error Handling
- Graceful degradation when fields are missing
- Clear error messages for troubleshooting
- Debug mode for LLM extraction issues

## 🧪 Validation Features

### Extraction Confidence Score
The system calculates a confidence score based on:
- Number of successfully extracted fields
- Presence of key identifiers (ISIN, Issuer)
- Completeness of data

### Reconciliation Metrics
- **Match Percentage**: Per-trade field match rate
- **Perfect Match**: All compared fields match
- **Success Rate**: Overall percentage of perfect matches
- **Field Similarity**: Numeric similarity scores (0.0 to 1.0)

### Mismatch Detection
- Exact value comparison for strings
- Tolerance-based comparison for numbers and dates
- Clear notes explaining differences

## 📂 Project Structure

```
bnpp_assignment_reconcilliation_3/
├── main.py                      # CLI orchestration
├── config.py                    # Configuration settings
├── data_models.py               # Pydantic models
├── pdf_extractor.py             # PDF extraction
├── llm_processor.py             # LLM integration
├── booking_processor.py         # JSON processing
├── reconciliation.py            # Comparison engine
├── report_generator.py          # Report generation
├── requirements.txt             # Dependencies
├── README.md                    # This file
├── SAMPLE_OUTPUTS.md            # Sample run results
├── .env.example                 # Environment template
├── data/                        # Sample input data
│   ├── Genel/
│   └── IDBI/
└── outputs/                     # Generated reports
```

## 🐛 Known Limitations

1. **LLM Dependency**: Requires OpenAI API access and credits
2. **Perpetual Bonds**: May not have issue/maturity dates to extract
3. **Field Name Variations**: May need to extend mappings for new formats
4. **PDF Quality**: Works best with text-based PDFs (not scanned images)

## 🔮 Future Enhancements

- [ ] Support for multiple LLM providers (Anthropic, local models)
- [ ] CSV booking data format support
- [ ] Configurable field mappings via external YAML/JSON
- [ ] Batch processing of multiple term sheets
- [ ] Web UI for easier operation
- [ ] Integration with booking systems via REST API
- [ ] OCR support for scanned documents
- [ ] Multi-language support

## 🤝 Assignment Compliance

✅ **Automated Document Parsing**: Generic PDF extraction works on any format  
✅ **LLM Integration**: OpenAI API with structured JSON outputs  
✅ **Booking Data Processing**: JSON support with dynamic field mapping  
✅ **Reconciliation Logic**: Clear field-by-field comparison with configurable tolerance  
✅ **Output Generation**: Business-useful CSV and Markdown reports  
✅ **Code Quality**: Clean, modular design with error handling and type safety  
✅ **Extensibility**: Easy to adapt to new document types and booking formats

## 📚 Additional Documentation

- **Sample Outputs**: See `SAMPLE_OUTPUTS.md` for example reconciliation results
- **API Documentation**: Run `python -m pydoc <module_name>` for module details
- **Configuration Guide**: See comments in `config.py` for all settings

## 📝 License

This is an assignment project for BNP Paribas interview purposes.

---

**Note**: This system reconciles **bond instrument characteristics** from term sheets against booking records. Individual trade positions (notional amounts) are not compared as they vary per booking.
