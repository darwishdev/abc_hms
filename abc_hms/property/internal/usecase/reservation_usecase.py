import json
import re
from datetime import datetime
import frappe

from abc_hms.dto.pos_invoice_dto import PosInvoiceUpsertRequest, PosInvoiceUpsertResponse
from abc_hms.exceptions.exceptions import AvailabilityError, RoomShareError
from ..repo.reservation_repo import ReservationRepo
class ReservationUsecase:
    def __init__(self) -> None:
        self.repo = ReservationRepo()



    def room_type_rate_list(self ,
            property: str,
            from_date: str,
            to_date: str,
            room_category: str,
            room_types: str,
):
            return self.repo.room_type_rate_list(
                property,
                from_date,
            to_date,
            room_category,
            room_types
            )
    def get_inhouse_reservations_invoices(self , for_date: int):
        try:
            return self.repo.get_inhouse_reservations_invoices(
                for_date
            )
        except Exception as e:
            raise Exception(f"unexpected error: {str(e)}")
    def get_inhouse_reservations(self , business_date: int):
        try:
            return self.repo.get_inhouse_reservations(
                business_date
            )
        except Exception as e:
            raise Exception(f"unexpected error: {str(e)}")



    def reservation_date_list(self ,reservation):
        return self.repo.reservation_date_list(reservation)
    def reservation_date_bulk_upsert(self ,args):
        return self.repo.reservation_date_bulk_upsert(args)

    def reservation_date_sync(self ,args:dict):
        try:
            discount_type = args["discount_type"]
            discount_value = args['discount_amount'] if discount_type == 'Value' else args['discount_percent']
            return self.repo.reservation_date_sync(
                args["name"],
                args["arrival"],
                args["departure"],
                args["docstatus"],
                args["reservation_status"],
                args["room_type"],
                args["rate_code"],
                args["room"],
                args["rate_code_rate"],
                args["base_rate"],
                discount_type,
                discount_value,
                args["ignore_availability"],
                args["allow_share"],
            )
        except Exception as e:
            exc_msg = str(e)
            import re
            original_match = re.search(r"Original:\s*(.*)", exc_msg, re.DOTALL)
            clean_msg = original_match.group(1).strip() if original_match else exc_msg

            # action_label = 'Allow Sharing'
            # action_body = {**args, "allow_share": 1}
            if 'No availability' in clean_msg:
                raise AvailabilityError(clean_msg)
            raise RoomShareError(clean_msg)
            #     action_label = 'Ignore Availability'
            #     action_body = {**args, "ignore_availability": 1}
            # primary_action = {
            #     "label": action_label,
            #     "server_action": "abc_hms.ignore_and_resave",
            #     "hide_on_success": True,
            #     "args": json.dumps(action_body , default=str),
            # }
            # frappe.throw(clean_msg,primary_action=primary_action)

    def reservation_end_of_day_auto_mark(self , property:str ,auto_mark_no_show: bool):
        return self.repo.reservation_end_of_day_auto_mark(
            property,
            auto_mark_no_show,
        )

    def reservation_departures_for_current_date(self , property: str):
        result = self.repo.reservation_departures_for_current_date(property)
        return result
    def reservation_arrivals_for_current_date(self , property: str):
        result = self.repo.reservation_arrivals_for_current_date(property)
        return result
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
        if params:
            return self.repo.reservation_availability_check(params)
        return frappe.throw("should select filters")

    def sync_reservations_to_pos_invoices(self, business_date: int , default_rooms_group: str, upsert_pos_invoice_method ):
        # Step 1: fetch reservations
        invoices = self.repo.get_inhouse_reservations_invoices(
            business_date
        )
        frappe.throw(f"{json.dumps(invoices)}")

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

            except Exception:
                raise

            responses.append(response)

        return responses
