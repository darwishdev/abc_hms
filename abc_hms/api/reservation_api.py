import json
import frappe
import pymysql.cursors
import pymysql.cursors
from frappe import _
from frappe.utils import nowdate
from frappe.utils import today
from frappe.utils import today, getdate, add_days

from abc_hms.container import app_container
from frappe import render_template
from frappe.utils import now_datetime, format_datetime
import os
from utils.date_utils import date_to_int


@frappe.whitelist()
def reservation_sync_days(
        doc: str | dict,
        ignore_availability = 0,
        allow_sharing = 0
):
    if isinstance(doc, str):
        # parse the JSON string into dict
        doc = json.loads(doc)
    return app_container.reservation_usecase.reservation_sync_days(doc , ignore_availability ,allow_sharing)

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
