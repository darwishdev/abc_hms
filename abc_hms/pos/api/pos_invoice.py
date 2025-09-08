
import frappe
from frappe.exceptions import MandatoryError
import pymysql.cursors
import pymysql
from frappe import _
import json
from typing import Dict, TypedDict, List, Optional



class PaymentDict(TypedDict):
    mode_of_payment: str
    amount: float
    account: Optional[str]
    folio_window: Optional[str]


class InvoiceDict(TypedDict, total=False):
    customer: str
    number_of_guests: Optional[int]
    room_number: Optional[str]
    table_number: Optional[str]
    pos_session: Optional[str]
    payments: List[PaymentDict]


@frappe.whitelist(allow_guest=False, methods=["POST", "PUT"])
def pos_invoice_upsert(invoice_id: str, invoice: Dict):
    if not invoice or not isinstance(invoice, dict):
        frappe.throw("Invoice payload must be a dict")

    payments = invoice.pop("payments", [])

    # ----------------
    # 1. Load or create
    # ----------------
    if frappe.db.exists("POS Invoice", invoice_id):
        doc = frappe.get_doc("POS Invoice", invoice_id)
        doc.update(invoice)
    else:
        if not invoice.get("customer"):
            frappe.throw("Customer is required when creating a new invoice")
        doc = frappe.new_doc("POS Invoice")
        doc.name = invoice_id
        doc.update(invoice)

    # ----------------
    # 2. Handle payments
    # ----------------
    if payments:
        doc.set("payments", [])
        for pay in payments:
            if not pay.get("mode_of_payment") or not pay.get("amount"):
                frappe.throw("Each payment must have mode_of_payment and amount")
            doc.append("payments", {
                "mode_of_payment": pay["mode_of_payment"],
                "amount": float(pay["amount"]),
                "account": pay.get("account"),
                "folio_window": pay.get("folio_window"),
            })

    # ----------------
    # 3. Save (with retry if mandatory fields missing in items)
    # ----------------
    try:
        doc.save()
    except MandatoryError as e:
        if "item_name" in str(e) or "description" in str(e) or "uom" in str(e):
            # Fix items
            for it in doc.get("items", []):
                if not it.item_name:
                    it.item_name ="asd"
                if not it.description:
                    it.description = "asd"
                if not it.uom:
                    it.uom = "Unit"

            # retry save
        else:
            raise

    frappe.db.commit()

    return {
        "ok": True,
        "invoice_id": doc.name,
        "docstatus": doc.docstatus,
        "invoice": doc.as_dict(),
    }
@frappe.whitelist()
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
        void_bin = frappe.get_doc({
            "doctype": "POS Invoice Voide Bin",   # check Doctype spelling!
            "pos_invoice": item_row.parent,
            "cause": cause,
            "created_by": frappe.session.user,
            "item": item_row.item_code,
            "quanitity": item_row.qty,            # your Doctype field spelling
        })
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
            }
        }

    except Exception as e:
        # Rollback everything if any step failed
        frappe.db.rollback()
        frappe.log_error(f"folio_item_void failed: {str(e)}", "POS Void Error")
        raise






@frappe.whitelist(allow_guest=False, methods=["POST", "PUT"])
def pos_invoice_item_bulk_upsert(invoice_id: str,  items: list[dict]):
    """
    API Endpoint: Bulk upsert POS Invoice Items into `tabPOS Invoice Item` using stored procedure.

    Args:
        invoice_id (str): Target POS Invoice ID (parent).
        items (list[dict]): List of item dicts, each with keys like:
            - item_code (required, str)
            - qty (required, float)
            - name (optional, str)
            - item_name (optional, str)
            - uom (optional, str)
            - rate (optional, float)
            - amount (optional, float)
            - folio_window (optional, str)
            - description (optional, str)

    Returns:
        dict: {
            "ok": True,
            "invoice_id": str,
            "count": int,
            "total_amount": float,
            "total_qty": float,
            "items": list[dict]
        }
    """
    user = frappe.session.user
    # Validate input
    if not items:
        frappe.throw("No items provided")

    # Validate required fields
    for i, item in enumerate(items):
        if not item.get("item_code"):
            frappe.throw(f"Item {i+1}: item_code is required")
        if not item.get("qty") and item.get("qty") != 0:
            frappe.throw(f"Item {i+1}: qty is required")

    # Convert items list to JSON object format expected by stored procedure
    json_data = {
        "names":         [i.get("name", "") for i in items],
        "item_codes":    [i.get("item_code", "") for i in items],
        "item_names":    [i.get("item_name", "") for i in items],
        "descriptions":  [i.get("description", "") for i in items],
        "uoms":          [i.get("uom", "") for i in items],
        "qtys":          [float(i.get("qty", 0)) for i in items],
        "rates":         [float(i.get("rate", 0)) for i in items],
        "amounts":       [float(i.get("amount", 0)) for i in items],
        "folio_windows": [i.get("folio_window", "") for i in items],
    }
    try:
        # Use direct connection approach for stored procedures
        conn = frappe.db.get_connection()
        cur = conn.cursor(pymysql.cursors.DictCursor)

        query = "CALL pos_invoice_item_bulk_upsert(%s,%s,%s)"
        cur.execute(query, (invoice_id, user, json.dumps(json_data)))
        result = cur.fetchall()
        cur.close()

        # Calculate totals from returned data
        total_amount = sum(float(row.get('base_amount', 0)) for row in result)
        total_qty = sum(float(row.get('qty', 0)) for row in result)

        conn.commit()

        return {
            "ok": True,
            "invoice_id": invoice_id,
            "count": len(result),
            "total_amount": total_amount,
            "total_qty": total_qty,
            "items": result
        }

    except Exception as e:
        # Don't rollback if connection is already closed
        if frappe.db and hasattr(frappe.db, '_cursor') and frappe.db._cursor:
            try:
                frappe.db.rollback()
            except:
                # Connection might be closed, ignore rollback errors
                pass

        error_msg = str(e)
        frappe.log_error(f"Failed bulk upsert for invoice {invoice_id}: {error_msg}\nJSON Data: {json_data}", "POS Invoice Bulk Upsert")
        frappe.throw(f"Error adding invoice items: {error_msg}")
