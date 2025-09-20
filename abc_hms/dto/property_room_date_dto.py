
from typing import List, TypedDict, Union
from frappe import Optional

from abc_hms.dto.dto_helpers import ErrorResponse

from abc_hms.property.doctype.property_setting.property_setting import PropertySetting

class RoomDateLookup(TypedDict):
    id: Optional[int]
    lookup_type: str
    lookup_key: str
    lookup_value: int


class RoomDateLog(TypedDict):
    room: str
    user: str
    reason: str
    from_date: int
    to_date: int
    out_of_order_status: Optional[int]
    out_of_order_reason: Optional[str]


class RoomDateBulkUpsertFields(TypedDict):
    persons: Optional[int]
    house_keeping_status: Optional[int]
    room_status: Optional[int]
    out_of_order_status: Optional[int]
    out_of_order_reason: Optional[str]
    guest_service_status: Optional[int]

class RoomDate(RoomDateBulkUpsertFields):
    room: str
    for_date: int

class RoomDateView(TypedDict):
    room: str
    for_date: int
    persons: Optional[str]
    out_of_order_reason: Optional[str]
    house_keeping_status: Optional[str]
    room_status: Optional[str]
    out_of_order_status: Optional[str]
    guest_service_status: Optional[str]

class RoomDateBulkUpsertRequest(TypedDict):
    """API request DTO"""
    room_numbers: List[str]
    for_date: int
    updated_fileds: RoomDateBulkUpsertFields
    commit: bool

class RoomDateBulkUpsertResult(TypedDict):
    success: bool
    affected: List[RoomDateView]

RoomDateBulkUpsertResponse = Union[RoomDateBulkUpsertResult, ErrorResponse]
