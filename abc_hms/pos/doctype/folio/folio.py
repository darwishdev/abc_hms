import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class Folio(Document):
    def autoname(self):
        self.name = make_autoname(f"F-{self.reservation}-.######")

    def after_insert(self):
        try:
            window_doc: FolioWindow = frappe.new_doc("Folio Window")  # type: ignore
            window_doc.folio = self.name
            window_doc.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Folio after_insert: Failed to create Folio Window for {self.name}")
            raise e
