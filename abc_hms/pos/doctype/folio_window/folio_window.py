import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class FolioWindow(Document):
    def autoname(self):
        self.name = make_autoname(f"{self.folio}-W-.###")
        self.window_label = self.name.split("-")[-1]

