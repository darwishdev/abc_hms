from datetime import datetime
from time import sleep
from typing import List, Optional, TypedDict
from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import make_closing_entry_from_opening
from erpnext.accounts.doctype.pos_opening_entry.pos_opening_entry import POSOpeningEntry
import frappe
from frappe import _, enqueue, publish_realtime
import json

from frappe.model.workflow import show_progress
from pydantic import ValidationError
from sentry_sdk.utils import json_dumps
from abc_hms.api.decorators import business_date_protected
from abc_hms.api.pos_invoice_api import pos_invoice_upsert
from abc_hms.container import app_container
from abc_hms.dto.pos_opening_entry_dto import POSOpeningEntryData
from abc_hms.dto.property_dto import (
    PropertyEndOfDayRequest,
    PropertyEndOfDayResponse,
)
from abc_hms.dto.property_setting_dto import PropertySettingData
from abc_hms.exceptions.exceptions import EndOfDayValidationError


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
    departures  = app_container.reservation_usecase.reservation_departures_for_current_date(property)
    if len(departures) > 0:
        frappe.throw("Please Check Out Or Extend Departure To Be Able To Run The End of Day")
        raise frappe.ValidationError(f"EOD Failed: Departures not handled")
    arrivals  = None if auto_mark_no_show else app_container.reservation_usecase.reservation_arrivals_for_current_date(property)
    sessions  = None if auto_close_sessions else app_container.pos_session_usecase.pos_sessions_crrent_date(property)
    valid = not departures and (auto_mark_no_show or not arrivals) and (auto_close_sessions or not arrivals)
    return {"valid" :valid ,"arrivals" : arrivals , "departures" : departures, "sessions": sessions}


def _publish_step(property: str, step: str, status: str = "in-progress", details=None):
    """Helper to publish step progress using frappe.publish_progress directly"""
    # Complete step order to match property_end_of_day
    step_order = [
        "validation",
        "mark_no_show",
        "close_sessions",
        "close_invoices",
        "closing_entry",
        "new_opening_entry",
        "new_invoices",
        "end"
    ]

    total_steps = len(step_order)
    current_index = step_order.index(step) + 1 if step in step_order else 0

    # Calculate progress percentage
    progress = (current_index / total_steps) * 100
    sleep(.5)
    # Publish directly
    frappe.publish_progress(
        progress,
        title=f"{property} : End of Day Progress",
        description=f"{step}: {status}"
    )
def property_setting_to_pos_opening_entry(data: PropertySettingData, property: str) ->POSOpeningEntryData:
    """Convert property settings dict → POS Opening Entry dict."""
    return {
        "company": data.company,
        "property": property,
        "docstatus": 1,
        "user": frappe.session.user,
        "pos_profile": data.default_pos_profile,
        "for_date": data.business_date_int,
        "period_start_date": f"{data.business_date} 00:00:00",
        "balance_details": [{
            "mode_of_payment": "Cash",
            "opening_amount": 0,
        }],
        "posting_date": datetime.now().replace(microsecond=0),
    } # type: ignore

@frappe.whitelist()
def enqueue_property_end_of_day(property: str, auto_mark_no_show: bool=False, auto_session_close: bool=False):

    _publish_step(property, "validation", "in-progress")
    validation_result = property_end_of_day_validate(
        property,
        auto_mark_no_show,
        auto_session_close
    )
    if not validation_result["valid"]:
        raise EndOfDayValidationError(_("EOD Validation failed") , validation_result)

    _publish_step(property, "validation", "completed")

    enqueue(
        "abc_hms.property_end_of_day",
        property=property,
        auto_mark_no_show=auto_mark_no_show,
        auto_session_close=auto_session_close,
        now="true",
        queue="long"
    )
    # return {"status": "queued"}

@frappe.whitelist()
def property_end_of_day(property: str, auto_mark_no_show: bool=False, auto_session_close: bool=False) -> PropertyEndOfDayResponse:
    property_setting = app_container.property_setting_usecase.property_setting_find(property)
    if not property_setting:
        raise frappe.NotFound(f"Property {property} Not Found")

    frappe.db.begin()
    try:
        _publish_step(property, "mark_no_show", "in-progress")
        closed_sessions = []
        pos_invoices = []
        new_opening_entry = ""

        updated_reservations = app_container.reservation_usecase.reservation_end_of_day_auto_mark(property, auto_mark_no_show)
        _publish_step(property, "Update Reservations", "completed")

        if auto_session_close:
            _publish_step(property, "close_sessions", "in-progress")
            closed_sessions = app_container.pos_session_usecase.pos_sessions_close_crrent_date(property)
            _publish_step(property, "close_sessions", "completed")

        _publish_step(property, "close_invoices", "in-progress")
        closed_invoices = app_container.pos_invoice_usecase.pos_invoice_end_of_day_auto_close(property)
        _publish_step(property, "close_invoices", "completed")

        new_date_settings = app_container.property_setting_usecase.property_setting_increase_business_date(property)
        bzns_date = new_date_settings.get("business_date_int")
        bzns_date_int = new_date_settings.get("business_date")
        opening_entry = app_container.pos_opening_entry_usecase.pos_opening_entry_find_by_property(property)
        closing_entry = {}
        if opening_entry and isinstance(opening_entry, str):
            _publish_step(property, "closing_entry", "in-progress")
            closing_entry = app_container.pos_opening_entry_usecase.pos_closing_entry_from_opening_name({
                "opening_entry": opening_entry,
                "commit": False
            })

            _publish_step(property, "closing_entry", "completed")

        _publish_step(property, "new_opening_entry", "in-progress")

        if bzns_date and bzns_date_int:
            new_opening_entry_params = property_setting_to_pos_opening_entry(property_setting, property)
            new_opening_entry = app_container.pos_opening_entry_usecase.pos_opening_entry_upsert({
                "doc": new_opening_entry_params,
                "commit": False,
            })
            _publish_step(property, "new_opening_entry", "completed")

            _publish_step(property, "new_invoices", "in-progress")
            pos_invoices = app_container.reservation_usecase.sync_reservations_to_pos_invoices(
                bzns_date,
                bzns_date_int,
                app_container.pos_invoice_usecase.pos_invoice_upsert
            )
            _publish_step(property, "new_invoices", "completed")
        frappe.db.commit()
        sleep(.3)
        _publish_step(property, "end", "completed")
    except frappe.ValidationError:
        frappe.db.rollback()
        raise
    except Exception as e:
        frappe.db.rollback()
        raise Exception(f"Unexpected Error: {str(e)}")
    finally:
        _publish_step(property, "end", "completed")


@frappe.whitelist()
def property_eod(property: str, auto_mark_no_show: bool=False, auto_session_close: bool=False):
    frappe.db.begin()
    frappe.flags.in_install = True
    try:
        property_setting = app_container.property_setting_usecase.property_setting_find(property)
        if not property_setting:
            raise frappe.NotFound(f"Property {property} Not Found")

        business_date_int = property_setting["business_date_int"]
        opening_entries = app_container.pos_opening_entry_usecase.pos_opening_entry_find_by_property(property)
        closing_entries = []




        new_date_settings = app_container.property_setting_usecase.property_setting_increase_business_date(property)
        updated_reservations = app_container.reservation_usecase.reservation_end_of_day_auto_mark(property, auto_mark_no_show)
        new_business_date_int = new_date_settings["business_date_int"]
        new_opening_entry_params = property_setting_to_pos_opening_entry(new_date_settings, property)
        app_container.pos_opening_entry_usecase.pos_opening_entry_upsert({
            "doc": new_opening_entry_params,
            "commit": False,
        })

        invoices = app_container.reservation_usecase.get_inhouse_reservations_invoices(new_business_date_int)

        for inv in invoices:
            items = json.loads(inv.pop('items', '[]'))
            doc = frappe.get_doc({
                "doctype": "POS Invoice",
                **inv
            })
            for item in items:
                doc.append("items", item)
            doc.append("payments", {
                    "mode_of_payment": "Cash",
                    "amount": 0
                })
            doc.insert()

        for entry in opening_entries:
            entry_name = entry["name"]
            if auto_session_close:
                app_container.pos_session_usecase.pos_sessions_close_for_date_profile(business_date_int,entry_name)
            invoices = frappe.get_all(
                    "POS Invoice",
                filters={"for_date": business_date_int, "docstatus": 0 , "pos_profile" : entry["pos_profile"]},
                    fields=["name" , "pos_profile"]
                )
            for invoice in invoices:
                invoice_doc = frappe.get_doc("POS Invoice" , invoice["name"])
                if invoice_doc:
                    invoice_doc.submit()
            closing_entry = app_container.pos_opening_entry_usecase.pos_closing_entry_from_opening_name({
                    "opening_entry": entry_name
                })
            closing_entry.submit()
    except:
        frappe.db.rollback()
        raise
    finally:
        frappe.flags.in_install = False
