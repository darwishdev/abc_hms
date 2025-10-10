
from typing import Dict, List
from ..repo.room_date_repo import RoomDateRepo
from abc_hms.dto.property_room_date_dto import RoomDateBulkUpsertRequest, RoomDateView, RoomDateBulkUpsertResponse
class RoomDateUsecase:
    def __init__(self) -> None:
        self.repo = RoomDateRepo()

    def room_date_bulk_upsert(
        self,
        room_numbers: List[str],
        from_date: str,
        to_date: str,
        updated_fields: Dict[str, int],
        commit: bool = True,
    ) :
        try:
            result = self.repo.bulk_upsert(room_numbers , from_date,to_date , updated_fields , commit)
            return result
        except Exception as e:
            raise Exception(f"Un Expected Error: {str(e)}")
