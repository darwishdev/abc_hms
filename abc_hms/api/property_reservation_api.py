import json
import frappe
import pymysql.cursors
import pymysql.cursors
from frappe import _
from frappe.utils import nowdate
from frappe.utils import today
from frappe.utils import today, getdate, add_days

from pymysql import err as pymysql_err
from abc_hms.container import app_container
from frappe import render_template
from frappe.utils import now_datetime, format_datetime
import os
from utils.date_utils import date_to_int


@frappe.whitelist()
def reservation_sync(args: str | dict):
    if isinstance(args, str):
        args = json.loads(args)

    resp = app_container.reservation_usecase.reservation_sync(args)
    return resp

@frappe.whitelist()
def reservation_availability_check(
        property: str,
        arrival : str | int,
        departure : str | int ,
        room_categories : str | None =None,
        room_types : str | None =None,
        rate_code : str | None =None,
):
    return app_container.reservation_usecase.reservation_availability_check({
        "property" : property ,
        "arrival" : arrival ,
        "departure" : departure ,
        "room_types" : room_types,
    })


@frappe.whitelist()
def end_of_day(args: str |  dict):
    """Force save reservation by ignoring availability."""
    if isinstance(args, str):
        # In case Frappe sends it as JSON string
        import json
        args = json.loads(args)
    return app_container.reservation_usecase.end_of_day(args)
@frappe.whitelist()
def ignore_and_resave(args: str |  dict):
    """Force save reservation by ignoring availability."""
    if isinstance(args, str):
        # In case Frappe sends it as JSON string
        import json
        args = json.loads(args)

    updatable_fields = [
        "arrival",
        "departure",
        "docstatus",
        "reservation_status",
        "room_type",
        "room",
        "ignore_availability",
        "allow_share",
        "customer",
        "number_of_adults",
        "number_of_children",
        "number_of_infants",
        "number_of_rooms",
        "rate_code",
        "base_rate",
        "fixed_rate",
        "total_stay",
        "currency",
        "exchange_rate",
        "property",
        "travel_agent",
        "company_profile",
    ]

    update_values = {k: v for k, v in args.items() if k in updatable_fields}
    try:
        frappe.db.begin()
        app_container.reservation_usecase.reservation_sync({
            "reservation": args["name"],
            "new_arrival": args["arrival"],
            "new_departure": args["departure"],
            "new_docstatus": args["docstatus"],
            "new_reservation_status": args["reservation_status"],
            "new_room_type": args["room_type"],
            "new_room": args["room"],
            "ignore_availability": args["ignore_availability"],
            "allow_room_sharing": args["allow_share"]
        })

        frappe.db.set_value("Reservation", args['name'], update_values)
        frappe.publish_realtime(
            "reload_doc",
            {"doctype": "Reservation", "name": args["name"]},
            user=frappe.session.user,
        )
        frappe.db.commit()
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "ignore_and_resave failed")
        raise e
    return {"status": "success", "name": args["name"]}
