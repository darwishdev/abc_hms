import json
from typing import List
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

from collections import defaultdict


@frappe.whitelist()
def reservation_date_list(reservation):
    return app_container.reservation_usecase.reservation_date_list(reservation)
@frappe.whitelist()
def reservation_date_bulk_upsert(reservation_dates):
    return app_container.reservation_usecase.reservation_date_bulk_upsert(reservation_dates)
@frappe.whitelist()
def reservation_sync(args: str | dict):
    if isinstance(args, str):
        args = json.loads(args)

    resp = app_container.reservation_usecase.reservation_sync(args)
    return resp


def build_rate_diary(data):
    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for row in data:
        grouped[row["room_category"]][row["room_type"]][row["rate_code"]].append(row)

    result = []
    for cat, types in grouped.items():
        # Category level
        result.append({
            "indent": 0,
            "group_1": cat,
        })

        for rtype, codes in types.items():
            # Type level
            result.append({
                "indent": 1,
                "group_1": rtype,
            })

            for code, rows in codes.items():
                row_data = {}
                for r in rows:
                    row_data[str(r["date"])] = f"{r['base_rate']} {r['currency']}"

                result.append({
                    "indent": 2,
                    "group_1": code,
                    **row_data
                })

    return result
@frappe.whitelist()
def room_type_rate_list(
            property: str,
            from_date: str,
            to_date: str,
            room_category: str | None = None,
            room_types: str | None = None,
):
    resp = app_container.reservation_usecase.room_type_rate_list(
        property,
        from_date,
        to_date,
        room_category,
        room_types
    )
    return build_rate_diary(resp)

@frappe.whitelist()
def reservation_availability_check(
    property: str,
    arrival : str | int,
    departure : str | int ,
    room_category: str | None =None,
    room_type : str | None =None,
    discount_type : str | None =None,
    discount_percent : str | None =None,
    discount_amount: str | None =None,
    rate_code : str | None =None,
):
    return app_container.reservation_usecase.reservation_availability_check({
        "property" : property ,
        "arrival" : arrival ,
        "departure" : departure ,
        "discount_type" : discount_type ,
        "discount_percent" : discount_percent ,
        "discount_amount" : discount_amount,
        "rate_code" : rate_code ,
        "room_type" : room_type,
        "room_category" : room_category,
    })


@frappe.whitelist()
def end_of_day(args: str |  dict):
    """Force save reservation by ignoring availability."""
    if isinstance(args, str):
        args = json.loads(args)
    return app_container.reservation_usecase.end_of_day(args)
@frappe.whitelist()
def ignore_and_resave(args: dict | str):
    if isinstance(args, str):
        args = json.loads(args)
    reservation_doc = frappe.get_doc('Reservation' , args['name'])
    if not reservation_doc:
        frappe.throw(f"Can't find reservation with name {args['name']}")
    reservation_doc.update(args)
    reservation_doc.save()
    frappe.db.commit()
