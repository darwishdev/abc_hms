import frappe
from abc_hms.dto.pos_profile_dto import POSProfileItemListRequest
from frappe import  _
from ..repo.pos_profile_repo import POSProfileRepo

class POSProfileUsecase:
    def __init__(self):
        self.repo = POSProfileRepo()

    def profile_mode_of_payment_list(
        self,
        pos_profile: str
    ):
        try:
            return self.repo.profile_mode_of_payment_list(pos_profile)
        except frappe.ValidationError as e:
            raise frappe.ValidationError(f"validation failed: {e}")
    def profile_item_list(
        self,
        pos_profile :str
    ):
        try:
            return self.repo.profile_item_list(pos_profile)
        except frappe.ValidationError as e:
            raise frappe.ValidationError(f"validation failed: {e}")

        except Exception as e:
            raise Exception(f"Unexpected error: {str(e)}")
