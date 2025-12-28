import frappe
import json
from abc_hms.container import app_container
from abc_hms.dto.property_setting_dto import (
    PropertySettingBusinessDateFindResponse,
    PropertySettingFindResponse,
    PropertySettingUpsertRequest,
    PropertySettingUpsertResponse,
)

@frappe.whitelist(methods=["POST", "PUT"])
def property_setting_upsert() -> PropertySettingUpsertResponse:
    try:
        data = frappe.local.request.data
        payload: PropertySettingUpsertRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success": False, "error": f"{str(e)}"}

    result = app_container.property_setting_usecase.property_setting_upsert(payload)
    return result

@frappe.whitelist(methods=["GET"])
def default_property_setting_find() -> PropertySettingFindResponse:
    try:
        default = frappe.db.sql("""SELECT default_property from tabUser where name = %s""" ,
                                frappe.session.user , pluck=True)
        if not default or len(default) == 0 :
            return {"success": False, "error" : "user don't have default property"}
        result = app_container.property_setting_usecase.property_setting_find(default[0])
        return result
    except Exception as e:
        return {"success": False, "error": f"{str(e)}"}
@frappe.whitelist(methods=["GET"])
def property_setting_find(property_name: str) -> PropertySettingFindResponse:
    try:
        result = app_container.property_setting_usecase.property_setting_find(property_name)
        return result
    except Exception as e:
        return {"success": False, "error": f"{str(e)}"}
@frappe.whitelist(methods=["GET", "POST"])
def property_setting_business_date_find(property_name: str) -> PropertySettingBusinessDateFindResponse:
    try:
        result = app_container.property_setting_usecase.property_setting_business_date_find(property_name)
        return result
    except Exception as e:
        return {"success": False, "error": f"{str(e)}"}

@frappe.whitelist(methods=["PUT"])
def property_setting_increase_business_date(property_name: str, commit: bool = False) ->PropertySettingBusinessDateFindResponse:
    try:
        result = app_container.property_setting_usecase.property_setting_increase_business_date(
            property_name, commit=commit
        )
        return result
    except Exception as e:
        return {"success": False, "error": f"{str(e)}"}
