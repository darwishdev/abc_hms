import json
import re
from datetime import datetime
import frappe

from abc_hms.dto.pos_invoice_dto import PosInvoiceUpsertRequest, PosInvoiceUpsertResponse
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

    def reservation_sync(self , params:dict):
        return self.repo.reservation_sync(
            params.get("reservation"),
            params.get("new_arrival"),
            params.get("new_departure"),
            params.get("new_docstatus"),
            params.get("new_reservation_status"),
            params.get("new_room_type"),
            params.get("new_room"),
            params.get("ignore_availability", 0),
            params.get("allow_room_sharing", 0),
        )

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
