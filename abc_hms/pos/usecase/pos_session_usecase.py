from typing import List
import frappe

from abc_hms.dto.pos_session_dto import POSSessionFindForDateResponse, POSSessionUpsertRequest, POSSessionUpsertResponse
from frappe import Optional, _

from abc_hms.pos.doctype.pos_session.pos_session import POSSession
from abc_hms.pos.repo.pos_session_repo import POSSessionRepo

class POSSessionUsecase:
    def __init__(self):
        self.repo = POSSessionRepo()

    def pos_session_upsert(
        self,
        request :POSSessionUpsertRequest,
    ) -> POSSessionUpsertResponse:
        try:
            result = self.repo.pos_session_upsert(request['doc'],commit=request['commit'])
        except frappe.ValidationError as e:
            frappe.log_error(f"POS session validation failed: {e}")
            raise

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "POS session Upsert API Error")
            return {"success" : False , "error" : f"Unexpected error: {str(e)}"}

        return {
            "success": True,
            "doc": result,
        }


    def pos_sessions_close_crrent_date(
        self,
        property :str,
    ):
        return self.repo.pos_sessions_close_crrent_date(property)

    def pos_sessions_crrent_date(
        self,
        property :str,
    ) -> Optional[List[str]]:
        result = self.repo.pos_session_list_for_current_date(property)
        return result
    def pos_session_find_for_date(
        self,
        for_date :int,
        docstatus: int
    ) -> POSSessionFindForDateResponse:
        try:
            filters: POSSession = {"docstatus" : docstatus , "for_date": for_date}  # type: ignore
            result = self.repo.pos_session_list(filters)
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "POS session find by date API Error")
            return {"success" : False , "error" : f"Unexpected error: {str(e)}"}

        return {
            "success": True,
            "docs": result,
        }
