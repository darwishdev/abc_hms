from abc_hms.dto.property_room_type_dto import RoomTypeEnsureItemRequest, RoomTypeEnsureItemResponse
from ..repo.room_type_repo import RoomTypeRepo
from erpnext.stock.doctype.item.item import Item

class RoomTypeUsecase:
    def __init__(self):
        self.repo = RoomTypeRepo()

    def room_type_ensure_item(
        self,
        req: RoomTypeEnsureItemRequest
    ) -> RoomTypeEnsureItemResponse:
        try:
            item: Item = self.repo.room_type_ensure_item(
                room_type_name=req["room_type_name"],
                rate_code=req["rate_code"],
                currency=req["currency"],
                commit=req["commit"]
            )
            return {
                "success": True,
                "doc": item,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"RoomType Ensure Item Error: {str(e)}",
            }
