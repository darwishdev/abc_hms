from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import make_closing_entry_from_opening
import frappe

from abc_hms.dto.pos_opening_entry_dto import (
    POSClosingEntryFromOpeningRequest ,
    POSClosingEntryFromOpeningResponse,
    POSOpeningEntryFindByProfileRequest,
    POSOpeningEntryFindByProfileResponse ,
    POSOpeningEntryUpsertRequest,
    POSOpeningEntryUpsertResponse
)
from frappe import _

from abc_hms.pos.repo.pos_opening_entry_repo import POSOpeningEntryRepo

class POSOpeningEntryUsecase:
    def __init__(self):
        self.repo = POSOpeningEntryRepo()


    def pos_opening_entry_find_by_property(
        self,
        property: str,
    ):
        try:
            return self.repo.pos_opening_entry_find_by_property(property)
        except frappe.ValidationError as e:
            frappe.log_error(f"POS opening_entry validation failed: {e}")
            raise

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "POS opening_entry Upsert API Error")
            return {"success" : False , "error" : f"Unexpected error: {str(e)}"}
    def pos_opening_entry_upsert(
        self,
        request :POSOpeningEntryUpsertRequest,
    ) -> POSOpeningEntryUpsertResponse:
        try:
            result = self.repo.pos_opening_entry_upsert(request['doc'],commit=request['commit'])
        except frappe.ValidationError as e:
            frappe.log_error(f"POS opening_entry validation failed: {e}")
            raise

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "POS opening_entry Upsert API Error")
            return {"success" : False , "error" : f"Unexpected error: {str(e)}"}

        return {
            "success": True,
            "doc": result["doc"],
        }

    def pos_closing_entry_from_opening(
        self,
        request :POSClosingEntryFromOpeningRequest,
    ) -> POSClosingEntryFromOpeningResponse:
        try:
            pos_opening_entry = self.repo.pos_opening_entry_find(request["opening_entry"])
            closing_entry = make_closing_entry_from_opening(pos_opening_entry)
            closing_entry.insert(ignore_permissions=True)
            if request["commit"]:
                frappe.db.commit()
            doc: POSClosingEntry = closing_entry.as_dict() # type: ignore
            return { "success" : True  ,"doc": doc}
        except frappe.ValidationError as e:
            frappe.log_error(f"POS closing_entry validation failed: {e}")
            raise

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "POS closing_entry Upsert API Error")
            return {"success" : False , "error" : f"Unexpected error: {str(e)}"}
