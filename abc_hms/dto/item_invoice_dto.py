from typing import TypedDict, Union
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice
from frappe import Optional

from abc_hms.dto.dto_helpers import ErrorResponse


class POSInvoiceData(POSInvoice):
    """ERPNext POSInvoice with custom fields mixed in"""
    folio: Optional[str]
    number_of_guests: Optional[int]
    room_number: Optional[str]
    table_number: Optional[str]
    for_date: Optional[int]
class PosInvoiceUpsertRequest(TypedDict):
    """API request DTO"""
    invoice_id: str
    invoice: POSInvoiceData
    commit: bool

class PosInvoiceUpsertResult(TypedDict):
    """API response DTO"""
    success: bool
    invoice_id: str
    doc: POSInvoiceData  # return updated doc

PosInvoiceUpsertResponse = Union[PosInvoiceUpsertResult, ErrorResponse]
