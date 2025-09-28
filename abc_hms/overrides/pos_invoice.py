from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice
from frappe import _
from frappe.utils import  flt
class CustomPOSInvoice(POSInvoice):
    def validate_change_amount(self):
        self.change_amount = 0
        self.base_change_amount = 0

