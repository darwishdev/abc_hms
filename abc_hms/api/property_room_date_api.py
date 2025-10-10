from datetime import datetime
from typing import Dict, List, Union

from collections import defaultdict
import frappe
import json

from sentry_sdk.utils import json_dumps
from abc_hms.container import app_container
from abc_hms.dto.property_room_date_dto import RoomDateBulkUpsertRequest, RoomDateBulkUpsertResponse
from utils.sql_utils import run_sql

@frappe.whitelist(methods=["POST", "PUT"])
def room_date_bulk_upsert(room_numbers , from_date,to_date,updated_fields):
    if isinstance(room_numbers, str):
        try:
            parsed_room_numbers: List[str] = json.loads(room_numbers)
        except json.JSONDecodeError:
            parsed_room_numbers = [room_numbers]
    else:
        parsed_room_numbers: List[str] = list(room_numbers)


    # updated_fields → Dict[str, number]
    if isinstance(updated_fields, str):
        try:
            parsed_updated_fields: Dict[str, Union[int, float]] = json.loads(updated_fields)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid updated_fields: {updated_fields}")
    else:
        parsed_updated_fields: Dict[str, Union[int, float]] = dict(updated_fields)

    return app_container.room_date_usecase.room_date_bulk_upsert(parsed_room_numbers,from_date,to_date,parsed_updated_fields ,True)

@frappe.whitelist()
def room_type_availability_list(p_from, p_to, p_property, p_room_category=None, p_room_type=None):
    try:
        def sql_call(cur,_):
            if not p_from or not p_to:
                frappe.throw("From date and To date are required")

            if not p_property:
                frappe.throw("Property is required")

            # Call the stored procedure
            rc = p_room_category if p_room_category and len(p_room_category) > 0 else None
            rt = p_room_type if p_room_type and len(p_room_type) > 0 else None
            cur.execute(
                """
                CALL room_type_availability_list(%s, %s, %s, %s)
                """,
                (p_from, p_to,  rc, rt),
            )
            return cur.fetchall()
        result = run_sql(sql_call)
        # Validate required parameters

        # Process the result
        # The stored procedure returns JSON strings in the 'data' field
        # We need to parse them for easier handling
        processed_result = []
        for row in result:
            processed_row = {
                'room_category': row.get('room_category'),
                'data': row.get('data')
            }

            # Try to parse the JSON data field if it's a string
            if isinstance(processed_row['data'], str):
                try:
                    processed_row['data'] = json.loads(processed_row['data'])
                except json.JSONDecodeError as e:
                    raise e

            processed_result.append(processed_row)

        return processed_result

    except Exception as e:
        frappe.log_error(
            title="Room Availability Error",
            message=f"Error calling room_type_availability_list: {str(e)}\nParams: {p_from}, {p_to}, {p_property}, {p_room_category}, {p_room_type}"
        )
        frappe.throw(f"Error retrieving room availability data: {str(e)}")


@frappe.whitelist()
def room_availability_list(p_from, p_to, p_property, p_room_category=None, p_room_type=None):
    try:
        def sql_call(cur,_):
            if not p_from or not p_to:
                frappe.throw("From date and To date are required")

            if not p_property:
                frappe.throw("Property is required")

            # Call the stored procedure
            rc = p_room_category if p_room_category and len(p_room_category) > 0 else None
            rt = p_room_type if p_room_type and len(p_room_type) > 0 else None
            cur.execute(
                """
                CALL room_availability_list(%s,%s, %s, %s, %s)
                """,
                (p_property , p_from, p_to,  rc, rt),
            )
            room_categories = cur.fetchall()
            if not cur.nextset():
                return
            room_types = cur.fetchall()

            if not cur.nextset():
                return
            rooms = cur.fetchall()

            return {"room_categories": room_categories, "room_types":room_types,"rooms":rooms}
        result = run_sql(sql_call)
        if not result:
            return
        rooms = result["rooms"]
        # Process the result
        # The stored procedure returns JSON strings in the 'data' field
        # We need to parse them for easier handling
        processed_result = []
        for row in rooms:
            details = row.get('details')
            new_details = json.loads(details)
            processed_result.append({**row,"details":new_details})


        return transform_diary_data({**result,"rooms":processed_result})

    except Exception as e:
        frappe.log_error(
            title="Room Availability Error",
            message=f"Error calling room_type_availability_list: {str(e)}\nParams: {p_from}, {p_to}, {p_property}, {p_room_category}, {p_room_type}"
        )
        frappe.throw(f"Error retrieving room availability data: {str(e)}")
def transform_diary_data(data):
    categories = data["room_categories"]
    room_types = data["room_types"]
    rooms = data["rooms"]
    # --- 1️⃣ Collect all dates dynamically ---
    all_dates = sorted(
        list({d["date"] for r in rooms for d in r["details"]}),
        key=lambda x: datetime.strptime(x, "%Y-%m-%d")
    )

    # --- 2️⃣ Start building the flattened result ---
    result = []

    for cat in categories:
        # Level 0: Category
        result.append({
            "indent": 0,
            "group_1": cat["room_category"],
            "group_2": f"{int(cat['total_room_types'])} Room Types",
            "date_level_group": f"{int(cat['total_rooms'])} Rooms"
        })

        # Related room types
        related_types = [
            rt for rt in room_types if rt["room_category"] == cat["room_category"]
        ]

        for rt in related_types:
            # Level 1: Room Type
            result.append({
                "indent": 1,
                "group_1": rt["room_type"],
                # "group_2": rt["room_type"],
                "date_level_group": f"{int(rt['total_rooms'])} Rooms"
            })

            # Related rooms
            related_rooms = [
                r for r in rooms
                if r["room_type"] == rt["room_type"] and r["room_category"] == cat["room_category"]
            ]

            for r in related_rooms:
                # Level 2: Room
                row = {
                    "indent": 2,
                    # "group_1": r["room_category"],
                    "group_1": r["room_type"],
                    "date_level_group": r["room"]
                }
                ROOM_STATUS_COLORS = {
                    "Clean": "#d4edda",          # light green (default)
                    "Dirty": "#f8d7da",          # light red
                    "Inspected": "#d1ecf1",      # light blue
                    "Vacant": "#e2e3e5",         # light gray
                    "OCC": "#fff3cd",            # light yellow
                }

                OUT_OF_ORDER_COLORS = {
                    "OOS": "#ffc107",   # yellow
                    "OOO": "#dc3545",   # red
                }

                for d in r["details"]:
                    date = d["date"]

                    room_status = d.get("room_status", "")
                    guest_service_status = d.get("guest_service_status", "")
                    out_of_order_status = d.get("out_of_order_status", "")
                    in_house = d.get("in_house", False)

                    # base background color
                    bg_color = ROOM_STATUS_COLORS.get(room_status, "#d4edda")

                    # optional UI elements
                    badge_html = ""
                    guest_service_html = ""
                    inhouse_dot_html = ""

                    # out-of-order badge (only if not "In Order")
                    if out_of_order_status in OUT_OF_ORDER_COLORS:
                        ooo_color = OUT_OF_ORDER_COLORS[out_of_order_status]
                        badge_html = f"""
                        <div style="
                            position:absolute;
                            top:4px;
                            left:4px;
                            background:{ooo_color};
                            color:#fff;
                            font-size:10px;
                            padding:2px 4px;
                            border-radius:4px;
                        ">{out_of_order_status}</div>
                        """

                    # guest service label (only if not "No Status")
                    if guest_service_status not in ("", "No Status"):
                        guest_service_html = f"""
                        <div style="font-size:10px;opacity:0.8;">{guest_service_status}</div>
                        """

                    # in-house green dot (only if True)
                    if in_house:
                        inhouse_dot_html = """
                        <div style="
                            position:absolute;
                            top:4px;
                            right:4px;
                            width:8px;
                            height:8px;
                            background:#28a745;
                            border-radius:50%;
                        "></div>
                        """

                    # main container
                    row[date] = f"""
                    <div style="
                        position:relative;
                        width:100%;
                        height:100%;
                        background:{bg_color};
                        display:flex;
                        flex-direction:column;
                        justify-content:center;
                        align-items:center;
                        text-align:center;
                        font-size:11px;
                        font-weight:500;
                        color:#333;
                    ">
                        {badge_html}
                        {inhouse_dot_html}
                        {room_status}
                        {guest_service_html}
                    </div>
                    """

                result.append(row)

    return result


