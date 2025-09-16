
# abc_hms/container.py
from abc_hms.property.internal.usecase.reservation_usecase import ReservationUsecase
from abc_hms.property.internal.usecase.room_usecase import RoomUsecase
from abc_hms.property.internal.usecase.inventory_usecase import InventoryUsecase
from .pos.usecase.auth_usecase import AuthUsecase
from .pos.repo.auth_repo import AuthRepo

class AppContainer:
    def __init__(self):
        self.auth_usecase = AuthUsecase()
        self.room_usecase = RoomUsecase()
        self.inventory_usecase = InventoryUsecase()
        self.reservation_usecase = ReservationUsecase()



# global singleton container for APIs
app_container = AppContainer()
