
import frappe
import pymysql.cursors
import pymysql.cursors
from frappe import _
from frappe.utils import nowdate
from frappe.utils import today
from frappe.utils import today, getdate, add_days
from frappe import render_template
from frappe.utils import now_datetime, format_datetime
import os
from utils import date_utils
from utils.date_utils import date_to_int
from typing import Optional
import frappe
from pymysql import InternalError

from utils.sql_utils import run_sql

class ReservationRepo:
    @frappe.whitelist()

    def reservation_date_sync(
            self,
            name: str
    ):
        try:
            def procedure_call(cur):
                # Step 1: Availability
                cur.execute(
                    """
                    CALL reservation_date_sync(%s)
                    """,
                    (name)
                )


                return cur.fetchall()
            return run_sql(procedure_call)
        except Exception as e:
            raise e
    def reservation_sync_days(
            self,
            doc: dict,
            ignore_availability = 0,
            allow_sharing = 0
    ):
        def query_logic(cur):
            cur.execute(
                """
                    CALL reservation_sync(
                        %s, %s, %s, %s, %s, %s, %s, %s , %s
                    )
                """,
                (
                    doc["name"],
                    doc["arrival"],
                    doc["departure"],
                    doc["docstatus"],
                    doc["reservation_status"],
                    doc["room_type"],
                    getattr(doc, "room", None),
                    ignore_availability,
                    allow_sharing
                )
            )

            # Step 2: Get results
            return cur.fetchall()

        return run_sql(query_logic)
    def reservation_availability_check(
            self,
            params: dict
    ):
        def query_logic(cur):
            # Step 1: Availability
            arrival = date_utils.date_to_int(params['arrival'])
            departure = date_utils.date_to_int(params['departure'])
            cur.execute(
                """
                CALL inventory_availability_check(%s, %s, %s, %s, %s)
                """,
                ("CONA", arrival, departure, None, None)
            )

            # Step 2: Get results
            availability = cur.fetchall()

            # Step 3: Early return if empty
            if not availability:
                return {"availability": [], "rates": []}

            # Step 4: Extract room types
            room_type_list = ",".join([row["room_type"] for row in availability])

            # Step 5: Rates
            cur.execute(
                """
                CALL room_type_rate_list(%s, %s, %s)
                """,
                (arrival, departure, room_type_list)
            )

            # Step 6: Return both
            return {"availability": availability, "rates": cur.fetchall()}
        return run_sql(query_logic)
