
from typing import TypedDict, Union
from abc_hms.dto.dto_helpers import ErrorResponse
from abc_hms.pos.doctype.folio.folio import Folio
from abc_hms.pos.doctype.folio_window.folio_window import FolioWindow

class FolioUpsertRequest(TypedDict):
    doc: Folio
    commit: bool

class FolioUpsertResult(TypedDict):
    success: bool
    doc: Folio

FolioUpsertResponse = Union[FolioUpsertResult, ErrorResponse]
class FolioWindowUpsertRequest(TypedDict):
    doc: FolioWindow
    commit: bool

class FolioWindowUpsertResult(TypedDict):
    success: bool
    doc: FolioWindow


FolioWindowUpsertResponse = Union[FolioWindowUpsertResult, ErrorResponse]
