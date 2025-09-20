
import frappe
import json
from abc_hms.container import app_container
from abc_hms.dto.pos_folio_dto import FolioUpsertRequest, FolioUpsertResponse

@frappe.whitelist(methods=["POST" , "PUT"])
def folio_upsert()-> FolioUpsertResponse:
    try:
        data = frappe.local.request.data
        payload: FolioUpsertRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    result = app_container.folio_usecase.folio_upsert(payload)
    return result

