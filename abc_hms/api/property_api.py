from typing import List, Optional, TypedDict
import frappe
from frappe import _
import json

from pydantic import ValidationError
from abc_hms.container import app_container
from abc_hms.dto.property_dto import (
    PropertyEndOfDayRequest,
    PropertyEndOfDayResponse,
)


class ValidateResponse(TypedDict):
    arrivals: Optional[List[str]]
    departures: Optional[List[str]]
    sessions: Optional[List[str]]
    valid: bool

def property_end_of_day_validate(
    property: str,
    auto_close_sessions :bool,
    auto_mark_no_show: bool,
) -> ValidateResponse:
    departures  = []
    arrivals  = None if auto_mark_no_show else app_container.reservation_usecase.reservation_arrivals_for_current_date(property)
    sessions  = None if auto_close_sessions else app_container.pos_session_usecase.pos_sessions_crrent_date(property)
    valid = not departures and (auto_mark_no_show or not arrivals) and (auto_close_sessions or not arrivals)
    return {"valid" :valid ,"arrivals" : arrivals , "departures" : departures, "sessions": sessions}


@frappe.whitelist(methods=["POST"])
def property_end_of_day() -> PropertyEndOfDayResponse:
    try:
        data = frappe.local.request.data
        payload: PropertyEndOfDayRequest = json.loads(data or "{}")
        property = str(payload.get("property"))
        auto_mark_no_show = bool(payload.get("auto_mark_no_show" , False))
        auto_session_close = bool(payload.get("auto_session_close" , False))
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success": False, "data": None, "error": f"{str(e)}"}
    validation_result = property_end_of_day_validate(
        property ,
        auto_mark_no_show,
        auto_session_close
    )
    if not validation_result["valid"]:
        frappe.local.response.http_status_code = 400
        return {
            "success": False,
            "error": "End-of-day validation failed",
            "data": validation_result
        }
    frappe.db.begin()
    try:
        # updated_reservations = app_container.reservation_usecase.reservation_end_of_day_auto_mark(payload)
        # if auto_session_close:
        #     closed_sessions= app_container.pos_session_usecase.pos_sessions_close_crrent_date(property)
        # invoices = app_container.pos_invoice_usecase.pos_invoice_end_of_day_auto_close(property)
        opening_entry = app_container.pos_opening_entry_usecase.pos_opening_entry_find_by_property(property)
        return opening_entry
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"Error during property end-of-day: {e}")
        frappe.local.response.http_status_code = 500
        return {
            "success": False,
            "error": str(e),
            "data": None
        }
    return {
        "success": True,
        "doc" : {},
    }

