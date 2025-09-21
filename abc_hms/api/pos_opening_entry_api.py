import frappe
import json
from abc_hms.container import app_container
from abc_hms.dto.pos_opening_entry_dto import POSClosingEntryFromOpeningRequest, POSClosingEntryFromOpeningResponse, POSOpeningEntryFindByProfileRequest, POSOpeningEntryFindByProfileResponse, POSOpeningEntryUpsertRequest, POSOpeningEntryUpsertResponse


@frappe.whitelist(methods=["POST" , "PUT"])
def pos_opening_entry_upsert()-> POSOpeningEntryUpsertResponse:
    try:
        data = frappe.local.request.data
        payload: POSOpeningEntryUpsertRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    result = app_container.pos_opening_entry_usecase.pos_opening_entry_upsert(payload)
    return result

@frappe.whitelist(methods=["GET"])
def pos_opening_entry_find_by_profile() -> POSOpeningEntryFindByProfileResponse:
    try:
        data = frappe.local.request.data
        payload: POSOpeningEntryFindByProfileRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success": False, "error": f"{str(e)}"}

    result = app_container.pos_opening_entry_usecase.pos_opening_entry_find_by_profile(payload)
    return result

@frappe.whitelist(methods=["POST"])
def pos_closing_entry_from_opening() -> POSClosingEntryFromOpeningResponse:
    try:
        data = frappe.local.request.data
        payload: POSClosingEntryFromOpeningRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success": False, "error": f"{str(e)}"}

    result = app_container.pos_opening_entry_usecase.pos_closing_entry_from_opening_name(payload)
    return result
