
# abc_hms/container.py
from abc_hms.pos.usecase.folio_usecase import FolioUsecase
from abc_hms.pos.usecase.pos_closing_entry_usecase import POSClosingEntryUsecase
from abc_hms.pos.usecase.pos_invoice_usecase import POSInvoiceUsecase
from abc_hms.pos.usecase.pos_opening_entry_usecase import POSOpeningEntryUsecase
from abc_hms.pos.usecase.pos_session_usecase import POSSessionUsecase
from abc_hms.pos.usecase.restaurant_table_usecase import RestaurantTableUsecase
from abc_hms.property.internal.usecase.property_setting_usecase import PropertySettingUsecase
from abc_hms.property.internal.usecase.reservation_date_usecase import ReservationDateUsecase
from abc_hms.property.internal.usecase.reservation_usecase import ReservationUsecase
from abc_hms.property.internal.usecase.room_date_usecase import RoomDateUsecase
from abc_hms.property.internal.usecase.room_type_usecase import RoomTypeUsecase
from abc_hms.property.internal.usecase.room_usecase import RoomUsecase
from abc_hms.property.internal.usecase.inventory_usecase import InventoryUsecase
from .pos.usecase.auth_usecase import AuthUsecase

class AppContainer:
    def __init__(self):
        self.auth_usecase = AuthUsecase()
        self.pos_invoice_usecase = POSInvoiceUsecase()
        self.pos_opening_entry_usecase = POSOpeningEntryUsecase()
        self.pos_closing_entry_usecase = POSClosingEntryUsecase()
        self.property_setting_usecase = PropertySettingUsecase()
        self.pos_session_usecase = POSSessionUsecase()
        self.room_usecase = RoomUsecase()
        self.room_date_usecase = RoomDateUsecase()
        self.folio_usecase = FolioUsecase()
        self.restaurant_table_usecase = RestaurantTableUsecase()
        self.reservation_date_usecase = ReservationDateUsecase()
        self.room_type_usecase = RoomTypeUsecase()
        self.inventory_usecase = InventoryUsecase()
        self.reservation_usecase = ReservationUsecase()



# global singleton container for APIs
app_container = AppContainer()
