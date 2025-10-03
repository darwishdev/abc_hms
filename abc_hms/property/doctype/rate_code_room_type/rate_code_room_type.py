# Copyright (c) 2025, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RateCodeRoomType(Document):
    def after_insert(self):
        self.ensure_item_exists()

    def on_update(self):
        frappe.throw(f"error")
        self.ensure_item_exists()

    def ensure_item_exists(self):
        if not self.room_type:
            return

        # parent is the Rate Code document (since this is a child table)
        rate_code = self.parent
        item_name = f"{self.room_type}-{rate_code}"

        exists = frappe.db.exists("Item", item_name)
        if not exists:
            item_doc = frappe.get_doc({
                "doctype": "Item",
                "item_code": item_name,
                "item_name": item_name,
                "item_group": "All Item Groups",  # or your specific default
                "is_sales_item": 1,
                "is_purchase_item": 0
            })
            item_doc.insert(ignore_permissions=True)
            frappe.db.commit()  # ensure immediate insert
