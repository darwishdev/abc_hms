from typing import List
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice
import frappe

from abc_hms.dto.pos_invoice_dto import POSInvoiceData, PosInvoiceFindForDateRequest, PosInvoiceFindForDateResponse, PosInvoiceUpsertRequest, PosInvoiceUpsertResponse
from ..repo.pos_invoice_repo import POSInvoiceRepo
from frappe import  _

class POSInvoiceUsecase:
    def __init__(self):
        self.repo = POSInvoiceRepo()

    def pos_invoice_end_of_day_auto_close(
        self,
        property: str,
    ) :
        return self.repo.pos_invoice_end_of_day_auto_close(
            property
        )

    def pos_invoice_find_for_date(
        self,
        params: PosInvoiceFindForDateRequest,
    ) -> PosInvoiceFindForDateResponse:
        """Fetch POS invoices for a given date"""
        try:
            result: List[POSInvoiceData] = self.repo.pos_invoice_find_for_date(
                params.get("for_date"), params.get("fields")
            )
            return {
                "success": True,
                "invoices": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"POS Invoice Find For Date Error: {str(e)}",
            }
    def pos_invoice_upsert(
        self,
        request :PosInvoiceUpsertRequest,
    ) -> PosInvoiceUpsertResponse:
        try:
            result = self.repo.pos_invoice_invoice(request['doc'],commit=request['commit'])
            return {"success" : False , "doc" :result}
        except frappe.ValidationError as e:
            frappe.log_error(f"POS Invoice validation failed: {e}")
            raise

        except TypeError as e:
            tb = frappe.get_traceback()
            if (
                "cannot unpack non-iterable NoneType object" in str(e)
                and "pos_invoice.py" in tb
                and "set_pos_fields" in tb
            ):
                frappe.throw(
                    _("Customer not found or has missing default configuration"),
                    exc=frappe.ValidationError,
                )
            frappe.throw(
                str(e),
            )
            return {"success" : False , "error" : f"Type error: {str(e)}"}
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "POS Invoice Upsert API Error")
            frappe.throw(
                str(e),
            )
            return {"success" : False , "error" : f"Unexpected error: {str(e)}"}

