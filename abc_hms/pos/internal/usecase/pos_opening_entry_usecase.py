from typing import Union
from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import POSClosingEntry, make_closing_entry_from_opening
import frappe

from abc_hms.dto.dto_helpers import ErrorResponse
from abc_hms.dto.pos_opening_entry_dto import (
    POSClosingEntryFromOpeningRequest ,
    POSOpeningEntryData,
    POSOpeningEntryUpsertRequest,
)

from ..repo.pos_opening_entry_repo import POSOpeningEntryRepo

class POSOpeningEntryUsecase:
    def __init__(self):
        self.repo = POSOpeningEntryRepo()


    def pos_opening_entry_find_by_pos_profile(
        self,
        pos_profile: str,
        for_date: int
    ):
        return self.repo.pos_opening_entry_find_by_pos_profile(pos_profile , for_date)
    def pos_opening_entry_find_by_property(
        self,
        property: str,
    ):
        return self.repo.pos_opening_entry_find_by_property(property)
    def pos_opening_entry_upsert(
        self,
        request :POSOpeningEntryUpsertRequest,
    ) -> POSOpeningEntryData:
        try:
            return self.repo.pos_opening_entry_upsert(request['doc'],commit=request['commit'])
        except frappe.ValidationError as e:
            frappe.log_error(f"POS opening_entry validation failed: {e}")
            raise

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "POS opening_entry Upsert API Error")
            raise Exception(f"Unexpected errors: {str(e)}")



    def pos_closing_entry_from_opening_name(
        self,
        request :POSClosingEntryFromOpeningRequest,
    ) -> POSClosingEntry:
        pos_opening_entry = self.repo.pos_opening_entry_find(request["opening_entry"])
        closing_entry = make_closing_entry_from_opening(pos_opening_entry)
        closing_entry.insert(ignore_permissions=True)
        # closing_entry.submit()
        return closing_entry
    def pos_closing_entry_from_opening(
        self,
        pos_opening_entry :POSOpeningEntryData,
        commit: bool,
    ) -> Union[POSClosingEntry , ErrorResponse]:
        try:
            closing_entry = make_closing_entry_from_opening(pos_opening_entry)
            closing_entry.insert(ignore_permissions=True)
            if commit:
                frappe.db.commit()
            doc: POSClosingEntry = closing_entry.as_dict() # type: ignore
            return doc
        except frappe.ValidationError as e:
            frappe.log_error(f"POS closing_entry validation failed: {e}")
            raise

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "POS closing_entry Upsert API Error")
            return {"success" : False , "error" : f"Unexpected error: {str(e)}"}
