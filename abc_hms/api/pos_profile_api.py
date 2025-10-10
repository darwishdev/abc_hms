
import frappe
from abc_hms.api.decorators import business_date_protected
from abc_hms.container import app_container
@frappe.whitelist(methods=["GET"])
def profile_item_list():
    args = frappe.form_dict
    if not args.get("pos_profile"):
        raise  frappe.ValidationError("pos_profile is required")
    result = app_container.pos_profile_usecase.profile_item_list(args.get("pos_profile"))
    return result

@frappe.whitelist(methods=["GET"])
@business_date_protected(allow_empty_date=True)
def porfile_mode_of_payment_list():
    result = app_container.pos_profile_usecase.profile_mode_of_payment_list(frappe.local.pos_profile)
    return result

