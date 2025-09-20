
from typing import Dict, TypedDict, Union
from frappe import Optional
from abc_hms.dto.dto_helpers import ErrorResponse, ErrorResponseWithData



class PropertyEndOfDayRequest(TypedDict):
    property: str
    auto_mark_no_show: Optional[bool]
    auto_session_close: Optional[bool]

class PropertyEndOfDayResult(TypedDict):
    success: bool
    doc: Dict

PropertyEndOfDayResponse = Union[PropertyEndOfDayResult, ErrorResponseWithData]

