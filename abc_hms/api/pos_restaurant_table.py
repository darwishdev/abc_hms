import frappe
from abc_hms.container import app_container
@frappe.whitelist(methods=["GET"])
def restaurant_table_list(restaurant:str):
    result = app_container.restaurant_table_usecase.table_list(restaurant)
    return result

