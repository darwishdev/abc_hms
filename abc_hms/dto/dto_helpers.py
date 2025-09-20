
from typing import TypedDict

from frappe import Any, Optional



class ErrorResponse(TypedDict):
    success: bool
    error: str
class ErrorResponseWithData(ErrorResponse):
    data: Optional[Any]
