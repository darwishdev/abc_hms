
from typing import TypedDict, Union
from erpnext.stock.doctype.item.item import Item
from abc_hms.dto.dto_helpers import ErrorResponse

class RoomTypeEnsureItemRequest(TypedDict):
    room_type_name: str
    rate_code: str
    currency: str
    commit: bool

class RoomTypeEnsureItemResult(TypedDict):
    success: bool
    doc: Item  # return the Item as dict

RoomTypeEnsureItemResponse = Union[RoomTypeEnsureItemResult, ErrorResponse]
