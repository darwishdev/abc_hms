import frappe
from erpnext.stock.doctype.item.item import Item
class RoomTypeRepo:
    def room_type_ensure_item(
        self,
        room_type_name: str,
        rate_code: str,
        currency: str,
        commit: bool = True
    ) -> Item:
        try:
            item_code = f"{room_type_name}-{rate_code}-{currency}"
            if frappe.db.exists("Item", item_code):
                item: Item = frappe.get_doc("Item", item_code)  # type: ignore
            else:
                default_room_group = frappe.db.get_value("Property Setting", None, "default_room_group")
                if not default_room_group:
                    frappe.throw("Default room Item Group not set in Property Setting")
                item: Item = frappe.new_doc("Item")  # type: ignore
                item.item_code = item_code
                item.item_name = item_code
                item.description = item_code
                item.item_group = str(default_room_group) or "Rooms"
                item.stock_uom = "Nos"
                item.is_stock_item = 0
                item.has_variants = 0
                item.save(ignore_permissions=True)

                if commit:
                    frappe.db.commit()

            return item

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "RoomType Ensure Item Error")
            raise
