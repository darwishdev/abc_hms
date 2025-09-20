from typing import List, TypedDict, Union

from frappe import Optional
from abc_hms.dto.dto_helpers import ErrorResponse
from abc_hms.pos.doctype.pos_session.pos_session import POSSession


class POSSessionUpsertRequest(TypedDict):
    doc: POSSession
    commit: bool

class POSSessionUpsertResult(TypedDict):
    success: bool
    doc: POSSession

POSSessionUpsertResponse = Union[POSSessionUpsertResult, ErrorResponse]

class POSSessionDefaults(TypedDict):
    pos_profile: str
    for_date: int
    opening_entry: str


class POSSessionDefaultsFindRequest(TypedDict):
    """API request DTO"""
    property_name: str

class POSSessionDefaultsFindResult(TypedDict):
    success: bool
    doc: Optional[POSSessionDefaults]

POSSessionDefaultsFindResponse = Union[POSSessionDefaultsFindResult, ErrorResponse]


class POSSessionFindForDateRequest(TypedDict):
    for_date: int

class POSSessionFindForDateResult(TypedDict):
    success: bool
    docs: Optional[List[POSSession]]

POSSessionFindForDateResponse = Union[POSSessionFindForDateResult, ErrorResponse]


