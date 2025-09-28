from typing import List, Optional
import frappe
from abc_hms.dto.pos_folio_dto import FolioInsertRequest, FolioItem
from abc_hms.pos.doctype.folio.folio import Folio
from abc_hms.pos.doctype.folio_window.folio_window import FolioWindow
from utils.sql_utils import run_sql

class FolioRepo:

    def folio_insert(self, request : FolioInsertRequest):
        try:
            if not frappe.db.exists("POS Profile" , request["pos_profile"]):
                raise frappe.NotFound(f"POS Profile {request['pos_profile']} Not Found")
            frappe.db.begin()
            folio_doc = frappe.new_doc("Folio")
            folio_doc.update({
                "pos_profile" : request["pos_profile"],
                "reservation" : request["reservation"] if "reservation" in request else None,
                "restaurant_table" : request["restaurant_table"],
            })

            folio_doc.save()
            business_date = frappe.db.sql("""
                select  date_to_int(s.business_date) for_date                 from
                `tabPOS Profile` p
                  JOIN `tabProperty Setting` s
                  on p.property = s.name
                  where p.name = %s
            """ , request["pos_profile"] , pluck="for_date")
            if len(business_date) != 1:
                raise frappe.NotFound("this pos profile attached to property but property settings are not set properly")

            for_date = business_date[0]
            for item in request["items"]:
                item["folio_window"] = f"{folio_doc.name}-w-001"
            new_invoce = {
                "customer" : request["guest"] if "guest" in request else None,
                "number_of_guests" : request["number_of_guests"] if "number_of_guests" in request else None,
                "pos_profile" : request["pos_profile"],
                "folio" : folio_doc.name,
                "naming_series" : f"PI-{folio_doc.name}-{for_date}-.####",
                "for_date": for_date,
                "items" : request["items"],
                "payments" : [{
                    "mode_of_payment" : "Cash",
                    "folio_window" :  f"{folio_doc.name}-w-001",
                    "amount" : 0
                }]
            }
            invoice_doc = frappe.new_doc("POS Invoice")
            invoice_doc.update(new_invoce)
            invoice_doc.save()
            frappe.db.commit()

            return {
                "folio" : folio_doc.as_dict(),
                "invoice" : invoice_doc.as_dict()
            }

        except Exception as e:
            frappe.db.rollback()
            raise e
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

    def folio_merge(self,source_folio : str,destination_folio : str , destination_window : str):
        try:
            frappe.db.begin()
            folio_invoices = frappe.get_all("POS Invoice" , {
                "folio" : source_folio
            } , pluck="name")
            doc_updates = {
                invoice_name: {"folio": destination_folio}
                for invoice_name in folio_invoices
            }
            frappe.db.bulk_update("POS Invoice" , doc_updates)
            frappe.db.sql("""
            update `tabPOS Invoice Item` i join `tabFolio Window` fw on i.folio_window = fw.name and fw.folio = %s set i.folio_window = %s
            """ , (source_folio , destination_window))

            frappe.db.commit()
            return frappe.get_doc("Folio" , destination_folio)
        except:
            frappe.db.rollback()
            raise
