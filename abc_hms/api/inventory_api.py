import json
from typing import List
import ast
import frappe
from pydantic import InstanceOf
from abc_hms.container import app_container

@frappe.whitelist(methods=["GET"])
def inventory_lookup_list(lookup_types: list[str] | str | None = None):
    if not lookup_types:
        return app_container.inventory_usecase.inventory_lookup_list()
    if isinstance(lookup_types, str):
        try:
            parsed_types = [t.strip() for t in lookup_types.split(",") if t.strip()]
            return app_container.inventory_usecase.inventory_lookup_list(parsed_types)
        except Exception:
            frappe.throw("Invalid lookup_type format. Expected JSON array string, e.g. [\"room status\", \"hk status\"].")

    frappe.throw("lookup_types must be string or list or none")




@frappe.whitelist(methods=["POST" , "PUT"])
def inventory_upsert(
    payload
):
    if isinstance(payload, str):
        try:
            payload = ast.literal_eval(payload)
        except (ValueError, SyntaxError) as e:
            # Handle the error if the string isn't a valid dictionary representation
            print(f"Error parsing updated_statues string: {e}")
            return # Or raise an exception, depending on your error handling policy
    payload['user'] = frappe.session.user
    return app_container.inventory_usecase.inventory_upsert(payload)


@frappe.whitelist(methods=["GET"])
def room_status_list(
        date_range,
        property: str | None = None,
        room_category: str | None = None,
        room_type: str | None = None,
        room: str | None = None,
        hk_section: str | None = None,
        hk_status: str | None = None,
        guest_service_status: str | None = None):
    # Convert JSON string to Python list if needed
    if isinstance(date_range, str):
        try:
            date_range = json.loads(date_range)
        except Exception:
            frappe.throw("Invalid date_range format. Expected JSON array of strings.")
    payload = {
        "property": property,
        "room_category": room_category,
        "room_type": room_type,
        "room": room,
        "hk_section": hk_section,
        "hk_status": hk_status,
        "room_status": 0,
        "guest_service_status": guest_service_status,
        "date_range": date_range,
    }
    return app_container.inventory_usecase.room_status_list(payload)
