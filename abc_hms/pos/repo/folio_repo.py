import frappe
from abc_hms.pos.doctype.folio.folio import Folio
from abc_hms.pos.doctype.folio_window.folio_window import FolioWindow

class FolioRepo:
    def folio_upsert(self, docdata: Folio, commit: bool = True) -> Folio:
        folio_name = docdata.get("name")
        if folio_name and frappe.db.exists("Folio", folio_name):
            doc: Folio = frappe.get_doc("Folio", folio_name) # type: ignore
        else:
            doc: Folio = frappe.new_doc("Folio")  # type: ignore
            doc.update(docdata)
        doc.save(ignore_permissions=True)
        if commit:
            frappe.db.commit()

        return doc


    def folio_window_upsert(self, docdata:FolioWindow, commit: bool = True) -> FolioWindow:
        folio_window_name = docdata.get("name")
        existing = frappe.db.exists("Folio", folio_window_name)
        if existing:
            doc: FolioWindow = frappe.get_doc("Folio Window", folio_window_name)  # type: ignore
        else:
            doc: FolioWindow = frappe.new_doc("Folio Window")  # type: ignore
            doc.update(docdata)

        doc.save(ignore_permissions=True)
        if commit:
            frappe.db.commit()

        return doc

