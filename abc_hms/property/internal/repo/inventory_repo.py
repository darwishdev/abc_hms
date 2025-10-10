from ast import Tuple
import frappe
from pymysql import InternalError

class InventoryRepo:
    def room_date_lookup_list(self , lookup_types: list[str] | None = None):
        try:
            query = "SELECT lookup_type, lookup_key, lookup_value FROM room_date_lookup WHERE lookup_type IN %s"
            return frappe.db.sql(query ,(lookup_types,), as_dict=True)
        except Exception as e:
            raise e

    def room_status_list(self, params: dict):
        data = frappe.db.sql(
                """
                WITH dates as (
                    SELECT for_date from dim_date WHERE for_date BETWEEN %s AND %s
                ) , rooms as (
                    SELECT
                        r.name,
                        r.hk_section,
                        r.room_type,
                        r.minimum_guests_number,
                        r.maximum_guests_number,
                        i.hk_status,
                        i.ooo_status,
                        i.room_status,
                        i.service_status,
                        MIN(d.for_date) effective_from,
                        MAX(d.for_date) effective_to
                    FROM v_room r
                    CROSS JOIN dates d
                    left join inventory i on r.name = i.room  and i.for_date = d.for_date
                    WHERE
                        r.property = COALESCE(%s , r.property)
                        AND r.room_category = COALESCE(%s , r.room_category)
                        AND r.room_type = COALESCE(%s , r.room_type)
                        AND r.name = COALESCE(%s , r.name)
                    GROUP BY
                        r.name,
                        r.hk_section,
                        r.room_type,
                        r.minimum_guests_number,
                        r.maximum_guests_number,
                        i.hk_status,
                        i.room_status,
                        i.service_status
                )
                    SELECT
                        r.name,
                        r.hk_section,
                        r.room_type,
                        r.minimum_guests_number,
                        r.maximum_guests_number,
                        r.hk_status,
                        r.ooo_status,
                        r.room_status,
                        r.service_status,
                        r.effective_from,
                        r.effective_to
                    FROM rooms r
                    ORDER BY r.name , r.effective_from;
                """,
                (
                    params["date_from"],
                    params["date_to"],
                    params["property"],
                    params["room_category"],
                    params["room_type"],
                    params["room"],
                ),
                as_dict= True
            )

        return data

    def inventory_upsert(self, params: tuple):
        try:
            frappe.db.sql(
                """
                CALL upsert_inventory_status(%s,%s, %s, %s, %s,  %s, %s, %s, %s)
                """,
                params
            )
            frappe.db.commit()
            return {"status": "success"}
        except Exception as e:
            frappe.log_error(f"Error updating inventory: {str(e)}")
            raise InternalError(f"UNEXPECTED ERROR: {str(e)}")
