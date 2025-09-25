import frappe
from frappe.model.document import Document
class POSSession(Document):
    @frappe.whitelist()
    def get_current_bussiness_date(self):
        business_date = frappe.db.sql("""
        select date_to_int(s.business_date) from `tabPOS Profile` p
            JOIN `tabProperty Setting` s on p.property = s.name and p.name = %s
        """,(self.pos_profile))
        self.for_date = business_date[0][0]
    def autoname(self):
        if self.pos_profile and not self.for_date:
            self.get_current_bussiness_date()
        self.name = f"S-{self.pos_profile}-{self.for_date}"
