"""
Generic PDF extractor that works on any term sheet format
"""
import pdfplumber
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class GenericPDFExtractor:
    """
    Generic PDF extractor that works on various term sheet formats
    No hardcoded assumptions about document structure
    """

    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Extract all content from PDF generically"""

        try:
            with pdfplumber.open(pdf_path) as pdf:
                all_text = ""
                all_tables = []

                logger.info(f"Processing {len(pdf.pages)} pages from {pdf_path}")

                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text content
                    text = page.extract_text() or ""
                    all_text += f"\n\n--- PAGE {page_num} ---\n{text}"

                    # Extract tables
                    tables = page.find_tables()
                    for table_idx, table in enumerate(tables):
                        try:
                            table_data = table.extract()
                            if table_data and any(any(cell for cell in row if cell) for row in table_data):
                                all_tables.append({
                                    'page': page_num,
                                    'table_index': table_idx,
                                    'data': table_data
                                })

                                # Add table content to text
                                all_text += f"\n\nTABLE {page_num}-{table_idx}:\n"
                                for row in table_data:
                                    if row and any(cell for cell in row if cell):
                                        all_text += " | ".join(str(cell or "").strip() for cell in row) + "\n"

                        except Exception as e:
                            logger.warning(f"Error extracting table {table_idx} on page {page_num}: {e}")

                return {
                    'success': True,
                    'filename': Path(pdf_path).name,
                    'text': all_text.strip(),
                    'tables': all_tables,
                    'page_count': len(pdf.pages),
                    'text_length': len(all_text)
                }

        except Exception as e:
            logger.error(f"Error extracting PDF {pdf_path}: {e}")
            return {
                'success': False,
                'filename': Path(pdf_path).name,
                'error': str(e),
                'text': '',
                'tables': []
            }

def main():
    """Test the extractor"""
    extractor = GenericPDFExtractor()

    # Test with both documents
    test_files = ["Genel-Energy.pdf", "Term-Sheet-INE008A08U84.pdf"]

    for file in test_files:
        if Path(file).exists():
            result = extractor.extract_from_pdf(file)
            print(f"\n{'='*50}")
            print(f"File: {file}")
            print(f"Success: {result['success']}")
            if result['success']:
                print(f"Pages: {result['page_count']}")
                print(f"Text length: {result['text_length']} chars")
                print(f"Tables found: {len(result['tables'])}")
                print(f"Sample text: {result['text'][:200]}...")
            else:
                print(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
