from typing import List
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice
import frappe
from pydantic import ValidationError

from abc_hms.dto.pos_invoice_dto import POSInvoiceData, PosInvoiceFindForDateRequest, PosInvoiceFindForDateResponse, PosInvoiceItemTransferRequest, PosInvoiceItemUpdateRequest, PosInvoiceUpsertRequest, PosInvoiceUpsertResponse
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



    def pos_invoice_item_transfer(
        self,
        params: PosInvoiceItemTransferRequest
    ):
        try:
            result = self.repo.pos_invoice_item_transfer(
                params
            )
            return result
        except Exception as e:
            raise e
    def pos_invoice_item_update_widnow(
        self,
        params: PosInvoiceItemUpdateRequest
    ):
        try:
            result = self.repo.pos_invoice_item_update_widnow(
                params["name"],
                params["folio_window"]
            )
            return result
        except Exception as e:
            raise e
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
            result = self.repo.pos_invoice_upsert(request['doc'],commit=request['commit'])
            return result
        except frappe.ValidationError as e:
            raise frappe.ValidationError(f"POS Invoice validation failed: {e}")

        except TypeError as e:
            tb = frappe.get_traceback()
            if (
                "cannot unpack non-iterable NoneType object" in str(e)
                and "pos_invoice.py" in tb
                and "set_pos_fields" in tb
            ):
                raise frappe.ValidationError(f"Customer not found or has missing default configuration")
            raise TypeError(f"Type error: {str(e)}")
        except Exception as e:
            raise e

