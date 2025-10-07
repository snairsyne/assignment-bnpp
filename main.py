"""
Simple main script for term sheet reconciliation
Usage: python main.py <pdf_file> <booking_file>
"""
import sys
import logging
from pathlib import Path

# Import our modules
from pdf_extractor import GenericPDFExtractor
from llm_processor import SimpleLLMProcessor  
from booking_processor import BookingDataProcessor
from reconciliation import SimpleReconciliationEngine
from report_generator import SimpleReportGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main reconciliation workflow"""

    # Check command line arguments
    if len(sys.argv) != 3:
        print("Usage: python main.py <pdf_file> <booking_file>")
        print("\nExample:")
        print("  python main.py Genel-Energy.pdf Genel_Energy_Trades.json")
        print("  python main.py Term-Sheet-INE008A08U84.pdf IDBI_Omni_Trades.csv")
        sys.exit(1)

    pdf_file = sys.argv[1]
    booking_file = sys.argv[2]

    # Validate input files
    if not Path(pdf_file).exists():
        print(f"❌ PDF file not found: {pdf_file}")
        sys.exit(1)

    if not Path(booking_file).exists():
        print(f"❌ Booking file not found: {booking_file}")
        sys.exit(1)

    print("\n" + "="*70)
    print("TERM SHEET RECONCILIATION SYSTEM")
    print("="*70)
    print(f"PDF File: {pdf_file}")
    print(f"Booking File: {booking_file}")
    print("="*70)

    try:
        # Step 1: Extract content from PDF
        print("\n📄 Step 1: Extracting PDF content...")
        pdf_extractor = GenericPDFExtractor()
        pdf_result = pdf_extractor.extract_from_pdf(pdf_file)

        if not pdf_result['success']:
            print(f"❌ PDF extraction failed: {pdf_result.get('error', 'Unknown error')}")
            sys.exit(1)

        print(f"✅ Extracted {pdf_result['text_length']} characters from {pdf_result['page_count']} pages")
        if pdf_result['tables']:
            print(f"   Found {len(pdf_result['tables'])} tables")
        
        # Save extracted text to a file
        extracted_text_file = f"{Path(pdf_file).stem}_extracted_text.txt"
        with open(extracted_text_file, 'w', encoding='utf-8') as f:
            f.write(pdf_result['text'])

        print(f"📂 Extracted text saved to: {extracted_text_file}")


        # Step 2: Extract structured data using LLM
        print("\n🤖 Step 2: Extracting structured data with OpenAI...")
        llm_processor = SimpleLLMProcessor()

        if not llm_processor.client:
            print("❌ OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
            sys.exit(1)

        term_sheet_data = llm_processor.extract_term_sheet_data(
            pdf_result['text'], 
            pdf_result['filename']
        )

        if not term_sheet_data:
            print("❌ Failed to extract structured data from PDF")
            sys.exit(1)

        print("✅ Structured data extracted:")
        # for field, value in term_sheet_data.dict().items(): # Old Pydantic usage deprecated
        try:
            data_dict = term_sheet_data.model_dump()
        except AttributeError:
            data_dict = term_sheet_data.dict()

        for field, value in data_dict.items():
            if value is not None:
                print(f"   {field}: {value}")

        # Validation
        confidence = llm_processor.validate_extraction(term_sheet_data, pdf_result['text'])
        print(f"\n📊 Extraction confidence: {confidence:.1%}")

        # Step 3: Load booking data
        print("\n📋 Step 3: Loading booking data...")
        booking_processor = BookingDataProcessor()
        booking_records = booking_processor.load_booking_data(booking_file)

        if not booking_records:
            print("❌ No booking records loaded")
            sys.exit(1)

        print(f"✅ Loaded {len(booking_records)} booking records")

        summary = booking_processor.get_summary(booking_records)
        print(f"   ISINs: {summary['unique_isins']}")
        print(f"   Currencies: {summary['currencies']}")

        # Step 4: Perform reconciliation
        print("\n🔍 Step 4: Performing reconciliation...")
        reconciliation_engine = SimpleReconciliationEngine()
        results = reconciliation_engine.reconcile(term_sheet_data, booking_records, pdf_file)

        if not results:
            print("❌ No reconciliation results generated")
            sys.exit(1)

        print(f"✅ Reconciled against {len(results)} trades")

        # Step 5: Generate reports
        print("\n📊 Step 5: Generating reports...")
        report_generator = SimpleReportGenerator()

        # Generate files
        report_base = f"reconciliation_{Path(pdf_file).stem}_{Path(booking_file).stem}"
        csv_file = report_generator.generate_csv_report(results, report_base)
        md_file = report_generator.generate_markdown_report(
            results, 
            pdf_file, 
            booking_file, 
            report_base
        )

        print(f"✅ Generated reports:")
        print(f"   CSV: {csv_file}")
        print(f"   Markdown: {md_file}")

        # Print summary to console
        report_generator.print_summary(results)

        print("\n✅ Reconciliation completed successfully!")

    except KeyboardInterrupt:
        print("\n❌ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
