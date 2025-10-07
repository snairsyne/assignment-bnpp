"""
Simple report generator for reconciliation results
"""
import csv
import logging
from pathlib import Path
from typing import List
from data_models import ReconciliationResult
import config

logger = logging.getLogger(__name__)

class SimpleReportGenerator:
    """Simple report generator for reconciliation results"""

    def __init__(self, output_dir: str = config.OUTPUT_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_csv_report(self, 
                           results: List[ReconciliationResult],
                           filename: str = "reconciliation_report") -> str:
        """Generate CSV reconciliation report"""

        csv_path = self.output_dir / f"{filename}.csv"

        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)

                # Header row
                writer.writerow([
                    'Trade_ID',
                    'Overall_Match',
                    'Match_Percentage',
                    'Field_Name',
                    'Term_Sheet_Value',
                    'Booking_Value',
                    'Field_Match',
                    'Similarity',
                    'Notes'
                ])

                # Data rows
                for result in results:
                    for comparison in result.comparisons:
                        writer.writerow([
                            result.trade_id or '',
                            'YES' if result.overall_match else 'NO',
                            f"{result.match_percentage:.1f}%",
                            comparison.field_name,
                            comparison.term_sheet_value or '',
                            comparison.booking_value or '',
                            'YES' if comparison.match else 'NO',
                            f"{comparison.similarity:.3f}",
                            comparison.notes or ''
                        ])

            logger.info(f"Generated CSV report: {csv_path}")
            return str(csv_path)

        except Exception as e:
            logger.error(f"Error generating CSV report: {e}")
            raise

    def generate_markdown_report(self, 
                                results: List[ReconciliationResult],
                                term_sheet_file: str = "",
                                booking_file: str = "",
                                filename: str = "reconciliation_report") -> str:
        """Generate Markdown reconciliation report"""

        md_path = self.output_dir / f"{filename}.md"

        try:
            with open(md_path, 'w', encoding='utf-8') as f:
                # Header
                f.write("# Term Sheet Reconciliation Report\n\n")
                if term_sheet_file:
                    f.write(f"**Term Sheet:** {term_sheet_file}\n")
                if booking_file:
                    f.write(f"**Booking Data:** {booking_file}\n")
                f.write(f"**Total Trades:** {len(results)}\n\n")

                # Summary
                perfect_matches = len([r for r in results if r.overall_match])
                f.write("## Summary\n\n")
                f.write(f"- **Perfect Matches:** {perfect_matches}/{len(results)}\n")
                f.write(f"- **Success Rate:** {perfect_matches/len(results)*100:.1f}%\n\n")

                # Trade-by-trade results
                f.write("## Trade Results\n\n")

                for result in results:
                    status = "✅" if result.overall_match else "❌"
                    f.write(f"### Trade {result.trade_id} {status}\n\n")
                    f.write(f"{result.summary}\n\n")

                    # Field comparison table
                    f.write("| Field | Term Sheet | Booking System | Match | Notes |\n")
                    f.write("|-------|------------|----------------|-------|-------|\n")

                    for comp in result.comparisons:
                        match_icon = "✅" if comp.match else "❌"
                        f.write(f"| {comp.field_name} | {comp.term_sheet_value or 'N/A'} | {comp.booking_value or 'N/A'} | {match_icon} | {comp.notes or ''} |\n")

                    f.write("\n")

            logger.info(f"Generated Markdown report: {md_path}")
            return str(md_path)

        except Exception as e:
            logger.error(f"Error generating Markdown report: {e}")
            raise

    def print_summary(self, results: List[ReconciliationResult]):
        """Print summary to console"""

        if not results:
            print("❌ No reconciliation results to display")
            return

        perfect_matches = len([r for r in results if r.overall_match])

        print("\n" + "="*60)
        print("RECONCILIATION SUMMARY")
        print("="*60)
        print(f"Total Trades: {len(results)}")
        print(f"Perfect Matches: {perfect_matches}")
        print(f"Success Rate: {perfect_matches/len(results)*100:.1f}%")

        print("\nTrade Details:")
        for result in results:
            status = "✅" if result.overall_match else "❌"
            print(f"  {status} Trade {result.trade_id}: {result.match_percentage:.1f}% match")

            # Show mismatches
            mismatches = [c for c in result.comparisons if not c.match]
            if mismatches:
                for mismatch in mismatches:
                    print(f"      ❌ {mismatch.field_name}: {mismatch.term_sheet_value} ≠ {mismatch.booking_value}")

        print("="*60)

def main():
    """Test the report generator"""

    from data_models import ReconciliationResult, FieldComparison

    # Test data
    results = [
        ReconciliationResult(
            trade_id=1,
            overall_match=True,
            match_percentage=100.0,
            comparisons=[
                FieldComparison(field_name="isin", term_sheet_value="TEST123", booking_value="TEST123", match=True, similarity=1.0),
                FieldComparison(field_name="coupon_rate", term_sheet_value=5.0, booking_value=5.0, match=True, similarity=1.0)
            ],
            summary="Trade 1: 2/2 fields match (100.0%)"
        ),
        ReconciliationResult(
            trade_id=2,
            overall_match=False,
            match_percentage=50.0,
            comparisons=[
                FieldComparison(field_name="isin", term_sheet_value="TEST123", booking_value="TEST123", match=True, similarity=1.0),
                FieldComparison(field_name="coupon_rate", term_sheet_value=5.0, booking_value=5.5, match=False, similarity=0.9, notes="Coupon rate mismatch")
            ],
            summary="Trade 2: 1/2 fields match (50.0%)"
        )
    ]

    generator = SimpleReportGenerator()

    # Test report generation
    csv_file = generator.generate_csv_report(results, "test_report")
    md_file = generator.generate_markdown_report(results, "test.pdf", "test.json", "test_report")

    print(f"✅ Generated reports:")
    print(f"   CSV: {csv_file}")
    print(f"   Markdown: {md_file}")

    # Print summary
    generator.print_summary(results)

if __name__ == "__main__":
    main()
