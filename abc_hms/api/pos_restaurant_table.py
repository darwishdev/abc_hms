import frappe
from abc_hms.container import app_container
@frappe.whitelist(methods=["GET"])
def restaurant_table_list():
    args = frappe.form_dict
    if not args.get("restaurant"):
        raise  frappe.ValidationError("restaurant is required")
    result = app_container.restaurant_table_usecase.table_list(args.get("restaurant"))
    return result

