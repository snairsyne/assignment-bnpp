"""
Simple booking data processor for CSV and JSON files
"""
import csv
import json
import pandas as pd
import logging
from pathlib import Path
from typing import List
from data_models import BookingRecord

logger = logging.getLogger(__name__)

class BookingDataProcessor:
    """Simple processor for booking data in CSV or JSON format"""

    def load_booking_data(self, file_path: str) -> List[BookingRecord]:
        """Load booking data from CSV or JSON file"""

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = file_path.suffix.lower()

        if extension == '.csv':
            return self._load_from_csv(file_path)
        elif extension == '.json':
            return self._load_from_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")

    def _load_from_csv(self, csv_path: Path) -> List[BookingRecord]:
        """Load booking data from CSV"""

        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded CSV with {len(df)} rows, {len(df.columns)} columns")

            records = []
            for _, row in df.iterrows():
                try:
                    # Convert pandas Series to dict and handle NaN values
                    row_dict = row.to_dict()
                    cleaned_dict = {k: (v if pd.notna(v) else None) for k, v in row_dict.items()}

                    record = BookingRecord(**cleaned_dict)
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Error creating record from CSV row: {e}")

            logger.info(f"Successfully loaded {len(records)} booking records from CSV")
            return records

        except Exception as e:
            logger.error(f"Error loading CSV {csv_path}: {e}")
            raise

    def _load_from_json(self, json_path: Path) -> List[BookingRecord]:
        """Load booking data from JSON"""

        try:
            with open(json_path, 'r') as f:
                data = json.load(f)

            # Handle different JSON structures
            if isinstance(data, list):
                raw_records = data
            elif isinstance(data, dict):
                if 'trades' in data:
                    raw_records = data['trades']
                elif 'records' in data:
                    raw_records = data['records']
                else:
                    raw_records = [data]  # Single record
            else:
                raise ValueError("Invalid JSON structure")

            records = []
            for raw_record in raw_records:
                try:
                    record = BookingRecord(**raw_record)
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Error creating record from JSON: {e}")

            logger.info(f"Successfully loaded {len(records)} booking records from JSON")
            return records

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in file {json_path}: {e}")
            raise ValueError(f"Invalid JSON file: {json_path}. Error: {e}")

        except Exception as e:
            logger.error(f"Error loading JSON {json_path}: {e}")
            raise

    def get_summary(self, records: List[BookingRecord]) -> dict:
        """Get summary statistics of booking records"""

        if not records:
            return {"total": 0}

        # Extract ISINs and other key fields
        isins = set(r.ISIN for r in records if r.ISIN)
        issuers = set(r.Issuer for r in records if r.Issuer)
        currencies = set(r.Currency for r in records if r.Currency)
        coupons = [r.Coupon for r in records if r.Coupon is not None]

        summary = {
            "total_records": len(records),
            "unique_isins": list(isins),
            "unique_issuers": list(issuers),
            "currencies": list(currencies),
            "coupon_range": f"{min(coupons):.2f}%-{max(coupons):.2f}%" if coupons else "N/A"
        }

        return summary

def main():
    """Test the booking processor"""

    processor = BookingDataProcessor()

    # Test files
    test_files = ["Genel_Energy_Trades.json", "IDBI_Omni_Trades.json", "IDBI_Omni_Trades.csv"]

    for file in test_files:
        if Path(file).exists():
            try:
                records = processor.load_booking_data(file)
                summary = processor.get_summary(records)

                print(f"\n{'='*40}")
                print(f"File: {file}")
                print(f"Records loaded: {len(records)}")
                print(f"ISINs: {summary['unique_isins']}")
                print(f"Currencies: {summary['currencies']}")
                print(f"Coupon range: {summary['coupon_range']}")

                if records:
                    sample = records[0]
                    print(f"Sample record: TradeID={sample.TradeID}, ISIN={sample.ISIN}, Coupon={sample.Coupon}")

            except Exception as e:
                print(f"❌ Error loading {file}: {e}")
        else:
            print(f"❌ File not found: {file}")

if __name__ == "__main__":
    main()
