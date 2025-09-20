
from typing import List
import frappe
from frappe import Optional, _
from utils import date_utils
import frappe
from utils.sql_utils import run_sql

class ReservationRepo:

    # def reservation_ensure_folio(
    #      self,
    #     reservation_name: str,
    #     commit: bool = True
    #
    # ):

    def mark_new_departures(self,tomorrow_date_int: int):
        mark_departures_query = """
            update `tabReservation` r set reservation_status = 'Departure' where date_to_int(r.departure) = %s
        """
        def procedure_call(cur ,conn):
            cur.execute(mark_departures_query,(tomorrow_date_int ))
            conn.commit()
            return cur.fetchall()
        return run_sql(procedure_call)

    def mark_tomorrow_reservations(self,tomorrow_date_int: int):
        print("arrivals querssss" , tomorrow_date_int)
        room_date_query = """
            insert into room_date(room,for_date , room_status)
              select
                  r.room,
                  %s,
                  0
            from `tabReservation` r
            where date_to_int(arrival) = %s
              on duplicate key update
                  room_status = 0;
        """
        mark_arrival_query = """
            update `tabReservation` r set reservation_status = 'Arrival' where date_to_int(r.arrival) = %s
        """
        mark_departures_query = """
            update `tabReservation` r set reservation_status = 'Departure' where date_to_int(r.departure) = %s
        """

        print("arrivals quersss" , mark_arrival_query , tomorrow_date_int)
        def procedure_call(cur , conn):
            # step 1: availability
            cur.execute(room_date_query,(tomorrow_date_int , tomorrow_date_int ))

            cur.fetchall()
            cur.execute(mark_arrival_query,(tomorrow_date_int))
            cur.execute(mark_departures_query,(tomorrow_date_int))
            conn.commit()
            return cur.fetchall()
        return run_sql(procedure_call)


    def reservation_departures_for_current_date(self,property: str)->Optional[List[str]]:
        query = """
            SELECT
                r.name AS reservation
            FROM `tabProperty Setting` s
            JOIN `tabReservation` r on r.departure = s.business_date
            WHERE s.name = %(property)s;
        """
        results : Optional[List[str]] = frappe.db.sql(query, {"property": property}) # type: ignore
        return results
    def reservation_arrivals_for_current_date(self,property: str)->Optional[List[str]]:
        query = """
            SELECT
                r.name AS reservation
            FROM `tabProperty Setting` s
            JOIN `tabReservation` r on r.arrival = s.business_date
            WHERE s.name = %(property)s;
        """
        results : Optional[List[str]] = frappe.db.sql(query, {"property": property}) # type: ignore
        return results


    def get_inhouse_reservations(self,business_date: int):
        query = """
            SELECT
                r.name AS reservation,
                r.guest,
                f.name AS folio,
                inv.name AS invoice,
                CONCAT(r.room_type , '-' , r.rate_code) new_item_name,
                r.rate_code,
                r.room_type,
                r.room,
                r.base_rate,
                i.name item_name,
                i.item_code,
                i.description item_description,
                i.stock_uom,
                rc.currency,
                coalesce(ce.exchange_rate ,1) exchange_rate,
                min(fw.name) folio_window,
                CONCAT(f.name , '-W-001') new_folio_window
            FROM `tabReservation` r
            JOIN `tabFolio` f
                ON r.name = f.reservation
            JOIN `tabRate Code` rc on r.rate_code = rc.name
            LEFT join `tabFolio Window` fw  on f.name = fw.folio
            LEFT join `tabCurrency Exchange` ce on ce.from_currency = rc.currency
            LEFT JOIN `tabPOS Invoice` inv
                ON f.name  = inv.folio
               AND inv.for_date = %(business_date)s
            LEFT JOIN tabItem i on i.name = CONCAT(r.room_type , '-' , r.rate_code)
            WHERE r.reservation_status = 'In House'
            GROUP BY
                r.name,
                r.guest,
                f.name ,
                inv.name,
                r.rate_code,
                r.room_type,
                r.room,
                r.base_rate,
                i.name,
                i.item_code,
                i.description,
                i.stock_uom,
                rc.currency,
                ce.exchange_rate;

        """
        results = frappe.db.sql(query, {"business_date": business_date}, as_dict=True)
        return results

    def reservation_end_of_day_auto_mark(self, property: str, auto_mark_no_show: bool):
        if not auto_mark_no_show:
            return {}
        frappe.db.sql("""
            UPDATE `tabReservation` r
            SET r.reservation_status = 'No Show', r.docstatus = 2
            WHERE reservation_status = 'Arrival' AND property = %s
        """, (property,))
        frappe.db.sql("""
            DELETE rd
            FROM `reservation_date` rd
            JOIN `tabReservation` r on rd.reservation = r.name AND r.reservation_status = 'Arrival' AND r.property = %s
        """, (property,))
        frappe.db.sql("""
            UPDATE `tabReservation` r
            JOIN `tabProperty Setting` s on r.property = s.name
            SET r.reservation_status = 'Arrival'
            WHERE reservation_status = 'Confirmed'
            AND r.property = %s
            AND r.arrival =
            DATE_ADD(s.business_date, INTERVAL 1 DAY)
        """, (property,))
        frappe.db.sql("""
            UPDATE `tabReservation` r
            JOIN `tabProperty Setting` s on r.property = s.name
            SET r.reservation_status = 'Departure'
            WHERE reservation_status = 'In House'
            AND r.property = %s
            AND r.departure =
            DATE_ADD(s.business_date, INTERVAL 1 DAY)
        """, (property,))
        return {}
    def reservation_availability_check(
            self,
            params: dict
    ):
        def query_logic(cur , _):
            arrival = date_utils.date_to_int(params['arrival'])
            departure = date_utils.date_to_int(params['departure'])
            cur.execute(
                """
                CALL inventory_availability_check(%s, %s, %s, %s, %s)
                """,
                ("CONA", arrival, departure, None, None)
            )
            availability = cur.fetchall()
            if not availability:
                return {"availability": [], "rates": []}

            room_type_list = ",".join([row["room_type"] for row in availability])

            cur.execute(
                """
                CALL room_type_rate_list(%s, %s, %s)
                """,
                (arrival, departure, room_type_list)
            )

            return {"availability": availability, "rates": cur.fetchall()}
        return run_sql(query_logic)
