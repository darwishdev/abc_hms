
import frappe
import json
from abc_hms.container import app_container
from abc_hms.dto.pos_opening_entry_dto import POSClosingEntryFromOpeningRequest, POSClosingEntryFromOpeningResponse, POSOpeningEntryFindByProfileRequest, POSOpeningEntryFindByProfileResponse, POSOpeningEntryUpsertRequest, POSOpeningEntryUpsertResponse

@frappe.whitelist(methods=["POST" , "PUT"])
def item_list()-> POSOpeningEntryUpsertResponse:
    try:
        data = frappe.local.request.data
        payload: POSOpeningEntryUpsertRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    result = app_container.pos_opening_entry_usecase.pos_opening_entry_upsert(payload)
    return result

