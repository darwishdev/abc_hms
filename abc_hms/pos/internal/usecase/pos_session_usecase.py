import frappe
from abc_hms.dto.pos_session_dto import POSSessionFindForDateResponse, POSSessionUpsertRequest, POSSessionUpsertResponse
from frappe import  _


from abc_hms.pos.doctype.pos_session.pos_session import POSSession
from ..repo.pos_session_repo import POSSessionRepo
from pymysql.err import IntegrityError
class POSSessionUsecase:
    def __init__(self):
        self.repo = POSSessionRepo()

    def pos_session_upsert(
        self,
        request :POSSessionUpsertRequest,
        commit : bool
    ) -> POSSession:
        return self.repo.pos_session_upsert(request['doc'] , commit)

    def pos_session_find(
        self,
        pos_session :str
    ):
        return self.repo.pos_session_find(pos_session)




    def pos_sessions_close_for_date_profile(
        self,
        for_date :int,
        profile :str,
    ):
        return self.repo.pos_sessions_close_for_date_profile(for_date,  profile)
    def pos_sessions_close_crrent_date(
        self,
        property :str,
    ):
        return self.repo.pos_sessions_close_crrent_date(property)



    def pos_session_find_for_user(
        self,
        user :str,
        profile: str,
        docstatus: int
    ):
        result = self.repo.pos_session_find_for_user(user , profile , docstatus)
        return result
    def pos_sessions_crrent_date(
        self,
        property :str,
    ):
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
