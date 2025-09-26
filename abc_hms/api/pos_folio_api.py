
import frappe
import json

from pydantic import ValidationError
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
        args = frappe.form_dict
        if not args.get("pos_profile"):
            raise ValidationError("pos_profile is required")
        payload: FolioListFilteredRequest = {
            "pos_profile": args.get("pos_profile"),
            "docstatus": args.get("docstatus"),
            "reservation": args.get("reservation"),
            "guest": args.get("guest"),
            "room": args.get("room"),
            "arrival_from": args.get("arrival_from"),
            "arrival_to": args.get("arrival_to"),
            "departure_from": args.get("departure_from"),
            "departure_to": args.get("departure_to"),
        }
    except Exception as e:
        raise frappe.ValidationError(f"Invalid Request {str(e)}")

    result = app_container.folio_usecase.folio_list_filtered(payload)
    return  result

