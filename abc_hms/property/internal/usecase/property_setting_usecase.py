from utils.date_utils import date_to_int
from ..repo.property_setting_repo import PropertySettingRepo
from abc_hms.dto.property_setting_dto import (
    PropertySettingBusinessDateFindResponse,
    PropertySettingBusinessDateFindResult,
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
    ) -> PropertySettingFindResponse:
        """Get business date for a property"""
        try:
            result = self.repo.property_setting_find(property_name)
            result["business_date_int"] = date_to_int(str(result.get("business_date"))) # type: ignore
            return {"success" : True , "doc" : result}
        except Exception as e:
            return {
                "success": False,
                "error": f"PropertySetting BusinessDateFind Error: {str(e)}",
            }

    def property_setting_business_date_find(
        self,
        property_name: str,
    ) -> PropertySettingBusinessDateFindResponse:
        """Get business date for a property"""
        try:
            result = self.repo.property_setting_business_date_find(property_name)
            return {
                "success": True,
                "business_date_str": result["business_date_str"],
                "business_date_int": result["business_date_int"],
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"PropertySetting BusinessDateFind Error: {str(e)}",
            }

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
            return {
                "success": False,
                "error": f"PropertySetting IncreaseBusiness Error: {str(e)}",
            }
