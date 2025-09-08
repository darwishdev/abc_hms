import json
import frappe
from frappe.utils import now

@frappe.whitelist(allow_guest=False, methods=["POST"])
def folio_window_upsert(folio_id: str, window_code: str, window_label: str = None, remarks: str = None):
   """
   Create or update a Folio Window record.
   """
   try:
       # Check if window already exists
       existing = frappe.db.get_value("Folio Window",
           {"parent": folio_id, "window_code": window_code}, "name")

       if existing:
           # Update existing
           doc = frappe.get_doc("Folio Window", existing)
           if window_label:
               doc.window_label = window_label
           if remarks:
               doc.remarks = remarks
           doc.save(ignore_permissions=True)
       else:
           # Create new
           doc = frappe.new_doc("Folio Window")
           doc.parent = folio_id
           doc.parenttype = "Folio"
           doc.parentfield = "folio_windows"
           doc.window_code = window_code
           doc.window_label = window_label or ""
           doc.remarks = remarks or ""
           doc.total_charges = 0.0
           doc.total_payments = 0.0
           doc.balance = 0.0
           doc.insert(ignore_permissions=True)

       frappe.db.commit()

       return {
           "ok": True,
           "folio_window_id": doc.name,
           "action": "updated" if existing else "created"
       }

   except Exception as e:
       frappe.db.rollback()
       frappe.throw(f"Error upserting folio window: {str(e)}")
@frappe.whitelist(allow_guest=False, methods=["GET"])
def folio_list(status=None):
    filters = {}
    if status is not None and status != "":
        filters['folio_status'] = status
    return frappe.get_all("Folio" , filters , [
       'name',
       'linked_reservation',
       'guest',
       'folio_status',
       'check_in_date',
       'check_out_date',
       'cashier',
       'total_charges',
       'total_payments',
       'balance'])

@frappe.whitelist(allow_guest=False, methods=["GET"])
def folio_find(folio_name=str):
    try:
        result = frappe.db.sql("""
            SELECT
                JSON_OBJECT(
                    'folio_name', f.name,
                    'reservation_id', f.linked_reservation,
                    'customer', f.guest,
                    'folio_status', f.folio_status,
                    'check_in_date', f.check_in_date,
                    'check_out_date', f.check_out_date,
                    'invoice',
                    (
                        SELECT
                            JSON_OBJECT(
                                'pos_invoice_id', i.name,
                                'invoice_date', i.posting_date,
                                'folio_windows',
                                (
                                    SELECT
                                        JSON_ARRAYAGG(
                                            JSON_OBJECT(
                                                'folio_window', fw.name,
                                                'window_code', fw.window_code,

                                                -- Items per window
                                                'items',
                                                (
                                                    SELECT
                                                        COALESCE(
                                                            JSON_ARRAYAGG(
                                                                JSON_OBJECT(
                                                                    'name', ii.name,
                                                                    'item_code', ii.item_code,
                                                                    'item_name', ii.item_name,
                                                                    'item_amount', ii.base_amount,
                                                                    'qty', ii.qty,
                                                                    'rate', ii.rate
                                                                )
                                                            ), JSON_ARRAY()
                                                        )
                                                    FROM `tabPOS Invoice Item` ii
                                                    WHERE ii.parent = i.name
                                                      AND ii.folio_window = fw.name
                                                ),

                                                -- Total amount per window
                                                'total_amount',
                                                (
                                                    SELECT COALESCE(SUM(ii.base_amount), 0)
                                                    FROM `tabPOS Invoice Item` ii
                                                    WHERE ii.parent = i.name
                                                      AND ii.folio_window = fw.name
                                                ),

                                                -- Total paid per window
                                                'total_paid',
                                                (
                                                    SELECT COALESCE(SUM(p.amount), 0)
                                                    FROM `tabSales Invoice Payment` p
                                                    WHERE p.parent = i.name
                                                      AND p.folio_window = fw.name
                                                )
                                            )
                                        )
                                    FROM `tabFolio Window` fw
                                    WHERE fw.parent = f.name
                                )
                            )
                        FROM `tabPOS Invoice` i
                        WHERE i.folio = f.name
                        LIMIT 1
                    )
                ) AS folio_details
            FROM `tabFolio` f
            WHERE f.name = %s;
        """, (folio_name,), as_dict=True)

        if result:
            return json.loads(result[0]['folio_details'])
        else:
            return None

    except Exception as e:
        frappe.log_error(f"Error fetching folio details: {str(e)}")
        raise
