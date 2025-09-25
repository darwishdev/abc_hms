from typing import List, Optional
import frappe
from abc_hms.dto.pos_folio_dto import FolioItem
from abc_hms.pos.doctype.folio.folio import Folio
from abc_hms.pos.doctype.folio_window.folio_window import FolioWindow
from utils.sql_utils import run_sql

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



    def folio_list_filtered(
            self,
            pos_profile : str ,
            docstatus: Optional[str],
            reservation: Optional[str],
            guest: Optional[str],
            room: Optional[str],
            arrival_from: Optional[str],
            arrival_to: Optional[str],
            departure_from: Optional[str],
            departure_to: Optional[str]
    )-> List[FolioItem]:
        def procedure_call(cur ,_):
            cur.execute("""
            CALL folio_list_filtered(%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
                pos_profile ,
                docstatus ,
                reservation ,
                guest ,
                room ,
                arrival_from ,
                arrival_to ,
                departure_from ,
                departure_to,
             ))
            return cur.fetchall()

        folios : List[FolioItem] = run_sql(procedure_call) # type: ignore
        return folios

    def folio_find(self,folio : str):
        def procedure_call(cur ,_):
            cur.execute("""
            CALL folio_find(%s);
        """, (
                folio
            ))

            return cur.fetchall()
        folios = run_sql(procedure_call)
        if len(folios) == 0:
            raise frappe.NotFound(f"No Folio With Name : {folio}")

        return folios[0]

