import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from sentry_sdk.utils import json_dumps


class Folio(Document):
    def autoname(self):
        if not self.reservation and self.restaurant_table:
            self.name = make_autoname(f"F-{self.restaurant_table}-.######")
            return
        self.name = make_autoname(f"F-{self.reservation}-.######")


    def can_submit(self):
        result = frappe.db.sql(
            """
            WITH items AS (
                SELECT
                    i.folio_window,
                    SUM(i.amount) AS amount
                FROM `tabPOS Invoice Item` i
                GROUP BY i.folio_window
            ), payments AS (
                SELECT
                    p.folio_window,
                    SUM(p.amount) AS amount
                FROM `tabSales Invoice Payment` p
                GROUP BY p.folio_window
            )
            SELECT
                fw.name AS folio_window,
                COALESCE(items.amount, 0) AS amount,
                COALESCE(payments.amount, 0) AS paid
            FROM `tabReservation` r
            JOIN `tabFolio` f ON f.reservation = r.name
            JOIN `tabFolio Window` fw ON fw.folio = f.name
            LEFT JOIN items ON fw.name = items.folio_window
            LEFT JOIN payments ON fw.name = payments.folio_window
            WHERE f.name = %s
            """,
            (self.name,),
            as_dict=True,
        )

        if not result:
            return False  # no folio, cannot check out

        row = result[0]
        total_amount = row.get("amount") or 0
        total_paid = row.get("paid") or 0

        return total_amount == total_paid
    def before_submit(self):
        can_submit = self.can_submit()
        if not can_submit:
            frappe.throw(f"Folio Balance Not Zero")

        invoices = frappe.get_all("POS Invoice" , {"folio" : self.name} , pluck="name")
        for invoice in invoices:
            invoice_doc = frappe.get_doc("POS Invoice" ,invoice)
            invoice_doc.submit()

    def after_insert(self):
        try:
            window_doc: FolioWindow = frappe.new_doc("Folio Window")  # type: ignore
            window_doc.folio = self.name
            window_doc.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Folio after_insert: Failed to create Folio Window for {self.name}")
            raise e
