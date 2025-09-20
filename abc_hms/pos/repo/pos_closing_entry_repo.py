import frappe
from frappe import _

from abc_hms.dto.pos_closing_entry_dto import POSClosingEntry
class POSClosingEntryRepo:
    def pos_closing_entry_upsert(self , docdata: POSClosingEntry, commit: bool = True):
        doc_id = docdata.get('name' , None)
        if doc_id and frappe.db.exists("POS Closing Entry", doc_id):
            doc: POSClosingEntryData = frappe.get_doc("POS Closing Entry", doc_id) # type: ignore
        else:
            doc: POSClosingEntryData = frappe.new_doc("POS Closing Entry") # type: ignore

        doc.update(docdata)
        doc.save()
        if commit:
            frappe.db.commit()

        return {
            "ok": True,
            "doc": doc.as_dict(),
        }
