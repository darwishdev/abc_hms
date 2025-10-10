
from ..repo.rate_code_repo import RateCodeRepo
from frappe import _

class RateCodeUsecase:
    def __init__(self):
        self.repo = RateCodeRepo()

    def room_type_rate_bulk_upsert(
            self,
            room_type,
            rate_code,
            rate,
            date_from,
            date_to,
            commit: bool
    ):
        return self.repo.room_type_rate_bulk_upsert(
                room_type,
                rate_code,
                rate,
                date_from,
                date_to,
                commit
            )


