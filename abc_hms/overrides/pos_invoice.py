from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice
import frappe
from frappe import _
from frappe.utils import  add_days, flt
from pydantic import ValidationError

from utils.date_utils import date_to_int
class CustomPOSInvoice(POSInvoice):
    def validate_for_date(self):
        if self.for_date:
            current_date = frappe.db.sql("""
            SELECT  s.business_date from `tabProperty Setting` s JOIN
            `tabPOS Profile` p ON p.name = %s and p.property = s.name
            """ , self.pos_profile , pluck="business_date")
            if not current_date:
                errmsg = f"Please setup property setting the property attached to this pos profile : {self.pos_profile}"
                frappe.throw(errmsg , exc=frappe.ValidationError)
                raise frappe.ValidationError(errmsg)

            if len(current_date) == 0:
                frappe.throw(f"Please setup property setting the property attached to this pos profile : {self.pos_profile}")
            current_date_int = date_to_int(current_date[0])
            yesterday_date = add_days(current_date[0], -1)
            yesterday_date_int = date_to_int(yesterday_date)
            if str(self.for_date) != str(current_date_int):
                if self.docstatus != 1:
                    frappe.throw(
                        f"For Date must be {str(str(current_date_int) == str(self.for_date))} {current_date_int}. Current value: {self.for_date} ",
                        exc=frappe.ValidationError
                    )
                if self.for_date != yesterday_date_int:
                    frappe.throw(
                        f"Submitted Documents for_date must be {str(yesterday_date_int)} or {str(current_date_int)}. Current value: {self.for_date} ",
                        exc=frappe.ValidationError
                    )
    def validate(self):
        """Override validate method to add custom validation."""
        # Validate for_date field
        self.validate_for_date()

        # Call parent validate method to keep all existing validations
        super().validate()
    def validate_change_amount(self):
        self.change_amount = 0
        self.base_change_amount = 0

