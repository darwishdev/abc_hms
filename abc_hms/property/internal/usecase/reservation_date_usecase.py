
from typing import List
from ..repo.reservation_date_repo import ReservationDateRepo
from abc_hms.dto.property_reservation_date_dto import ReservationDate, ReservationDateSyncRequest,  ReservationDateSyncResponse
class ReservationDateUsecase:
    def __init__(self) -> None:
        self.repo = ReservationDateRepo()

    def reservation_date_sync(
        self,
        payload: ReservationDateSyncRequest
    ) -> ReservationDateSyncResponse:
        try:
            result: List[ReservationDate] = self.repo.reservation_date_sync(payload.get("reservation_name") , payload.get("commit"))
            return {
                "success": True,
                "affected": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"ReservationDate Sync Error: {str(e)}",
            }
