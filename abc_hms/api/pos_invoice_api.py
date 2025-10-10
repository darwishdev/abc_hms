import frappe
import json
from abc_hms.api.decorators import business_date_protected
from abc_hms.container import app_container
from abc_hms.dto.pos_invoice_dto import  PosInvoiceFindForDateRequest, PosInvoiceFindForDateResponse, PosInvoiceItemTransferRequest, PosInvoiceItemUpdateRequest, PosInvoiceUpsertRequest, PosInvoiceUpsertResponse


@frappe.whitelist(methods=["POST" , "PUT"])
@business_date_protected
def pos_invoice_item_void(item_row_id: str, cause: str):
    """
    Securely void a POS Invoice Item:
      - Copy its details into POS Invoice Void Bin
      - Delete it from tabPOS Invoice Item
    Entire process is atomic (rollback if any step fails).
    """
    try:
        # --- Step 1: Load the item row ---
        item_row = frappe.db.get_value(
            "POS Invoice Item",
            item_row_id,
            "parent, item_code, qty",
            as_dict=True,
        )
        if not item_row:
            frappe.throw(_("POS Invoice Item not found"))

        # --- Step 2: Create Void Bin entry ---
        void_bin = frappe.get_doc(
            {
                "doctype": "POS Invoice Voide Bin",  # check Doctype spelling!
                "pos_invoice": item_row.parent,
                "cause": cause,
                "created_by": frappe.session.user,
                "item": item_row.item_code,
                "quanitity": item_row.qty,  # your Doctype field spelling
            }
        )
        void_bin.insert(ignore_permissions=True)

        # --- Step 3: Delete the item row ---
        frappe.db.delete("POS Invoice Item", {"name": item_row_id})

        # --- Step 4: Commit transaction ---
        frappe.db.commit()

        return {
            "ok": True,
            "voided_item": {
                "pos_invoice": item_row.parent,
                "item_code": item_row.item_code,
                "qty": item_row.qty,
                "cause": cause,
            },
        }

    except Exception as e:
        # Rollback everything if any step failed
        frappe.db.rollback()
        frappe.log_error(f"folio_item_void failed: {str(e)}", "POS Void Error")
        raise

@frappe.whitelist(methods=["GET"])
def currency_list():
    try:
        currencies = frappe.db.sql(
            """
            SELECT 'EGP' as name , 1 as exchange_rate
            UNION
             SELECT DISTINCT c.name , e.exchange_rate
            FROM `tabCurrency` c
            JOIN `tabCurrency Exchange` e
                ON e.from_currency = c.name
        """,
            as_dict=True,
        )
        return currencies
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}


@frappe.whitelist(methods=["POST" , "PUT"])
@business_date_protected
def pos_invoice_upsert()-> PosInvoiceUpsertResponse:
    try:
        data = frappe.local.request.data
        payload: PosInvoiceUpsertRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    doc = payload.get("doc")
    doc["for_date"] = frappe.local.business_date
    doc["pos_profile"] = frappe.local.pos_profile
    result = app_container.pos_invoice_usecase.pos_invoice_upsert(
        payload.get("doc"),
        payload.get("reset_items"),
        payload.get("reset_payments"),
        True
    )
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

