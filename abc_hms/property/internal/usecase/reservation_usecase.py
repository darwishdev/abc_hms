import re

from datetime import datetime
import json
from time import sleep
from typing import List
from pydantic import ValidationError
from pymysql import err as pymysql_err
import frappe
from frappe import Optional, utils


from erpnext.accounts.doctype.pos_closing_entry.pos_closing_entry import make_closing_entry_from_opening
from frappe.utils import now_datetime, nowdate, nowtime
from abc_hms.dto.pos_invoice_dto import POSInvoiceData, PosInvoiceUpsertRequest, PosInvoiceUpsertResponse
from abc_hms.dto.property_dto import PropertyEndOfDayRequest
from utils import date_utils
from ..repo.reservation_repo import ReservationRepo

class ReservationUsecase:
    def __init__(self) -> None:
        self.repo = ReservationRepo()


    def get_inhouse_reservations(self , business_date: int):
        try:
            return self.repo.get_inhouse_reservations(
                business_date
            )
        except Exception as e:
            raise Exception(f"unexpected error: {str(e)}")


    def reservation_end_of_day_auto_mark(self , payload: PropertyEndOfDayRequest):
        return self.repo.reservation_end_of_day_auto_mark(
            payload.get("property"),
            bool(payload.get("auto_mark_no_show" , False)),
        )

    def reservation_departures_for_current_date(self , property: str)->Optional[List[str]]:
        result = self.repo.reservation_departures_for_current_date(property)
        return result
    def reservation_arrivals_for_current_date(self , property: str)->Optional[List[str]]:
        result = self.repo.reservation_arrivals_for_current_date(property)
        return result
    def end_of_day(
        self,
        params : dict | None =None,
    ):
        frappe.publish_progress(10, title="End Of Day", description="Getting Current Bussiness Date")
        property_business_date = frappe.db.get_value(
            "Property Setting",
            {"property": params["property"]},
            "business_date",
            for_update=True
        )
        yesterday_date = utils.add_days(property_business_date, -1)
        tomorrow_date = utils.add_days(property_business_date, 1)
        business_date_int = date_utils.date_to_int(property_business_date)
        tomorrow_date_int = date_utils.date_to_int(tomorrow_date)

        print("arrivals quer11" , tomorrow_date_int)
        sleep(0.3)
        frappe.publish_progress(15, title="End Of Day", description=f"Ending Day {str(property_business_date)}")

        yesterday_date = utils.add_days(property_business_date, -1)


            # find invoices from yesterday
        yesterday_invoices = frappe.get_all(
            "POS Invoice",
            filters={"for_date": date_utils.date_to_int(yesterday_date)},
            fields=["name", "pos_profile" , "customer" , "grand_total" , "posting_date", "posting_time"  ,"docstatus"]
        )
        if yesterday_invoices:
            # submit all draft invoices from yesterday
            pos_transactions = []
            for inv in yesterday_invoices:
                if inv.docstatus == 0:  # 0 = Draft, 1 = Submitted, 2 = Cancelled
                    doc = frappe.get_doc("POS Invoice", inv.name)
                    doc.submit()
                pos_transactions.append({
                    "doctype": "POS Invoice Reference",  # child table doctype
                    "customer": inv.customer,
                    "pos_invoice": inv.name,
                    "date": inv.posting_date,
                    "amount": inv.grand_total
                })
            pos_profile = yesterday_invoices[0].pos_profile
            opening_entry = frappe.get_all(
                "POS Opening Entry",
                filters={
                    "pos_profile": pos_profile,
                    "docstatus": 1,  # submitted
                    "status": "Open"
                },
                order_by="creation desc",
                limit=1,
            )
            if opening_entry:
                yesterday_opening = frappe.get_doc("POS Opening Entry", opening_entry[0].name)
                closing_entry = make_closing_entry_from_opening(yesterday_opening)
                closing_entry.insert(ignore_permissions=True)
                new_opening = frappe.new_doc("POS Opening Entry")
                new_opening.pos_profile = yesterday_opening.pos_profile
                new_opening.company = yesterday_opening.company
                new_opening.user = yesterday_opening.user
                new_opening.period_start_date = property_business_date
                new_opening.balance_details = []

                pos_profile_doc = frappe.get_doc("POS Profile", yesterday_opening.pos_profile)
            # Build balance_details from POS Profile payments
                for payment in pos_profile_doc.payments:
                    new_opening.append("balance_details", {
                        "mode_of_payment": payment.mode_of_payment,
                        "opening_amount": 0.0,   # start fresh for the new day
                        "closing_amount": 0.0
                    })
                new_opening.insert(ignore_permissions=True)
                new_opening.submit()
            # ✅ cancel this case (skip new draft creation)
        reservation_data = self.repo.get_inhouse_reservations(str(property_business_date))
        for row in reservation_data:
            if not row.get("item_name"):  # check if item not set
                existing_item = frappe.db.exists("Item", {"name": row["new_item_name"]})
                if not existing_item:
                    item = frappe.get_doc({
                        "doctype": "Item",
                        "name": row["new_item_name"],
                        "item_code": row["new_item_name"],
                        "item_name": row["new_item_name"],
                        "description": f"Auto-created item for room type {row['room_type']} and rate code {row['rate_code']}",
                        "stock_uom": row.get("stock_uom") or "Nos",
                        "is_sales_item": 1,
                        "is_purchase_item": 0,
                        "item_group": "Rooms",   # make sure this group exists
                        "default_currency": row.get("currency") or "EGP",
                    })
                    item.insert(ignore_permissions=True)
                    row["item_code"] = item.item_code
                    row["item_name"] = item.item_name
                    row["item_description"] = item.description
                    row["stock_uom"] = item.stock_uom

                    sleep(0.3)
                    frappe.publish_progress(25, title="End Of Day", description=f"Creating Invoices")

            frappe.db.commit()
                # if invoice missing → create draft POS Invoice

            if  not row.get("folio_window") or row.get("folio_window") is None:
                window_name = row['new_folio_window']

                folio_window = frappe.get_doc({
                    "doctype": "Folio Window",
                    "name": window_name,
                    "window_code": row["new_folio_window"],
                    "window_label": "01",
                    "folio": row["folio"],               # bind folio
                })
                # save as draft, not submit
                folio_window.insert(ignore_permissions=True)

                row["folio_window"] = folio_window.name

            if  not row.get("invoice") or row.get("invoice") is None:
                invoice_name = f"INV-{business_date_int}-{row['reservation']}"
                pos_invoice = frappe.get_doc({
                    "doctype": "POS Invoice",
                    "naming_series": invoice_name,
                    "currency": row["currency"],
                    "customer": row["guest"],
                    "for_date": business_date_int,
                    "folio": row["folio"],               # bind folio
                    "set_posting_time": 1,
                    "posting_date": frappe.utils.nowdate(),
                    "items": [
                        {
                            "for_date": business_date_int,
                            "item_name": row["new_item_name"],
                            "description": row["new_item_name"],
                            "folio_window": row["folio_window"],
                            "income_account" : "4120 - Room Revenue - CH",
                            "uom": row["stock_uom"],
                            "qty": 1,
                            "rate": row["base_rate"],
                            "amount": row["base_rate"],
                        }
                    ],
                    "payments": [
                                {
                                    "mode_of_payment": "Cash",   # you can pick your default mode
                                    "amount": 0,
                                    "folio_window": row["folio_window"],
                                    "for_date": business_date_int,
                                    "currency": row["currency"],
                                }
                        ],
                })

                # save as draft, not submit
                pos_invoice.insert(ignore_permissions=True)

                row["invoice"] = pos_invoice.name
        tomorrow = self.repo.mark_tomorrow_reservations(tomorrow_date_int)
        print("tomorrw" , tomorrow)

        # update business_date
        frappe.db.set_value(
            "Property Setting",
            {"property": params["property"]},
            "business_date",
            tomorrow_date
        )
        sleep(0.3)
        frappe.publish_progress(100, title="End Of Day", description=f"Items Created For All Room Types And Rate Code Combinations")
        return {"status" : "Success" , "reservation_data" : reservation_data}

    def reservation_to_pos_invoice(self , reservation: dict) -> dict:
        now = datetime.now()
        posting_date = now.strftime("%Y-%m-%d")
        posting_time = now.strftime("%H:%M:%S")

        return {
            "customer": reservation["guest"],
            "posting_date": posting_date,
            "posting_time": posting_time,
            "currency": reservation["currency"],
            "company": reservation["company"],
            "is_pos": 1,
            "folio": reservation["folio"].upper(),  # Example: make folio uppercase
            "number_of_guests": reservation["number_of_guests"],
            "naming_series": reservation["new_pos_invoice_naming_series"],
            "for_date": reservation["for_date"],
            "items": [
                {
                    "item_name": reservation["item_name"],
                    "item_code": reservation["item_code"],
                    "item_description": reservation["item_description"],
                    "stock_uom": reservation["stock_uom"],
                    "currency": reservation["currency"],
                    "exchange_rate": reservation["exchange_rate"],
                    "rate": reservation["base_rate"],
                    "amount": reservation["base_rate"],  # rate * qty
                    "for_date": reservation["for_date"],
                    "qty": 1,
                    "folio_window": reservation["folio_window"],
                }
            ],
            "payments": [
                {
                    "mode_of_payment": "Cash",
                    "amount": 0
                }
            ]
        }

    def reservation_availability_check(
        self,
        params : dict | None =None,
    ):
        print("params")
        print(params)
        if params:
            return self.repo.reservation_availability_check(params)
        return frappe.throw("should select filters")

    def sync_reservations_to_pos_invoices(self, business_date: int , default_rooms_group: str, upsert_pos_invoice_method ):
        # Step 1: fetch reservations
        reservations = self.get_inhouse_reservations(
            business_date
        )
        responses: list[PosInvoiceUpsertResponse] = []
        for reservation in reservations:
            invoice_doc: POSInvoiceData = self.reservation_to_pos_invoice(reservation) # type: ignore
            request: PosInvoiceUpsertRequest = {
                "doc": invoice_doc,
                "commit": False,
            }
            try:
                response = upsert_pos_invoice_method(request)

            except frappe.ValidationError as e:
                msg = str(e)
                match = re.search(r"Item (.+?) not found", msg)
                if match:
                    item_code = match.group(1)
                    frappe.get_doc({
                        "doctype": "Item",
                        "item_code": item_code,
                        "item_group": default_rooms_group,
                        "item_name": item_code,
                        "description": item_code,
                        "stock_uom": "Nos",   # 👈 adjust if you want a different default
                        "is_sales_item": 1,
                        "is_stock_item": 0,
                    }).insert(ignore_permissions=True)
                    frappe.db.commit()

                    response = upsert_pos_invoice_method(request)
                raise
            except Exception:
                raise

            responses.append(response)

        return responses
