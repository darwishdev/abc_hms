# Copyright (c) 2025, Your Name and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.model.document import Document


class RateCode(Document):
    def after_insert(self):
        self.ensure_items()

    def on_update(self):
        self.ensure_items()



    def ensure_items(self):
        room_types = self.as_dict()["room_types"]
        if room_types:
            for room_type in room_types:
                self.ensure_item_exists(room_type)
        # self.ensure_item_exists()

    def ensure_item_exists(self , room_type_dict: dict):
        room_type = room_type_dict["room_type"]
        is_pay_master = frappe.db.get_value("Room Type" , room_type , 'pay_master')
        if is_pay_master:
            return
        rate_code = room_type_dict["parent"]
        item_name = f"{room_type}-{rate_code}"

        exists = frappe.db.exists("Item", item_name)
        if not exists:
            item_doc = frappe.get_doc({
                "doctype": "Item",
                "item_code": item_name,
                "stock_uom": "Nos",
                "item_name": item_name,
                "item_group": "All Item Groups",  # or your specific default
                "is_sales_item": 1,
                "is_purchase_item": 0
            })
            item_doc.insert(ignore_permissions=True)
            frappe.db.commit()
