
from ..repo.rate_code_repo import RateCodeRepo
from frappe import _

class RateCodeUsecase:
    def __init__(self):
        self.repo = RateCodeRepo()


    def room_type_rate_bulk_upsert_json(
            self,
            date_from,
            date_to,
            rate,
            items,
    ):
        return self.repo.room_type_rate_bulk_upsert_json(
            date_from,
            date_to,
            rate,
            items,
            )



    def rate_code_room_type_list(
            self,
            rate_code,
    ):
        return self.repo.rate_code_room_type_list(
                rate_code,
            )


