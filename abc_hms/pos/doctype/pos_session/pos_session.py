import frappe
from frappe.model.document import Document
class POSSession(Document):
    @frappe.whitelist()
    def get_current_bussiness_date(self):
        business_date = frappe.db.sql("""
        select date_to_int(s.business_date) business_date from `tabPOS Profile` p
            JOIN `tabProperty Setting` s on p.property = s.name and p.name = %s
        """,(self.pos_profile) , pluck=['business_date'])
        return business_date[0]
    def validate(self):
        if self.pos_profile and self.for_date:
            current_business_date = self.get_current_bussiness_date()
            if current_business_date and self.for_date != current_business_date:
                frappe.throw(
                    f"Business date mismatch. Expected: {current_business_date} Got: {self.for_date}",
                    title="Invalid Business Date"
                )
            opening_entry = frappe.db.exists("POS Opening Entry" , {
                "for_date" : self.for_date,
                "pos_profile" : self.pos_profile,
                "status": 'Open'
            })
            if not opening_entry:
                frappe.throw(f"POS Profile {self.pos_profile} has no POS Opening Entry for date {self.for_date}")
    def autoname(self):
        if self.pos_profile and not self.for_date:
            self.for_date = self.get_current_bussiness_date()

        owner = getattr(self, 'owner', None) or frappe.session.user
        owner_abbr = frappe.get_value("User" , owner , "cashier_abbriviation")
        if owner_abbr:
            owner = owner_abbr
        self.name = f"S-{owner}-{self.pos_profile}-{self.for_date}"
