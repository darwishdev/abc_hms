from typing import Dict
from frappe import _
from ..repo.room_repo import RoomRepo
class RoomUsecase:
    def __init__(self) -> None:
        self.repo = RoomRepo()

    def room_list(self , filters):
        return self.repo.room_list(filters)

    def room_list_input(self, pay_master=None, txt=None, searchfield=None, start=0, page_len=10):
        return self.repo.room_list_input(pay_master, txt, searchfield, start, page_len)


