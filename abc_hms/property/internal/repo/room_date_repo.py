from typing import List
import frappe
from abc_hms.dto.property_room_date_dto import RoomDateLookup, RoomDateView, RoomDateBulkUpsertRequest

from typing import TypedDict, List, Optional

class RoomDateViewFilters(TypedDict):
    room_numbers: Optional[List[str]]
    for_date: Optional[int]
    house_keeping_status: Optional[int]
    room_status: Optional[int]
    out_of_order_status: Optional[int]
    guest_service_status: Optional[int]
class RoomDateRepo:

    def room_date_lookup_list(self , lookup_types: list[str] | None = None)  -> List[RoomDateLookup]:
        try:
            query = "SELECT lookup_type, lookup_key, lookup_value FROM room_date_lookup WHERE lookup_type IN %s"
            result : List[RoomDateLookup] = frappe.db.sql(query ,(lookup_types,), as_dict=True) # type: ignore
            return result
        except Exception as e:
            raise e


    def bulk_upsert(self, payload: RoomDateBulkUpsertRequest) -> List[RoomDateView]:
        """
        Call the SP to upsert room_date for given rooms and date,
        then return the updated rows from the view.
        """
        try:
            # Prepare params
            rooms_json = frappe.as_json(payload["room_numbers"])  # JSON array for SP
            for_date = payload["for_date"]
            fields = payload["updated_fileds"]
            commit = payload.get("commit", False)

            # Call the stored procedure
            frappe.db.sql(
                """
                CALL sp_upsert_room_date(
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    rooms_json,
                    for_date,
                    fields.get("house_keeping_status"),
                    fields.get("room_status"),
                    fields.get("guest_service_status"),
                    fields.get("out_of_order_status"),
                    fields.get("out_of_order_reason"),
                    fields.get("persons"),
                ),
            )

            if commit:
                frappe.db.commit()
            filters: RoomDateViewFilters = {}
            updated_rows: List[RoomDateView] = self.room_date_view_list(filters)
            # Return updated rows from the view
            updated_rows: List[RoomDateView] = frappe.db.sql(
                """
                SELECT * FROM v_room_date
                WHERE for_date = %s
                  AND room IN (%s)
                """ % (for_date, ",".join(f"'{r}'" for r in payload["room_numbers"])),
                as_dict=True
            ) # type: ignore

            return updated_rows

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "RoomDateRepo BulkUpsert Error")
            raise

    def room_date_view_list(
        self,
        payload: RoomDateViewFilters,
    ) -> List[RoomDateView]:
        """
        Return rows from v_room_date for the given rooms and date,
        filtering each status using COALESCE to allow optional overrides.
        """
        try:
            if not payload["room_numbers"]:
                return []

            rooms_json = frappe.as_json(payload["room_numbers"])  # JSON array for SP
            for_date = payload["for_date"]

            query = f"""
                SELECT
                    room,
                    for_date,
                    COALESCE(persons, 0) AS persons,
                    COALESCE(out_of_order_reason, 'N/A') AS out_of_order_reason,
                    COALESCE(house_keeping_status, 0) AS house_keeping_status,
                    COALESCE(room_status, 0) AS room_status,
                    COALESCE(out_of_order_status, 0) AS out_of_order_status,
                    COALESCE(guest_service_status, 0) AS guest_service_status
                FROM v_room_date
                WHERE for_date = coalesce(%s,for_date)
                  AND (
                      %s IS NULL OR JSON_CONTAINS(%s, JSON_QUOTE(room))
                  )
                  AND house_keeping_status = COALESCE(%s, house_keeping_status)
                  AND room_status = COALESCE(%s, room_status)
                  AND out_of_order_status = COALESCE(%s, out_of_order_status)
                  AND guest_service_status = COALESCE(%s, guest_service_status)
            """ % (
                for_date,
                rooms_json,
                rooms_json,
                payload.get("house_keeping_status"),
                payload.get("room_status"),
                payload.get("out_of_order_status"),
                payload.get("guest_service_status"),
            )

            result: List[RoomDateView] = frappe.db.sql(query, as_dict=True)  # type: ignore
            return result

        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "RoomDateRepo ViewList Error")
            raise
