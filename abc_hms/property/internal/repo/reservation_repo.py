
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
from utils.date_utils import date_to_int
from typing import Optional
import frappe
from pymysql import InternalError

from utils.sql_utils import run_sql

class ReservationRepo:
    @frappe.whitelist()
    def reservation_availability_check(
            self,
            params: dict
    ):
        def query_logic(cur):
            # Step 1: Availability
            cur.execute(
                """
                CALL inventory_availability_check(%s, %s, %s, %s, %s)
                """,
                ("CONA", 20250807, 20250809, None, None)
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
                (20250807, 20250809, room_type_list)
            )

            # Step 6: Return both
            return {"availability": availability, "rates": cur.fetchall()}
        return run_sql(query_logic)
        return run_sql(lambda cur: (
            # Step 1: Availability
            cur.execute(
                """
                CALL inventory_availability_check(%s, %s, %s, %s, %s)
                """,
                (
                    "CONA",
                    20250807,
                    20250809,
                    None,
                    None
                )
            ),

            # Get availability results
            availability := cur.fetchall(),

            # Early return if nothing available
            {"availability": [], "rates": []} if not availability else (
                # Step 2: Extract room types
                room_type_list := ",".join([row["room_type"] for row in availability]),

                # Step 3: Rates
                cur.execute(
                    """
                    CALL room_type_rate_list(%s, %s, %s)
                    """,
                    (20250807, 20250809, room_type_list)
                ),

                # Return both results
                {"availability": availability, "rates": cur.fetchall()}
            )[-1]  # Get the final result
        ))
