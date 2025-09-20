from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import POSClosingEntry
import frappe
from frappe import Optional, _

from abc_hms.dto.pos_opening_entry_dto import POSOpeningEntryData
class POSOpeningEntryRepo:


    def pos_opening_entry_find_by_property(self , property: str):
       return frappe.db.sql("""
                                SELECT e.name
                                FROM `tabPOS Opening Entry` e
                                JOIN `tabProperty Setting` s
                                on s.property = %s
                                AND e.for_date = date_to_int(s.business_date)
                                AND e.pos_profile = default_pos_profile
                                AND e.docstatus = 1
                                AND e.status = 'Open'
                            """ ,
                            (property,))
    def pos_opening_entry_find(self , name: str) -> POSOpeningEntryData:
        response : POSOpeningEntryData = frappe.get_doc("POS Opening Entry", name) # type: ignore
        return response

    def pos_opening_entry_upsert(self , docdata: POSOpeningEntryData, commit: bool = True):
        doc_id = docdata.get('name' , None)
        if doc_id and frappe.db.exists("POS Opening Entry", doc_id):
            doc: POSOpeningEntryData = frappe.get_doc("POS Opening Entry", doc_id) # type: ignore
        else:
            doc: POSOpeningEntryData = frappe.new_doc("POS Opening Entry") # type: ignore

        doc.update(docdata)
        doc.save()
        if commit:
            frappe.db.commit()

        return {
            "ok": True,
            "doc": doc.as_dict(),
        }
