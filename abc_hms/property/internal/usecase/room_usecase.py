from typing import Dict
from frappe import _
from ..repo.room_repo import RoomRepo
class RoomUsecase:
    def __init__(self) -> None:
        self.repo = RoomRepo()

    def room_list(self , filters):
        return self.repo.room_list(filters)

