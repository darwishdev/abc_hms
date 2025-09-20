from typing import Dict
import frappe
from abc_hms.container import app_container

@frappe.whitelist()
def room_list(filters ):
    return app_container.room_usecase.room_list(filters)
