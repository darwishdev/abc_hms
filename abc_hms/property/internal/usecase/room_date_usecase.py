
from typing import List
from ..repo.room_date_repo import RoomDateRepo
from abc_hms.dto.property_room_date_dto import RoomDateBulkUpsertRequest, RoomDateView, RoomDateBulkUpsertResponse
class RoomDateUsecase:
    def __init__(self) -> None:
        self.repo = RoomDateRepo()

    def room_date_bulk_upsert(
        self,
        payload: RoomDateBulkUpsertRequest
    ) -> RoomDateBulkUpsertResponse:
        try:
            result: List[RoomDateView] = self.repo.bulk_upsert(payload)
            return {
                "success": True,
                "affected": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"RoomDate BulkUpsert Error: {str(e)}",
            }
