"""
Fixed reconciliation engine to detect all mismatches
Addresses the missing maturity and notional comparisons
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from data_models import TermSheetData, BookingRecord, FieldComparison, ReconciliationResult
import config

logger = logging.getLogger(__name__)

class SimpleReconciliationEngine:
    """Fixed reconciliation engine that detects all mismatches"""

    def __init__(self, field_mappings: dict = None):
        """
        Initialize reconciliation engine
        
        Args:
            field_mappings: Custom field mappings dict, or None to use defaults
        """
        self.field_mappings = field_mappings  # or self.get_field_mappings()

    def reconcile(self, 
                  term_sheet: TermSheetData, 
                  booking_records: List[BookingRecord],
                  filename: str = "") -> List[ReconciliationResult]:
        """Reconcile term sheet data with booking records - FIXED VERSION"""

        if not term_sheet:
            logger.error("No term sheet data provided")
            return []

        if not booking_records:
            logger.error("No booking records provided")
            return []

        results = []

        # Find relevant booking records (by ISIN if available)
        relevant_records = self._filter_relevant_records(term_sheet, booking_records)

        logger.info(f"Reconciling against {len(relevant_records)} relevant booking records")

        for record in relevant_records:
            result = self._reconcile_single_record(term_sheet, record)
            results.append(result)

        return results

    def _filter_relevant_records(self, 
                                term_sheet: TermSheetData, 
                                booking_records: List[BookingRecord]) -> List[BookingRecord]:
        """Filter booking records that are relevant to the term sheet"""

        if not term_sheet.isin:
            logger.warning("No ISIN in term sheet - using all booking records")
            return booking_records

        # Filter by ISIN
        relevant = [r for r in booking_records if r.ISIN == term_sheet.isin]

        if not relevant:
            logger.warning(f"No booking records found for ISIN {term_sheet.isin}")
            return booking_records  # Return all if no ISIN match

        return relevant

    # def _reconcile_single_record(self, 
    #                             term_sheet: TermSheetData, 
    #                             booking_record: BookingRecord) -> ReconciliationResult:
    #     """Fixed reconciliation with ALL field comparisons"""

    #     comparisons = []
    #     matches = 0
    #     total = 0

    #     # 🐛 BUGFIX: Enhanced field mappings to catch ALL mismatches
    #     # field_mappings = {
    #     #     'isin': 'ISIN',
    #     #     'issuer': 'Issuer',
    #     #     'coupon_rate': 'Coupon',
    #     #     'currency': 'Currency',
    #     #     'maturity_date': 'Maturity',      # Added for maturity comparison
    #     #     # 'face_value': 'Notional',         # Added for notional comparison
    #     #     'face_value': 'NominalAmountPerBond',
    #     #     'issue_amount': 'IssueAmount'     # Added for issue amount comparison
    #     # }

    #     field_mappings = {
    #         # Core identifiers
    #         'isin': 'ISIN',
    #         'issuer': 'Issuer',
            
    #         # Financial terms
    #         'issue_amount': 'IssueAmount',
    #         'face_value': 'NominalAmountPerBond',  # or 'FaceValue'
    #         'coupon_rate': 'Coupon',
    #         'currency': 'Currency',
            
    #         # Dates
    #         'issue_date': 'IssueDate',
    #         'maturity_date': 'Maturity',
    #         'settlement_date': 'SettlementDate',
            
    #         # Payment terms
    #         'payment_frequency': 'InterestPaymentFrequency',
    #         'day_count_convention': 'DayCountFraction',
            
    #         # Bond characteristics
    #         'security_type': 'SecurityType',  # e.g., "Unsecured", "Secured"
    #         'seniority': 'Seniority',  # e.g., "Senior", "Subordinated"
    #         'tenor': 'Tenor'  # e.g., "5 years", "Perpetual"
    #     }

    #     for ts_field, booking_field in field_mappings.items():
    #         ts_value = getattr(term_sheet, ts_field, None)
    #         booking_value = getattr(booking_record, booking_field, None)

    #         # Skip if both values are None
    #         if ts_value is None and booking_value is None:
    #             continue

    #         comparison = self._compare_field(ts_field, ts_value, booking_value)
    #         comparisons.append(comparison)

    #         if comparison.match:
    #             matches += 1
    #         total += 1

    #     match_percentage = (matches / total * 100) if total > 0 else 0
    #     overall_match = matches == total

    #     # Generate summary
    #     summary = f"Trade {booking_record.TradeID}: {matches}/{total} fields match ({match_percentage:.1f}%)"

    #     return ReconciliationResult(
    #         trade_id=booking_record.TradeID,
    #         overall_match=overall_match,
    #         match_percentage=match_percentage,
    #         comparisons=comparisons,
    #         summary=summary
    #     )

    def _reconcile_single_record(self, 
                                 term_sheet: TermSheetData, 
                                 booking_record: BookingRecord) -> ReconciliationResult:
        """Reconciliation with dynamic field matching"""

        comparisons = []
        matches = 0
        total = 0

        # Get all available fields from booking record
        booking_fields = set(booking_record.model_dump().keys())
        
        # Define possible (booking) field name variations for each term sheet field
        # TODO: Add a 'field_name' detection mechanism using LLM and map to standard names
        field_name_mappings = {
            'isin': ['ISIN', 'isin', 'Isin'],
            'issuer': ['Issuer', 'issuer', 'IssuerName', 'IssuingEntity'],
            'issue_amount': ['IssueAmount', 'IssueSize', 'TotalAmount', 'issue_amount'],
            'face_value': ['NominalAmountPerBond', 'FaceValue', 'Denomination', 'ParValue', 'face_value'],
            'notional_amount': ['Notional', 'NotionalAmount', 'TotalNotional', 'notional_amount'],  # trade specific
            'coupon_rate': ['Coupon', 'CouponRate', 'InterestRate', 'Rate', 'coupon_rate'],
            'currency': ['Currency', 'currency', 'Ccy'],
            'issue_date': ['IssueDate', 'issue_date', 'IssuanceDate'],
            'maturity_date': ['Maturity', 'MaturityDate', 'maturity_date'],
            'settlement_date': ['SettlementDate', 'settlement_date', 'SettleDate'],
            'payment_frequency': ['InterestPaymentFrequency', 'PaymentFrequency', 'Frequency', 'payment_frequency'],
            'day_count_convention': ['DayCountFraction', 'DayCount', 'DayCountConvention', 'day_count_convention'],
        }

        # Compare each field from term sheet
        for ts_field, possible_booking_fields in field_name_mappings.items():
            ts_value = getattr(term_sheet, ts_field, None)
            
            # Skip if term sheet doesn't have this field
            if ts_value is None:
                continue
            
            # Find matching booking field
            booking_field = None
            booking_value = None
            
            for possible_field in possible_booking_fields:
                if possible_field in booking_fields:
                    booking_field = possible_field
                    booking_value = getattr(booking_record, booking_field, None)
                    break
            
            # If no matching field found in booking data, skip this comparison
            if booking_field is None:
                logger.debug(f"No matching booking field found for term sheet field: {ts_field}")
                continue
            
            # If booking value is None, skip
            if booking_value is None:
                continue
                
            total += 1
            comparison = self._compare_field(ts_field, ts_value, booking_value)
            
            if comparison.match:
                matches += 1
            
            comparisons.append(comparison)

        # Calculate match percentage
        match_percentage = (matches / total * 100) if total > 0 else 0.0
        perfect_match = (match_percentage == 100.0)

        # Generate summary
        summary = f"Trade {booking_record.TradeID}: {matches}/{total} fields match ({match_percentage:.1f}%)"

        return ReconciliationResult(
            trade_id=booking_record.TradeID,
            overall_match=perfect_match,  # Use overall_match to match the data model
            match_percentage=match_percentage,
            comparisons=comparisons,
            summary=summary
        )

    def _compare_field(self, field_name: str, ts_value, booking_value) -> FieldComparison:
        """Enhanced field comparison with date support"""

        # Handle None values
        if ts_value is None and booking_value is None:
            return FieldComparison(
                field_name=field_name,
                term_sheet_value=ts_value,
                booking_value=booking_value,
                match=True,
                similarity=1.0,
                notes="Both values are None"
            )
        elif ts_value is None or booking_value is None:
            return FieldComparison(
                field_name=field_name,
                term_sheet_value=ts_value,
                booking_value=booking_value,
                match=False,
                similarity=0.0,
                notes="One value is missing"
            )

        # 🔧 FIX 3: Enhanced comparison logic
        if field_name in ['coupon_rate', 'face_value', 'issue_amount']:
            return self._compare_numeric(field_name, ts_value, booking_value)
        elif field_name in ['maturity_date', 'issue_date']:
            return self._compare_date(field_name, ts_value, booking_value)
        elif field_name in ['isin', 'currency']:
            return self._compare_exact(field_name, ts_value, booking_value)
        else:
            return self._compare_text(field_name, ts_value, booking_value)

    def _compare_numeric(self, field_name: str, ts_value, booking_value) -> FieldComparison:
        """Compare numeric values with tolerance"""

        try:
            ts_num = float(ts_value)
            booking_num = float(booking_value)

            # Calculate relative difference
            if booking_num != 0:
                diff = abs(ts_num - booking_num) / abs(booking_num)
            else:
                diff = abs(ts_num - booking_num)

            match = diff <= config.NUMERIC_TOLERANCE
            similarity = max(0.0, 1.0 - diff)

            notes = f"Difference: {abs(ts_num - booking_num):.4f}" if not match else None

            return FieldComparison(
                field_name=field_name,
                term_sheet_value=ts_value,
                booking_value=booking_value,
                match=match,
                similarity=similarity,
                notes=notes
            )

        except (ValueError, TypeError):
            # Not numeric, fall back to exact comparison
            return self._compare_exact(field_name, ts_value, booking_value)

    def _compare_date(self, field_name: str, ts_value, booking_value) -> FieldComparison:
        """🔧 NEW: Compare date fields with tolerance"""

        try:
            ts_date = self._parse_date(str(ts_value))
            booking_date = self._parse_date(str(booking_value))

            if ts_date and booking_date:
                diff_days = abs((ts_date - booking_date).days)
                tolerance_days = getattr(config, 'DATE_TOLERANCE_DAYS', 1)

                match = diff_days <= tolerance_days
                similarity = max(0.0, 1.0 - (diff_days / 365))  # Annual decay

                notes = None
                if not match:
                    notes = f"Date difference: {diff_days} days ({ts_value} vs {booking_value})"

                return FieldComparison(
                    field_name=field_name,
                    term_sheet_value=ts_value,
                    booking_value=booking_value,
                    match=match,
                    similarity=similarity,
                    notes=notes
                )
            else:
                # Could not parse dates - fallback to exact comparison
                return self._compare_exact(field_name, ts_value, booking_value)

        except Exception:
            return self._compare_exact(field_name, ts_value, booking_value)

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse date string with multiple format support"""

        import re
        from datetime import datetime

        # Clean the date string
        date_str = re.sub(r'[^0-9-/.]', '', date_str.strip())

        date_formats = [
            '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y',
            '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y',
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    def _compare_exact(self, field_name: str, ts_value, booking_value) -> FieldComparison:
        """Compare values for exact match"""

        ts_str = str(ts_value).strip()
        booking_str = str(booking_value).strip()

        match = ts_str == booking_str
        similarity = 1.0 if match else 0.0
        notes = None if match else "Exact values don't match"

        return FieldComparison(
            field_name=field_name,
            term_sheet_value=ts_value,
            booking_value=booking_value,
            match=match,
            similarity=similarity,
            notes=notes
        )

    def _compare_text(self, field_name: str, ts_value, booking_value) -> FieldComparison:
        """Compare text values with similarity matching"""

        ts_str = str(ts_value).strip().lower()
        booking_str = str(booking_value).strip().lower()

        if ts_str == booking_str:
            match = True
            similarity = 1.0
            notes = None
        else:
            # Simple similarity check - check if one contains the other
            if ts_str in booking_str or booking_str in ts_str:
                match = True
                similarity = 0.9
                notes = "Partial text match"
            else:
                match = False
                similarity = 0.0
                notes = "Text doesn't match"

        return FieldComparison(
            field_name=field_name,
            term_sheet_value=ts_value,
            booking_value=booking_value,
            match=match,
            similarity=similarity,
            notes=notes
        )
