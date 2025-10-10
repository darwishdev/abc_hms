
import frappe
class RateCodeRepo:
    def room_type_rate_bulk_upsert(
            self,
            room_type,
            rate_code,
            rate,
            date_from,
            date_to,
            commit: bool
    ):
        try:
            result = frappe.db.sql("CALL room_type_rate_bulk_upsert(%s,%s,%s,%s,%s)" ,
                                   (room_type,rate_code,rate,date_from,date_to))
            if commit:
                frappe.db.commit()
            return result
        except Exception as e:
            raise e
