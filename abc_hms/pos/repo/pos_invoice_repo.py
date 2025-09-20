
import frappe
from typing import  Any, Dict, List
from frappe import Optional, _
from abc_hms.dto.pos_invoice_dto import POSInvoiceData
class POSInvoiceRepo:

    def pos_invoice_find_for_date(
        self,
        for_date: int,
        fields: Optional[List[str]] = None,
    ) -> List[POSInvoiceData]:
        try:
            default_fields = [
                "name",
                "pos_profile",
                "customer",
                "grand_total",
                "posting_date",
                "posting_time",
                "docstatus"
            ]

            fields_to_fetch = fields or default_fields

            invoices = frappe.get_all(
                "POS Invoice",
                filters={"for_date": for_date},
                fields=fields_to_fetch
            )

            return invoices

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "POS Invoice Find For Date Error")
            raise
    def pos_invoice_invoice(self , docdata: POSInvoiceData, commit: bool = True)->POSInvoiceData:
        payments = docdata.get("payments", None)
        items = docdata.get("items", None)
        invoice_id = str(docdata.get("name"))
        if frappe.db.exists("POS Invoice", invoice_id):
            doc: POSInvoiceData = frappe.get_doc("POS Invoice", invoice_id) # type: ignore
        else:
            doc: POSInvoiceData = frappe.new_doc("POS Invoice") # type: ignore

        doc.update(docdata)

        if items is not None:
            doc.set("items", [])
            for row in items:
                doc.append("items", row)

        if payments is not None:
            doc.set("payments", [])
            for row in payments:
                doc.append("payments", row)

        doc.set_missing_values()
        if hasattr(doc, "set_pos_fields"):
            doc.set_pos_fields()

        doc.save()
        invoice : POSInvoiceData = doc.as_dict() # type: ignore
        if commit:
            frappe.db.commit()

        return invoice

    def pos_invoice_end_of_day_auto_close(self, property: str):
        frappe.db.sql("""
            UPDATE `tabPOS Invoice` p
            JOIN `tabProperty Setting` s on s.property = %s
            SET p.docstatus = 1
            WHERE p.docstatus = 0 and p.for_date = s.business_date
        """, (property,))
        return {}
