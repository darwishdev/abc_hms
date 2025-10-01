
import frappe
import json

from pydantic import ValidationError
from abc_hms.api.decorators import business_date_protected
from abc_hms.container import app_container
from abc_hms.dto.pos_folio_dto import FolioInsertRequest, FolioUpsertRequest,  FolioListFilteredRequest, FolioWindowUpsertRequest


@frappe.whitelist(methods=["POST"])
def folio_insert():
    try:
        data = frappe.local.request.data
        payload: FolioInsertRequest = json.loads(data or "{}")
    except Exception as e:
        raise frappe.ValidationError(f"Invalid Request {str(e)}")

    result = app_container.folio_usecase.folio_insert(payload)
    return result
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
@business_date_protected
def folio_find(folio: str):
    result = app_container.folio_usecase.folio_find(folio , frappe.local.pos_profile)
    return  result


@frappe.whitelist(methods=["PUT" , "POST"])
def folio_merge():
    try:
        data = frappe.local.request.data
        payload: FolioUpsertRequest = json.loads(data or "{}")
    except Exception as e:
        raise frappe.ValidationError(f"Invalid Request {str(e)}")

    result = app_container.folio_usecase.folio_merge(payload)
    return  result

@frappe.whitelist(methods=["GET"])
@business_date_protected
def folio_list_filtered():
    try:
        args = frappe.form_dict
        payload: FolioListFilteredRequest = {
            "pos_profile": frappe.local.pos_profile,
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


@frappe.whitelist(methods=["POST"])
def folio_window_upsert():
    try:
        data = frappe.local.request.data
        payload: FolioWindowUpsertRequest = json.loads(data or "{}")
    except Exception as e:
        raise frappe.ValidationError(f"Invalid Request {str(e)}")

    result = app_container.folio_usecase.folio_window_upsert(payload)
    return result
