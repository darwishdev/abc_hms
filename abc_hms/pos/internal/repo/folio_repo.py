import json
from typing import List, Optional
import frappe
from sentry_sdk.utils import json_dumps
from abc_hms.dto.pos_folio_dto import FolioInsertRequest, FolioItem
from abc_hms.pos.doctype.folio.folio import Folio
from abc_hms.pos.doctype.folio_window.folio_window import FolioWindow
from utils.sql_utils import run_sql


class FolioRepo:
    def folio_window_list(self, folio: str):
        return frappe.get_all(
            "Folio Window",
            {
                "Folio": folio,
            },
            ["name", "window_label"],
        )

    def folio_item_transfer(
        self,
        source_folio,
        destination_folio,
        destination_window,
        source_window,
        item_names,
    ):
        folio = frappe.get_doc("Folio", source_folio)
        return folio.folio_item_transfer(
            destination_folio, destination_window, source_window, item_names
        )

    def folio_insert(self, request: FolioInsertRequest):
        try:
            if not frappe.db.exists("POS Profile", request["pos_profile"]):
                raise frappe.NotFound(f"POS Profile {request['pos_profile']} Not Found")
            frappe.db.begin()
            folio_doc = frappe.new_doc("Folio")
            folio_doc.update(
                {
                    "pos_profile": request["pos_profile"],
                    "reservation": (
                        request["reservation"] if "reservation" in request else None
                    ),
                    "restaurant_table": request["restaurant_table"],
                }
            )

            folio_doc.save()
            business_date = frappe.db.sql(
                """
                select  date_to_int(s.business_date) for_date                 from
                `tabPOS Profile` p
                  JOIN `tabProperty Setting` s
                  on p.property = s.name
                  where p.name = %s
            """,
                request["pos_profile"],
                pluck="for_date",
            )
            if len(business_date) != 1:
                raise frappe.NotFound(
                    "this pos profile attached to property but property settings are not set properly"
                )

            for_date = business_date[0]
            for item in request["items"]:
                item["folio_window"] = f"{folio_doc.name}-w-001"
            new_invoce = {
                "customer": request["guest"] if "guest" in request else None,
                "number_of_guests": (
                    request["number_of_guests"]
                    if "number_of_guests" in request
                    else None
                ),
                "pos_profile": request["pos_profile"],
                "folio": folio_doc.name,
                "naming_series": f"PI-{folio_doc.name}-{for_date}-.####",
                "for_date": for_date,
                "items": request["items"],
                "payments": [
                    {
                        "mode_of_payment": "Cash",
                        "folio_window": f"{folio_doc.name}-w-001",
                        "amount": 0,
                    }
                ],
            }
            invoice_doc = frappe.new_doc("POS Invoice")
            invoice_doc.update(new_invoce)
            invoice_doc.save()
            frappe.db.commit()

            return {"folio": folio_doc.as_dict(), "invoice": invoice_doc.as_dict()}

        except Exception as e:
            frappe.db.rollback()
            raise e

    def folio_upsert(self, docdata: Folio, commit: bool = True) -> Folio:
        folio_name = docdata.get("name")
        if folio_name and frappe.db.exists("Folio", folio_name):
            doc: Folio = frappe.get_doc("Folio", folio_name)  # type: ignore
        else:
            doc: Folio = frappe.new_doc("Folio")  # type: ignore
        doc.update(docdata)
        doc.save(ignore_permissions=True)
        if commit:
            frappe.db.commit()

        return doc

    def folio_window_upsert(
        self, docdata: FolioWindow, commit: bool = True
    ) -> FolioWindow:
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
        pos_profile: str,
        docstatus: Optional[str],
        reservation: Optional[str],
        guest: Optional[str],
        room: Optional[str],
        arrival_from: Optional[str],
        arrival_to: Optional[str],
        departure_from: Optional[str],
        departure_to: Optional[str],
        include_paymaster: Optional[bool],
    ) -> List[FolioItem]:
        def procedure_call(cur, _):
            cur.execute(
                """
            CALL folio_list_filtered(%s, %s, %s, %s, %s, %s, %s, %s, %s,%s);
        """,
                (
                    pos_profile,
                    docstatus,
                    reservation,
                    guest,
                    room,
                    arrival_from,
                    arrival_to,
                    departure_from,
                    departure_to,
                    include_paymaster == "true",
                ),
            )
            return cur.fetchall()

        folios: List[FolioItem] = run_sql(procedure_call)  # type: ignore
        return folios

    def folio_find(self, folio: str, pos_profile: str):
        def procedure_call(cur, _):
            cur.execute(
                """
            CALL folio_find(%s , %s);
        """,
                (folio, pos_profile),
            )

            return cur.fetchall()

        folios = run_sql(procedure_call)
        if len(folios) == 0:
            raise frappe.NotFound(f"No Folio With Name : {folio}")

        return folios[0]

    def folio_merge(
        self,
        source_folio: str,
        destination_folio: str,
        destination_window: str,
        keep_source_folio: bool = False,
    ):
        folio = frappe.get_doc("Folio", source_folio)
        if not folio:
            raise frappe.NotFound("Folio Not Found")
        return folio.folio_merge(
            destination_folio, destination_window, keep_source_folio
        )

        # try:
        # source_folio_doc = frappe.get_doc("Folio" , source_folio)
        # destination_folio_doc = frappe.get_doc("Folio" , destination_folio)
        # folio_invoices = frappe.get_all("POS Invoice" , {
        #     "folio" : source_folio,
        #     "docstatus" : 1
        # } , pluck="name")
        # doc_updates = {
        #     invoice_name: {"folio": destination_folio}
        #     for invoice_name in folio_invoices
        # }
        # frappe.db.bulk_update("POS Invoice" , doc_updates)
        #
        # source_active_invoice = frappe.get_doc("POS Invoice" , source_folio_doc.folio_active_invoice())
        # destination_active_invoice = frappe.get_doc("POS Invoice" , destination_folio_doc.folio_active_invoice())
        # for item in source_active_invoice.items:
        #     # Append a new row to the destination invoice's 'items' table
        #     # and get a reference to the newly created row
        #     new_item = destination_active_invoice.append('items', {})
        #
        #     # Copy the necessary fields from the source item to the new destination item
        #     # Note: You should only copy fields relevant to an invoice item and avoid
        #     # copying system-managed fields like 'name', 'parent', 'idx', etc.
        #     # The list below covers common essential fields.
        #
        #     new_item.item_code = item.item_code
        #     new_item.folio_window = destination_window
        #     new_item.item_name = item.item_name
        #     new_item.qty = item.qty
        #     new_item.rate = item.rate
        #     new_item.amount = item.amount
        #     new_item.base_rate = item.base_rate
        #     new_item.base_amount = item.base_amount
        #     new_item.uom = item.uom
        # destination_active_invoice.calculate_taxes_and_totals()
        # destination_active_invoice.save(ignore_permissions=True)
        #
        # frappe.db.sql("""
        # CALL folio_merge_submitted_invoices(%s,%s,%s);
        # """ , (source_folio , destination_folio, destination_window))
        #
        # frappe.db.commit()
        # return frappe.get_doc("Folio" , destination_folio)
        # except:
        #     raise
