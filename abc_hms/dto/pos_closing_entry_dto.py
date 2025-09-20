from typing import TypedDict, Union
from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry  import POSClosingEntry
from abc_hms.dto.dto_helpers import ErrorResponse


class POSClosingEntryUpsertRequest(TypedDict):
    """API request DTO"""
    doc: POSClosingEntry
    commit: bool

class POSClosingEntryUpsertResult(TypedDict):
    """API response DTO"""
    success: bool
    doc: POSClosingEntry

POSClosingEntryUpsertResponse = Union[POSClosingEntryUpsertResult, ErrorResponse]
