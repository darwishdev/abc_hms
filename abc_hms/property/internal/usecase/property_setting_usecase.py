from utils.date_utils import date_to_int
from ..repo.property_setting_repo import PropertySettingRepo
from abc_hms.dto.property_setting_dto import (
    PropertySettingBusinessDateFindResponse,
    PropertySettingBusinessDateFindResult,
    PropertySettingData,
    PropertySettingFindResponse,
    PropertySettingUpsertRequest,
    PropertySettingUpsertResponse,
)
from frappe import _

class PropertySettingUsecase:
    def __init__(self):
        self.repo = PropertySettingRepo()

    def property_setting_upsert(
        self,
        request: PropertySettingUpsertRequest,
    ) -> PropertySettingUpsertResponse:
        """Upsert a property setting"""
        try:
            result = self.repo.property_setting_upsert(request["doc"], commit=request.get("commit", False))
            return {
                "success": True,
                "doc": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"PropertySetting Upsert Error: {str(e)}",
            }


    def property_setting_find(
        self,
        property_name: str,
    ) -> PropertySettingData:
        """Get business date for a property"""
        try:
            result = self.repo.property_setting_find(property_name)
            return result
        except:
            raise

    def property_setting_business_date_find(
        self,
        property_name: str,
    ) -> PropertySettingBusinessDateFindResult:
        """Get business date for a property"""
        try:
            result = self.repo.property_setting_business_date_find(property_name)
            return result
        except Exception as e:
            raise Exception(f"unexpected_error: {str(e)}")

    def property_setting_increase_business_date(
        self,
        property_name: str,
        commit: bool = False,
    ) -> PropertySettingBusinessDateFindResponse:
        """Increase business date for a property"""
        try:
            result = self.repo.property_setting_increase_business_date(property_name, commit=commit)
            return result
        except Exception as e:
            raise e
