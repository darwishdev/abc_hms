import frappe
import json
from abc_hms.container import app_container
from abc_hms.dto.pos_session_dto import POSSessionFindForDateRequest, POSSessionDefaultsFindResponse, POSSessionFindForDateResponse, POSSessionUpsertRequest, POSSessionUpsertResponse

@frappe.whitelist(methods=["GET"])
def pos_session_find_for_date()-> POSSessionFindForDateResponse:
    try:
        data = frappe.local.request.data
        payload: POSSessionFindForDateRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    result = app_container.pos_session_usecase.pos_session_find_for_date(payload.get("for_date") ,1)
    return result

@frappe.whitelist(methods=["POST" , "PUT"])
def pos_session_upsert()-> POSSessionUpsertResponse:
    try:
        data = frappe.local.request.data
        payload: POSSessionUpsertRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    result = app_container.pos_session_usecase.pos_session_upsert(payload)
    return result

@frappe.whitelist(methods=["GET"])
def pos_session_defaults_find(property_name: str) -> POSSessionDefaultsFindResponse:
    settings_resp = app_container.property_setting_usecase.property_setting_find(property_name)
    opening_entry:str = ""
    if settings_resp.get("success"):
        settings = settings_resp.get("doc")
        if settings:
            pos_profile = str(settings.get("default_pos_profile"))
            for_date = int(str(settings.get("business_date_int")))
            opening_entry = app_container.pos_opening_entry_usecase.pos_opening_entry_find_by_property(property_name)
            return {
                "success": True,
                "doc": {
                    "pos_profile": pos_profile,
                    "for_date": for_date,
                    "opening_entry": opening_entry,
                },
            }

    return {"success": True , "doc" : None}
