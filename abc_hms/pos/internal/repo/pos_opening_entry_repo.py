from typing import Dict, List
from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import POSClosingEntry
import frappe
from frappe import Optional, _
from sentry_sdk.utils import json_dumps

from abc_hms.dto.pos_opening_entry_dto import POSOpeningEntryData
class POSOpeningEntryRepo:


    def pos_opening_entry_find_by_pos_profile(self , pos_profile: str , for_date: int):
        results =  frappe.db.sql("""
                                SELECT e.name ,
                                e.pos_profile
                                FROM `tabPOS Opening Entry` e
                                WHERE e.docstatus = 1
                                AND e.status = 'Open'
                                AND e.pos_profile = %(pos_profile)s
                                AND e.for_date = %(for_date)s
                                ORDER BY e.name DESC
                                LIMIT 1
                            """ ,
                                 {"pos_profile" :pos_profile , "for_date" : for_date} , as_dict=True)
        return results[0] if len(results) > 0 else None

    def pos_opening_entry_find_by_property(self , property: str):
        results =  frappe.db.sql("""
                                SELECT e.name ,
                                e.pos_profile,
                                (e.pos_profile = default_pos_profile) is_default
                                FROM `tabPOS Opening Entry` e
                                JOIN `tabProperty Setting` s
                                on s.property = %(property)s
                                AND e.docstatus = 1
                                AND e.status = 'Open'
                            """ ,
                                {"property" :property} , as_dict=True)

        return results
    def pos_opening_entry_find(self , name: str) -> POSOpeningEntryData:
        response : POSOpeningEntryData = frappe.get_doc("POS Opening Entry", name) # type: ignore
        return response

    def pos_opening_entry_upsert(self , docdata: POSOpeningEntryData, commit: bool = True) -> POSOpeningEntryData:
        doc_id = docdata.get('name' , None)
        if doc_id and frappe.db.exists("POS Opening Entry", doc_id):
            doc: POSOpeningEntryData = frappe.get_doc("POS Opening Entry", doc_id) # type: ignore
        else:
            doc: POSOpeningEntryData = frappe.new_doc("POS Opening Entry") # type: ignore


        doc.update(docdata)

        doc.save()
        if commit:
            frappe.db.commit()

        return doc
