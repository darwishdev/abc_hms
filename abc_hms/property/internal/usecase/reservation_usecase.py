
import frappe
from ..repo.reservation_repo import ReservationRepo

class ReservationUsecase:
    def __init__(self) -> None:
        self.repo = ReservationRepo()

    @frappe.whitelist()
    def reservation_sync_days(
            self,
            doc: dict,
            ignore_availability = 0,
            allow_sharing = 0
    ):
        return self.repo.reservation_sync_days(doc , ignore_availability ,allow_sharing)


    def reservation_availability_check(
            self,
            params : dict | None =None,
    ):
        print("params")
        print(params)
        if params:
            return self.repo.reservation_availability_check(params)
        return frappe.throw("should select filters")
