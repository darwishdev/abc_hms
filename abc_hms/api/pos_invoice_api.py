import frappe
import json
from abc_hms.api.decorators import business_date_protected
from abc_hms.container import app_container
from abc_hms.dto.pos_invoice_dto import  PosInvoiceFindForDateRequest, PosInvoiceFindForDateResponse, PosInvoiceItemTransferRequest, PosInvoiceItemUpdateRequest, PosInvoiceUpsertRequest, PosInvoiceUpsertResponse


@frappe.whitelist(methods=["POST" , "PUT"])
@business_date_protected
def pos_invoice_upsert()-> PosInvoiceUpsertResponse:
    try:
        data = frappe.local.request.data
        payload: PosInvoiceUpsertRequest = json.loads(data or "{}")
        payload["doc"]["for_date"] = frappe.local.business_date
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    result = app_container.pos_invoice_usecase.pos_invoice_upsert(payload , False)
    return result


@frappe.whitelist(methods=["POST"])
@business_date_protected
def pos_invoice_item_update_widnow():
    try:
        data = frappe.local.request.data
        payload: PosInvoiceItemUpdateRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    result = app_container.pos_invoice_usecase.pos_invoice_item_update_widnow(payload)
    return result
@frappe.whitelist(methods=["POST"])
@business_date_protected
def pos_invoice_item_transfer():
    try:
        data = frappe.local.request.data
        payload: PosInvoiceItemTransferRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    result = app_container.pos_invoice_usecase.pos_invoice_item_transfer(payload)
    return result

@frappe.whitelist(methods=["GET"])
@business_date_protected
def pos_invoice_find_for_date()-> PosInvoiceFindForDateResponse:
    try:
        data = frappe.local.request.data
        payload: PosInvoiceFindForDateRequest = json.loads(data or "{}")
        payload["for_date"] = frappe.local.business_date
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    result = app_container.pos_invoice_usecase.pos_invoice_find_for_date(payload)
    return result

