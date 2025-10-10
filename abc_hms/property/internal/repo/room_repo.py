import json
import frappe
from pymysql import InternalError

class RoomRepo:
    def room_list_input(self, pay_master=None, txt=None, searchfield=None, start=0, page_len=10):
        txt = f"%{txt or ''}%"
        return frappe.db.sql("""
            SELECT r.name
            FROM `tabRoom` r
            INNER JOIN `tabRoom Type` rt ON rt.name = r.room_type
            WHERE rt.pay_master = COALESCE(%s, rt.pay_master)
              AND (r.name  LIKE %s)
            ORDER BY r.name
            LIMIT %s, %s
        """, (pay_master, txt,  start, page_len))
    def room_list(self, filters: dict | None = None):
        try:
            # normalize filters (frappe may send JSON string)
            if isinstance(filters, str):
                filters = json.loads(filters)
            filters = filters or {}

            # build query with COALESCE
            base_query = """
                SELECT
                    r.name,
                    r.display_name,
                    r.hk_section,
                    r.room_type,
                    r.property
                FROM v_room r
                WHERE
                  r.property = COALESCE(%(property)s, r.property)
                  AND r.room_category = COALESCE(%(room_category)s, r.room_category)
                  AND r.room_type = COALESCE(%(room_type)s, r.room_type)
                  AND r.hk_section   = COALESCE(%(hk_section)s, r.hk_section)
            """

            values = {
                "room_type": filters.get("room_type") or None,
                "property": filters.get("property") or None,
                "room_category": filters.get("room_category") or None,
                "hk_section": filters.get("hk_section") or None,
            }

            return frappe.db.sql(base_query, values, as_dict=True)

        except Exception as e:
            frappe.log_error(f"Error fetching room list: {str(e)}")
            raise InternalError(f"UNEXPECTED ERROR: {str(e)}")
