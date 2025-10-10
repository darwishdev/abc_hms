import frappe

from abc_hms.dto.pos_closing_entry_dto import POSClosingEntryUpsertRequest, POSClosingEntryUpsertResponse
from frappe import _
from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import POSClosingEntry, make_closing_entry_from_opening
from ..repo.pos_closing_entry_repo import POSClosingEntryRepo

class POSClosingEntryUsecase:
    def __init__(self):
        self.repo = POSClosingEntryRepo()

    def pos_closing_entry_upsert(
        self,
        opening_entry :str,
    ) -> POSClosingEntryUpsertResponse:
        try:
            pos_opening_entry = self.repo.pos_opening_entry_find(opening_entry)

            closing_entry = make_closing_entry_from_opening({"name" : pos_opening_entry})
            return closing_entry

            closing_entry.insert(ignore_permissions=True)
            doc: POSClosingEntry = closing_entry.as_dict() # type: ignore
            return { "success" : True  ,"doc": doc}
        except frappe.ValidationError as e:
            frappe.log_error(f"POS closing_entry validation failed: {e}")
            raise

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "POS closing_entry Upsert API Error")
            return {"success" : False , "error" : f"Unexpected error: {str(e)}"}
