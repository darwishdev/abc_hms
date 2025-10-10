from typing import List
from click import Option
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice
import frappe
from frappe import Optional, _
from frappe.utils import  add_days, flt
from pydantic import ValidationError

from utils.date_utils import date_to_int
class CustomPOSInvoice(POSInvoice):
    def pos_invoice_item_transfer(self , destination_folio: str ,destination_window : str , source_window: str ,item_names:Optional[List[str]] ):
        destination_folio_doc = frappe.get_doc("Folio" , destination_folio)
        destination_folio_invoice_doc = destination_folio_doc.folio_active_invoice_doc()
        for item in self.items:
            item_dict = item.as_dict()
            if item_dict['name'] in item_names:
                new_item = item_dict.copy()
                new_item["parent"] = destination_folio_invoice_doc.name
                new_item["idx"] = None
                new_item["name"] = None
                new_item['folio_window'] = destination_window
                destination_folio_invoice_doc.append('items' , new_item)
                destination_folio_invoice_doc.calculate_taxes_and_totals()
                self.remove(item)
                destination_folio_invoice_doc.save()
                self.calculate_taxes_and_totals()
                self.save()

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

