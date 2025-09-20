
import frappe
from frappe import _
from abc_hms.dto.pos_folio_dto import FolioUpsertRequest, FolioUpsertResponse, FolioWindowUpsertRequest, FolioWindowUpsertResponse
from abc_hms.pos.doctype.folio.folio import Folio
from abc_hms.pos.doctype.folio_window.folio_window import FolioWindow
from abc_hms.pos.repo.folio_repo import FolioRepo

class FolioUsecase:
    def __init__(self):
        self.repo = FolioRepo()

    def folio_upsert(
        self,
        payload :FolioUpsertRequest,
    ) -> FolioUpsertResponse:
        try:
            folio = self.repo.folio_upsert(payload.get("doc") , payload.get("commit"))
            return {"success" : True , "doc" : folio}
        except frappe.ValidationError as e:
            frappe.log_error(f"Folio validation failed: {e}")
            raise

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "POS closing_entry Upsert API Error")
            return {"success" : False , "error" : f"Unexpected error: {str(e)}"}

    def folio_window_upsert(self, req: FolioWindowUpsertRequest) -> FolioWindowUpsertResponse:
        try:
            doc = self.repo.folio_window_upsert(req["doc"], commit=req["commit"])
            return {
                "success": True,
                "doc": doc,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Folio Window Upsert Error: {str(e)}",
            }
