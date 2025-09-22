from typing import List

import frappe
from abc_hms.dto.property_reservation_date_dto import ReservationDate
from utils.sql_utils import run_sql

class ReservationDateRepo:
    def reservation_date_sync(
            self,
            name: str,
            commit: bool
    )-> List[ReservationDate]:
        try:
            result = frappe.db.sql("CALL reservation_date_sync(%s)" , (name))
            if commit:
                frappe.db.commit()
            return result
        except Exception as e:
            raise e
