
from decimal import Decimal
from typing import TypedDict, Union

from frappe import Optional
from abc_hms.dto.dto_helpers import ErrorResponse
from abc_hms.pos.doctype.folio.folio import Folio
from abc_hms.pos.doctype.folio_window.folio_window import FolioWindow

class FolioUpsertRequest(TypedDict):
    doc: Folio
    commit: bool


class FolioWindowUpsertRequest(TypedDict):
    doc: FolioWindow
    commit: bool

class FolioWindowUpsertResult(TypedDict):
    success: bool
    doc: FolioWindow




class FolioListFilteredRequest(TypedDict):
    pos_profile: str
    docstatus: Optional[int]
    reservation: Optional[str]
    guest: Optional[str]
    room: Optional[str]
    arrival_from: Optional[str]
    arrival_to: Optional[str]
    departure_from: Optional[str]
    departure_to: Optional[str]

class FolioItem(TypedDict):
    room: str
    folio_window: str
    restaurant_table: Optional[str]
    folio: str
    reservation: Optional[str]
    arrival: Optional[str]
    departure: Optional[str]
    guest: Optional[str]
    total_required_amount: Decimal
    total_paid_amount: Decimal

class FolioListFilteredResponse(TypedDict):
    folios: list[FolioItem]
