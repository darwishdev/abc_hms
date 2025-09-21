from datetime import datetime
from typing import List, Optional, TypedDict
from erpnext.accounts.doctype.pos_opening_entry.pos_opening_entry import POSOpeningEntry
import frappe
from frappe import _, enqueue
import json

from pydantic import ValidationError
from abc_hms.api.pos_invoice_api import pos_invoice_upsert
from abc_hms.container import app_container
from abc_hms.dto.pos_opening_entry_dto import POSOpeningEntryData
from abc_hms.dto.property_dto import (
    PropertyEndOfDayRequest,
    PropertyEndOfDayResponse,
)
from abc_hms.dto.property_setting_dto import PropertySettingData


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

def property_setting_to_pos_opening_entry(data: PropertySettingData, property: str) ->POSOpeningEntryData:
    """Convert property settings dict → POS Opening Entry dict."""
    return {
        "company": data.company,
        "property": property,
        "docstatus": 0,
        "user": frappe.session.user,
        "pos_profile": data.default_pos_profile,
        "for_date": data.business_date_int,
        "period_start_date": f"{data['business_date']} 00:00:00",
        "balance_details": [{
            "mode_of_payment": "Cash",
            "opening_amount": 0,
        }],
        "posting_date": datetime.now().replace(microsecond=0),
    } # type: ignore

@frappe.whitelist()
def enqueue_property_end_of_day(property: str, auto_mark_no_show: bool=False, auto_session_close: bool=False):
    """Enqueue End of Day process instead of running immediately"""
    enqueue(
        "abc_hms.end_of_day.run_property_end_of_day",
        property=property,
        auto_mark_no_show=auto_mark_no_show,
        auto_session_close=auto_session_close,
        queue="default"
    )
    return {"status": "queued"}
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


    property_setting = app_container.property_setting_usecase.property_setting_find(property)
    if not property_setting:
        frappe.local.response.http_status_code = 404
        frappe.throw(f"Property {property} Not Found")
        raise
    frappe.db.begin()
    try:
        updated_reservations = app_container.reservation_usecase.reservation_end_of_day_auto_mark(payload)
        if auto_session_close:
            closed_sessions = app_container.pos_session_usecase.pos_sessions_close_crrent_date(property)

        closed_invoices = app_container.pos_invoice_usecase.pos_invoice_end_of_day_auto_close(property)
        opening_entry = app_container.pos_opening_entry_usecase.pos_opening_entry_find_by_property(property)
        closing_entry = {}
        if opening_entry and isinstance(opening_entry , str):
            closing_entry = app_container.pos_opening_entry_usecase.pos_closing_entry_from_opening_name({
                    "opening_entry" : opening_entry,
                    "commit": False
            })

        new_date_settings = app_container.property_setting_usecase.property_setting_increase_business_date(property)
        bzns_date = new_date_settings.get("business_date_int")
        bzns_date_int = new_date_settings.get("business_date")
        if bzns_date and bzns_date_int:
            new_opening_entry_params = property_setting_to_pos_opening_entry(property_setting , property)
            new_opening_entry = app_container.pos_opening_entry_usecase.pos_opening_entry_upsert({
                "doc" : new_opening_entry_params,
                "commit" : False,
            })

            pos_invoices = app_container.reservation_usecase.sync_reservations_to_pos_invoices(
                bzns_date,
                bzns_date_int,
                app_container.pos_invoice_usecase.pos_invoice_upsert
            )
        return {
            "new_date" : bzns_date,
            "updated_reservations" : updated_reservations,
            "closed_invoices" : closed_invoices,
            "opening_entry" : opening_entry,
            "closed_sessions" : closed_sessions,
            "closing_entry" : closing_entry,
            "new_opening_entry" : opening_entry,
            "new_invoices" : pos_invoices
        }
    except frappe.ValidationError:
        frappe.db.rollback()
        raise
    except Exception as e:
        frappe.db.rollback()
        raise Exception(f"Unexpected Error : {str(e)}")
    return {
        "success": True,
        "doc" : {},
    }

