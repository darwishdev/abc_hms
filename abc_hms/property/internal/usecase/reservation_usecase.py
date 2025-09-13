
import frappe
from ..repo.reservation_repo import ReservationRepo

class ReservationUsecase:
    def __init__(self) -> None:
        self.repo = ReservationRepo()



    def reservation_availability_check(
            self,
            params : dict | None =None,
    ):
        if params:
            return self.repo.reservation_availability_check(params)
        return frappe.throw("should select filters")
