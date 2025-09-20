from typing import TypedDict, Union
from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import POSClosingEntry
from erpnext.accounts.doctype.pos_opening_entry.pos_opening_entry  import POSOpeningEntry
from frappe import Optional

from abc_hms.dto.dto_helpers import ErrorResponse


class POSOpeningEntryData(POSOpeningEntry):
    """ERPNext POSInvoice with custom fields mixed in"""
    for_date: Optional[int]

class POSOpeningEntryUpsertRequest(TypedDict):
    """API request DTO"""
    doc: POSOpeningEntryData
    commit: bool

class POSOpeningEntryUpsertResult(TypedDict):
    """API response DTO"""
    success: bool
    doc: POSOpeningEntryData

POSOpeningEntryUpsertResponse = Union[POSOpeningEntryUpsertResult, ErrorResponse]


class POSClosingEntryFromOpeningRequest(TypedDict):
    """API request DTO"""
    opening_entry: str        # The POS Opening Entry name (doctype primary key)
    commit: Optional[bool] # Optional flag to commit transaction


class POSClosingEntryFromOpeningResult(TypedDict):
    """API response DTO"""
    success: bool
    doc: POSClosingEntry

POSClosingEntryFromOpeningResponse = Union[POSClosingEntryFromOpeningResult, ErrorResponse]

class POSOpeningEntryFindByProfileRequest(TypedDict):
    pos_profile: str
    for_date: Optional[int]


class POSOpeningEntryFindByProfileResult(TypedDict):
    success: bool
    doc: POSClosingEntry

POSOpeningEntryFindByProfileResponse = Union[POSOpeningEntryFindByProfileResult, ErrorResponse]
