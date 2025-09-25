
import frappe
import json
from abc_hms.container import app_container
from abc_hms.dto.pos_folio_dto import FolioListFilteredResponse, FolioUpsertRequest,  FolioListFilteredRequest

@frappe.whitelist(methods=["POST" , "PUT"])
def folio_upsert():
    try:
        data = frappe.local.request.data
        payload: FolioUpsertRequest = json.loads(data or "{}")
    except Exception as e:
        raise frappe.ValidationError(f"Invalid Request {str(e)}")

    result = app_container.folio_usecase.folio_upsert(payload)
    return result


@frappe.whitelist(methods=["GET"])
def folio_find(folio: str):
    result = app_container.folio_usecase.folio_find(folio)
    return  result

@frappe.whitelist(methods=["GET"])
def folio_list_filtered():
    try:
        data = frappe.local.request.data
        payload: FolioListFilteredRequest = json.loads(data or "{}")
    except Exception as e:
        raise frappe.ValidationError(f"Invalid Request {str(e)}")

    result = app_container.folio_usecase.folio_list_filtered(payload)
    return  result

