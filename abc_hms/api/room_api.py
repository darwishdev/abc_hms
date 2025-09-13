from typing import Dict
import frappe
from abc_hms.container import container

@frappe.whitelist()
def room_list(filters ):
    return container.room_usecase.room_list(filters)
