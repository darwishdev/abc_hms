import frappe
import json
from abc_hms.container import app_container
from abc_hms.dto.property_room_date_dto import RoomDateBulkUpsertRequest, RoomDateBulkUpsertResponse

@frappe.whitelist(methods=["POST", "PUT"])
def room_date_bulk_upsert() -> RoomDateBulkUpsertResponse:
    try:
        data = frappe.local.request.data
        payload: RoomDateBulkUpsertRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success": False, "error": f"{str(e)}"}

    result = app_container.room_date_usecase.room_date_bulk_upsert(payload)
    return result
