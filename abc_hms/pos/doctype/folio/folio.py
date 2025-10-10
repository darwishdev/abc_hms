import ast
from typing import Dict, List, Optional
import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from sentry_sdk.utils import json_dumps

from utils.sql_utils import run_sql


class Folio(Document):
    def autoname(self):
        doc = self.as_dict()
        reservation = doc['reservation']
        restaurant_table = doc['restaurant_table']
        if not reservation and restaurant_table:
            self.name = make_autoname(f"F-{restaurant_table}-.######")
            return
        if reservation:
            self.name = make_autoname(f"F-{reservation}-.######")

    def folio_active_invoice_doc(self):
        invoice_name = self.folio_active_invoice()
        if invoice_name and isinstance(invoice_name , str):
            return frappe.get_doc("POS Invoice",invoice_name)
    def folio_invoice_list(self , docstatus: Optional[int] = None):
        filters : dict = {
                "folio" : self.name,
            }
        if docstatus:
            filters["docstatus"] = docstatus
        return frappe.get_all(
            "POS Invoice",
            filters
        )

    def folio_active_invoice(self):
        return frappe.db.get_value(
            "POS Invoice",
            {
                "folio" : self.name,
                "docstatus" : 0
            }
        )



    @frappe.whitelist()
    def folio_item_transfer(self ,destination_folio: str, destination_window: str , source_window: str ,item_names):
       item_names_csv = ",".join(item_names)
       transfer_submitted = frappe.db.sql("""
           CALL folio_transfer_submitted_items(%s,%s,%s);
           """,
            (destination_window,source_window,item_names_csv),
       )
       active_invoice_doc = self.folio_active_invoice_doc()
       active_invoice_doc.pos_invoice_item_transfer(destination_folio,destination_window,source_window,item_names)
    @frappe.whitelist()
    def folio_merge(self , destination_folio: str ,  destination_window: str):
        destination_folio_doc = frappe.get_doc("Folio" , destination_folio)
        source_active_invoice = self.folio_active_invoice_doc()
        dest_active_invoice = destination_folio_doc.folio_active_invoice_doc()
        if not source_active_invoice:
            frappe.throw(f"Folio {self.name} has no active invoice")
        for item in source_active_invoice.items:
            item.folio_window = destination_window
            item.parent = None
            dest_active_invoice.append('items' , item)

        dest_active_invoice.calculate_taxes_and_totals()
        dest_active_invoice.save()

        frappe.db.sql("""
        CALL folio_merge_submitted_invoices(%s,%s,%s);
        """ , (self.name , destination_folio, destination_window))
        frappe.msgprint(
                msg=f"✅ Successfully merged folio <b>{self.name}</b> into <b>{destination_folio_doc.name}</b> ({destination_window})",
                title="Folio Merge Successful",
                indicator="green",
            )
    @frappe.whitelist()
    def make_payment(self, mode_of_payment: str, amount: float , window: str):
        try:
            active_invoice = self.folio_active_invoice_doc()
            if not active_invoice:
                frappe.throw("No active POS Invoice found for this folio." , exc=frappe.ValidationError)
                return
            active_invoice.append("payments", {
                "mode_of_payment": mode_of_payment,
                "folio_window": window,
                "amount": amount
            })
            active_invoice.save()
            folio_balance = self.folio_find_balance()
            paid_amount = folio_balance.get("paid" , 0) + amount
            balance = folio_balance.get("amount") - paid_amount
            if balance > 1:
                self.folio_status = 'Partially Paid'
                self.save()
                return

            self.folio_status = 'Settled'
            self.save()
        except:
            frappe.db.rollback()
            raise

    @frappe.whitelist()
    def folio_submit(self):
        self.submit()
    @frappe.whitelist()
    def folio_find_balance(self , window: Optional[str] = None):
        def call_proc(cur , _):
            cur.execute(
                """
                CALL folio_find_balance(%s , %s)
                """,
                (self.name,
                window)
            )

            result : Optional[List[Dict]] = cur.fetchall() # type: ignore

            failed_err = f"Can't get balance for folio {self.name}"
            if window:
                failed_err += f"And Window {window}"
            if not result:
                raise Exception(failed_err)
            if len(result) == 0:
                raise Exception(failed_err)


            return result
        result = run_sql(call_proc)
        if window:
            return {"balance" : result[0], "result" : result}
        folio_banlance = {"amount":0,"paid":0}
        for windo_balance in result:
            folio_banlance["amount"] += windo_balance["amount"]
            folio_banlance["paid"] += windo_balance["paid"]
        return {"balance" : folio_banlance , "result" : result}
    def before_submit(self):
        reservation = self.as_dict()['reservation']
        if reservation:
            reservation_doc = frappe.get_doc("Reservation" , reservation)
            if reservation_doc.as_dict()['reservation_status'] != 'Departure':
                frappe.throw(f"Folio cann't be submitted unless the linked reservation departure date is today")

        active = self.folio_active_invoice()
        balance_result = self.folio_find_balance()
        balance_dict = balance_result.get("balance")
        amount  = balance_dict.get('amount')
        paid = balance_dict.get('paid')
        if amount:
            balance  = float(amount) - float(paid or 0)
            if float(balance) > 1 :
                # frappe.throw(f"Folio required amount is {amount} , paid amount is {paid} and Balance is {balance}")
                raise frappe.ValidationError(f"folio_blanace_issue:{json_dumps(balance_result)}")
        invoices = frappe.get_all("POS Invoice" , {"folio" : self.name} , pluck="name")
        for invoice in invoices:
            invoice_doc = frappe.get_doc("POS Invoice" ,invoice)
            invoice_doc.submit()


    def after_submit(self):
        reservation = frappe.get_doc("Reservation" , self.reservation)
        if reservation:
            reservation.reservation_status = 'Checked Out'
            reservation.save()
    def after_insert(self):
        try:
            window_doc: FolioWindow = frappe.new_doc("Folio Window")  # type: ignore
            window_doc.folio = self.name
            window_doc.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), f"Folio after_insert: Failed to create Folio Window for {self.name}")
            raise e

