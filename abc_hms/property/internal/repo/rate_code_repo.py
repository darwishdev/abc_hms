
import json
import frappe
class RateCodeRepo:
    def room_type_rate_bulk_upsert(
            self,
            room_type,
            rate_code,
            rate,
            date_from,
            date_to,
    ):
        result = frappe.db.sql("CALL room_type_rate_bulk_upsert(%s,%s,%s,%s,%s)" ,
                               (room_type,rate_code,rate,date_from,date_to))
        return result

    def room_type_rate_bulk_upsert_json(
            self,
            date_from,
            date_to,
            rate_code,
            items
    ):
        if not isinstance(items, str):
            items = json.dumps(items)

        result = frappe.db.sql(
            "CALL room_type_rate_bulk_upsert_json(%s, %s, %s, %s)",
            (date_from, date_to, rate_code, items)
        )

        return result
    def rate_code_room_type_list(
            self,
            rate_code
    ):
        try:
            result = frappe.db.sql("SELECT room_type , base_price FROM `tabRate Code Room Type` WHERE parent = %s " ,
                                   (rate_code,) , as_dict=True)

            return result
        except Exception as e:
            raise e
