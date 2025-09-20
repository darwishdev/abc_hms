import frappe
import json
from abc_hms.container import app_container
from abc_hms.dto.pos_closing_entry_dto import POSClosingEntryUpsertRequest, POSClosingEntryUpsertResponse


@frappe.whitelist(methods=["POST" , "PUT"])
def pos_closing_entry_upsert()-> POSClosingEntryUpsertResponse:
    try:
        data = frappe.local.request.data
        payload: POSClosingEntryUpsertRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    result = app_container.pos_closing_entry_usecase.pos_closing_entry_upsert(payload)
    return result
