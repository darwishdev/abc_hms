
import json
from click import pause
import frappe
from typing import  Any, Dict, List
from frappe import NotFound, Optional, _, destroy
from frappe.rate_limiter import update
from pydantic import ValidationError
from sentry_sdk.utils import json_dumps
from abc_hms.dto.pos_invoice_dto import POSInvoiceData, PosInvoiceItemTransferRequest
from utils.date_utils import date_to_int
from utils.sql_utils import run_sql
class POSInvoiceRepo:

    def pos_invoice_find_for_date(
        self,
        for_date: int,
        fields: Optional[List[str]] = None,
    ) -> List[POSInvoiceData]:
        try:
            default_fields = [
                "name",
                "pos_profile",
                "customer",
                "grand_total",
                "posting_date",
                "posting_time",
                "docstatus"
            ]

            fields_to_fetch = fields or default_fields

            invoices = frappe.get_all(
                "POS Invoice",
                filters={"for_date": for_date},
                fields=fields_to_fetch
            )

            return invoices

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "POS Invoice Find For Date Error")
            raise


    def pos_invoice_item_update_widnow(
        self ,
        names : List[str] ,
        folio_window:str
    ):
        def run_update(cur , conn):
            names_arg = ','.join(names)
            query = f"""
            UPDATE `tabPOS Invoice Item` i
            SET
            i.folio_window = coalesce(%s,i.folio_window)
            where FIND_IN_SET(i.name, %s)
            """
            cur.execute(query,(folio_window,names_arg))
            conn.commit()
            return

        return run_sql(run_update)


    def pos_invoice_item_transfer(self , payload: PosInvoiceItemTransferRequest):
        try:
            frappe.db.begin()
            source_invoice = frappe.get_doc("POS Invoice", payload["source_invoice"])
            if not source_invoice:
                raise NotFound(f"the source invoice not found {payload['source_invoice']}")
            if "destination_invoice" in payload:
                dest_invoice = frappe.get_doc("POS Invoice", payload['destination_invoice'])

            if "destination_folio" in payload:
                pos_profile = frappe.db.get_value("POS Invoice" , payload["source_invoice"] ,
                                                  "pos_profile")
                business_date = frappe.db.sql("""
                    SELECT date_to_int(s.business_date) for_date FROM
                    `tabPOS Profile` p join `tabProperty Setting` s on p.property = s.name where
                    p.name = %s
                                              """ , pos_profile , pluck=['for_date'])

                if len(business_date) != 1:
                    raise frappe.NotFound("this pos profile attached to property but property settings are not set properly")

                for_date = business_date[0]
                dest_invoices = frappe.get_all("POS Invoice",{
                    "folio" : payload["destination_folio"],
                    "for_date" : for_date
                } , pluck="name")
                if len(dest_invoices) == 0:
                    raise frappe.NotFound("Destination Folio Don not Have POS Invoce For Current Business Date")
                dest_invoice = frappe.get_doc("POS Invoice" , dest_invoices[0])
            if not dest_invoice:
                raise NotFound(f"the source invoice not found {payload['destination_invoice']}")
            items_passed = 'items' in payload
            for item in source_invoice.items:
                if item.folio_window == payload["source_window"] and (not items_passed or item.name in
                                                                          payload["items"]):
                    source_invoice.remove(item)
                    dest_invoice.append("items" , item)

            if not items_passed:
                frappe.db.sql("update `tabFolio Window` fw SET fw.folio = %s where name = %s" ,
                              ( dest_invoice.folio ,payload["source_window"]) )
            source_invoice.save()
            dest_invoice.save()
            frappe.db.commit()
            return dest_invoice
        except:
            frappe.db.rollback()
            raise
    def pos_invoice_update(self, doc ,docdata,  commit):
        payments = docdata.pop("payments", None)
        items = docdata.pop("items", None)
        for key, value in docdata.items():
            if key not in ("items", "payments") and value != "" and value is not None:
                setattr(doc, key, value)
        if items is not None:
            for row in items:
                row_name = row.get("name")

                if row_name:
                    existing_row = next((i for i in doc.items if i.name == row_name), None)

                    if existing_row:
                        setattr(existing_row,"pos_session",  frappe.local.pos_session)
                        for field, val in row.items():
                            if field not in ("name", "parent", "parentfield", "parenttype") and val not in ("", None):
                                setattr(existing_row, field, val)
                else:
                    doc.append("items", row)

        if payments is not None:
            for row in payments:
                row["pos_session"] = frappe.local.pos_session
                doc.append("payments", row)

        doc.set_missing_values()
        doc.calculate_taxes_and_totals()
        doc.save()
        if hasattr(doc, "set_pos_fields"):
            doc.set_pos_fields()
        if commit:
            frappe.db.commit()
        invoice : POSInvoiceData = doc.as_dict() # type: ignore

        return invoice
    def pos_invoice_upsert(self , docdata: POSInvoiceData,reset_items: bool = True,reset_payments: bool = True, commit: bool = True)->POSInvoiceData:
        doc_names : List[str] = frappe.db.sql(
            """
                SELECT name from `tabPOS Invoice`
                WHERE name = %s OR (
                               docstatus = 0 AND
                               pos_profile = %s
                               AND folio = %s
                               AND for_date = %s
                               )
            """ ,
             (docdata.get("name"),
             docdata.get("pos_profile" , "Main"),
             docdata.get("folio"),
             docdata.get("for_date"),
              ),
            pluck="name") # type: ignore
        if doc_names and len(doc_names) > 0:
            doc_name = doc_names[len(doc_names) - 1]

            doc: POSInvoiceData = frappe.get_doc("POS Invoice", doc_name) # type: ignore


            if docdata.get("docstatus") == 1:
                docdata["submitted_at_session"] = frappe.local.pos_session

            return self.pos_invoice_update(doc , docdata ,  commit)

        doc: POSInvoiceData = frappe.new_doc("POS Invoice") # type: ignore
        docdata["issued_at_session"] = frappe.local.pos_session
        return self.pos_invoice_update(doc , docdata ,   commit)





    def pos_invoice_end_of_day_auto_close(self, business_date : int):
        invoices = frappe.get_all(
            "POS Invoice",
            filters={"for_date": date_to_int(business_date), "docstatus": 0},
            fields=["name"]
        )

        # 3️⃣ Submit each invoice via Frappe Doc API
        for inv in invoices:
            doc = frappe.get_doc("POS Invoice", inv.name)
            try:
                doc.submit()
            except frappe.ValidationError as e:
                frappe.log_error(f"Error submitting POS Invoice {inv.name}: {e}")

        return {"submitted": [inv.name for inv in invoices]}
