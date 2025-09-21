from erpnext.accounts.doctype.pos_opening_entry.pos_opening_entry import POSOpeningEntry
import frappe
from frappe.model.naming import make_autoname

class CustomPOSOpeningEntry(POSOpeningEntry):
    def autoname(self):
        if self.naming_series:
            self.name = make_autoname(self.naming_series + ".####")
        self.name = make_autoname(f"POE-{self.property}-{str(self.for_date)}-.####")

