from decimal import Decimal
from typing import List, TypedDict, Union
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice
from frappe import Optional

from abc_hms.dto.dto_helpers import ErrorResponse


class PosInvoiceItemTransferRequest(TypedDict):
    source_invoice: str
    source_window: str
    items: Optional[List[str]]
    destination_folio: Optional[str]
    destination_invoice: str
    destination_window: str
    folio_window: Optional[str]

class PosInvoiceItemUpdateRequest(TypedDict):
    names: List[str]
    folio_window: Optional[str]

class POSInvoiceData(POSInvoice):
    """ERPNext POSInvoice with custom fields mixed in"""
    folio: Optional[str]
    number_of_guests: Optional[int]
    room_number: Optional[str]
    table_number: Optional[str]
    for_date: Optional[int]
class PosInvoiceUpsertRequest(TypedDict):
    """API request DTO"""
    doc: POSInvoiceData
    reset_items: bool
    reset_paymnets: bool
PosInvoiceUpsertResponse = Union[POSInvoiceData, ErrorResponse]

class PosInvoiceFindForDateRequest(TypedDict):
    """API request DTO for fetching POS invoices by date"""
    for_date: int
    fields: Optional[List[str]]  # optional, defaults handled in repo

class PosInvoiceFindForDateResult(TypedDict):
    """API response DTO"""
    success: bool
    invoices: List[POSInvoiceData]

PosInvoiceFindForDateResponse = Union[PosInvoiceFindForDateResult, ErrorResponse]
