import frappe
import json
from abc_hms.container import app_container
from abc_hms.dto.pos_invoice_dto import  PosInvoiceFindForDateRequest, PosInvoiceFindForDateResponse, PosInvoiceUpsertRequest, PosInvoiceUpsertResponse


@frappe.whitelist(methods=["POST" , "PUT"])
def pos_invoice_upsert()-> PosInvoiceUpsertResponse:
    try:
        data = frappe.local.request.data
        payload: PosInvoiceUpsertRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    result = app_container.pos_invoice_usecase.pos_invoice_upsert(payload)
    return result

@frappe.whitelist(methods=["GET"])
def pos_invoice_find_for_date()-> PosInvoiceFindForDateResponse:
    try:
        data = frappe.local.request.data
        payload: PosInvoiceFindForDateRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    result = app_container.pos_invoice_usecase.pos_invoice_find_for_date(payload)
    return result

