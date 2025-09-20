from typing import  List, TypedDict, Union
from frappe import Optional
from abc_hms.dto.dto_helpers import ErrorResponse

class ReservationDate(TypedDict):
    for_date: int
    reservation: str
    room_type: Optional[str]
    room: Optional[str]

class ReservationDateSyncRequest(TypedDict):
    reservation_name: str
    commit: bool

class ReservationDateSyncResult(TypedDict):
    success: bool
    affected: List[ReservationDate]

ReservationDateSyncResponse = Union[ReservationDateSyncResult, ErrorResponse]
