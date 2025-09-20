import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
class POSSession(Document):
    @frappe.whitelist()
    def get_defaults(self):
        from abc_hms.api.pos_session_api import pos_session_defaults_find
        if self.pos_profile or self.for_date:
            return
        if not self.get("property"):
            return frappe.throw("Property is required to generate name")
        property = str(self.get("property"))
        defaults_resp = pos_session_defaults_find(property)
        if not defaults_resp.get("success"):
            return frappe.throw("property settings not set")


        if defaults_resp.get("success") and defaults_resp.get("doc"):
            defaults = defaults_resp.get("doc")
            if defaults:
                self.pos_profile = defaults.get("pos_profile" , None)
                self.for_date = defaults.get("for_date" , None)
        if not self.for_date:
            return frappe.throw("for_date is required to generate name")

    def autoname(self):
        self.get_defaults()
        self.name = make_autoname(f"S-{self.get('property')}-{self.get('for_date')}-.######")
