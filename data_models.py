"""
Simple data models for term sheet reconciliation
Compatible with both old and new Pydantic versions
"""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class TermSheetData(BaseModel):
    # Identifiers
    isin: Optional[str] = None
    issuer: Optional[str] = None
    
    # Financial terms
    issue_amount: Optional[float] = None
    face_value: Optional[float] = None
    notional_amount: Optional[float] = None
    coupon_rate: Optional[float] = None
    currency: Optional[str] = None
    
    # Dates
    issue_date: Optional[str] = None
    maturity_date: Optional[str] = None
    settlement_date: Optional[str] = None
    
    # Payment terms
    payment_frequency: Optional[str] = None
    day_count_convention: Optional[str] = None
    
    # Bond characteristics
    security_type: Optional[str] = None
    seniority: Optional[str] = None
    tenor: Optional[str] = None
    
    class Config:
        populate_by_name = True  # For Pydantic v2

class BookingRecord(BaseModel):
    """Booking system record - backward compatible"""
    TradeID: Optional[int] = None
    ISIN: Optional[str] = None
    Issuer: Optional[str] = None
    Notional: Optional[float] = None
    Coupon: Optional[float] = None
    Currency: Optional[str] = None
    Maturity: Optional[str] = None
    SettlementDate: Optional[str] = None
    IssueDate: Optional[str] = None
    IssueAmount: Optional[float] = None  # 🔧 NEW: Added for issue amount comparison

    class Config:
        allow_population_by_field_name = True

class FieldComparison(BaseModel):
    """Field comparison result"""
    field_name: str
    term_sheet_value: Optional[Any] = None
    booking_value: Optional[Any] = None
    match: bool
    similarity: float
    notes: Optional[str] = None

class ReconciliationResult(BaseModel):
    """Complete reconciliation result"""
    trade_id: Optional[int] = None
    overall_match: bool
    match_percentage: float
    comparisons: List[FieldComparison]
    summary: str

