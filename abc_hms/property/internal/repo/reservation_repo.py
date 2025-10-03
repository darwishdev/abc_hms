
from typing import List
import frappe
from frappe import Optional, _
from utils import date_utils
import frappe
from utils.sql_utils import run_sql

class ReservationRepo:
    def reservation_sync(
        self,
        reservation: str,
        new_arrival: str,
        new_departure: str,
        new_docstatus: int,
        new_reservation_status: str,
        new_room_type: str,
        new_rate_code: str,
        new_room: str,
        ignore_availability: int,
        allow_room_sharing: int,
    ):
        query = """
            CALL reservation_sync(%s, %s, %s, %s, %s, %s, %s, %s,%s, %s)
        """

        params = (
            reservation,
            new_arrival,
            new_departure,
            new_docstatus,
            new_reservation_status,
            new_room_type,
            new_rate_code,
            new_room,
            ignore_availability,
            allow_room_sharing,
        )

        # frappe.db.sql is the right API (not frappe.sql.call)
        result = frappe.db.sql(query, params, as_dict=True)

        return result

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


    def reservation_departures_for_current_date(self,property: str):
        query = """
            SELECT
                r.name AS reservation,
                r.guest,
                r.room_type,
                r.room,
                r.base_rate
            FROM `tabProperty Setting` s
            JOIN `tabReservation` r on r.departure = s.business_date
and r.reservation_status =
            'Departure'
            WHERE s.name = %(property)s;
        """
        results = frappe.db.sql(query, {"property": property} , as_dict=True)
        return results
    def reservation_arrivals_for_current_date(self,property: str):
        query = """
            SELECT
                r.name AS reservation,
                r.guest,
                r.room_type,
                r.room,
                r.base_rate
            FROM `tabProperty Setting` s
            JOIN `tabReservation` r on r.arrival = s.business_date and r.reservation_status =
            'Arrival'
            WHERE s.name = %(property)s;
        """
        results = frappe.db.sql(query, {"property": property} , as_dict=True)
        return results


    def get_inhouse_reservations_invoices(self , for_date: int):
        query = """
with reservations as (
  select
  r.name reservation,
  r.rate_code_rate,
  r.room_type,
  r.arrival,
  r.discount_percent,
  r.nights,
  r.discount_amount,
  r.guest customer,
  r.departure,
  r.rate_code,
  r.base_rate,
  r.property,
  p.company,
  CONCAT('F-',r.name , '-000001') folio,
  rc.currency,
  r.adults number_of_guests,
  %(for_date)s for_date,
  CONCAT('PI-F-' , r.name , '-%(for_date)s-.####') naming_series
FROM `tabReservation` r
JOIN `tabRate Code` rc on r.rate_code = rc.name
  JOIN `tabProperty` p  on r.property = p.name
WHERE r.reservation_status IN ('In House' , 'Departure')
), pkg_items as (
  select
  r.reservation,
  0 pkgs_rate,
  pkgp.item_name,
  pkgp.item_code,
  pkgp.item_description,
  pkgp.uom stock_uom,
  pkgp.currency,
  pkgp.price_list_rate rate,
  1 qty,
  pkgp.price_list_rate amount,
  %(for_date)s for_date,
  CONCAT(r.folio , '-W-001') folio_window
  FROM reservations r
  JOIN `tabRate PKG` rp on r.rate_code = rp.parent
  JOIN `tabProperty Setting` s on r.property = s.name
  JOIN  `tabItem Price`  pkgp ON pkgp.item_name = rp.pkg and pkgp.price_list = s.default_price_list and pkgp.valid_from <= r.arrival and pkgp.valid_upto >= r.departure
) , room_item as (
  select
  r.reservation ,
  r.rate_code_rate price_before_discount,
  ((r.discount_amount  / r.nights) + SUM(i.amount)) discount_amount,
  SUM(i.amount) pkgs_rate,
  CONCAT(r.room_type , '-' , r.rate_code) item_name,
  CONCAT(r.room_type , '-' , r.rate_code) item_code,
  CONCAT(r.room_type , '-' , r.rate_code) item_description,
  'Nos' stock_uom,
  r.currency,
  r.rate_code_rate rate,
  1 qty,
  r.base_rate amount,
  %(for_date)s for_date,
  CONCAT(r.folio , '-W-001') folio_window
  from reservations r
  JOIN pkg_items i on r.reservation = i.reservation
group by
  r.reservation ,
  r.rate_code_rate,
  r.discount_amount,
  r.nights,
  r.room_type ,
  r.rate_code  ,
  r.currency,
  r.rate_code_rate,
  r.base_rate
), items as (
  select
  reservation,
  0 discount_amount,
  0 discount_percentage,
  item_name,
  item_code,
  item_description,
  stock_uom,
  currency,
  rate,
  qty,
  amount,
  %(for_date)s for_date,
  folio_window
  FROM pkg_items
  union
select
  reservation,
  discount_amount,
  (discount_amount / price_before_discount ) * 100 discount_percentage,
  item_name,
  item_code,
  item_description,
  'Nos' stock_uom,
  currency,
  price_before_discount rate,
  1 qty,
  price_before_discount amount,
  %(for_date)s for_date,
  folio_window
  -- price_before_discount, discount_amount ,
  -- (price_before_discount - discount_amount) price_after_discount,
  -- ROUND((discount_amount / price_before_discount),4)  discount_ratio,
  -- ROUND((discount_amount / price_before_discount) * 100 , 2)  discount_percent
  from room_item
  )
 select
  SUM(i.amount) total_amount,
  r.rate_code_rate,
  r.base_rate,
  'Main' pos_profile,
  r.customer,
  r.rate_code,
  r.discount_percent,
  r.property,
  r.company,
  r.folio,
  r.currency,
  r.number_of_guests,
  r.for_date,
  r.naming_series,
  JSON_ARRAYAGG(JSON_OBJECT(
      'item_name', i.item_name,
      'for_date',  %(for_date)s,
      'item_code', i.item_code,
      'item_description', i.item_description,
      'stock_uom', i.stock_uom,
      'price_list_rate', i.rate,
      'discount_percentage', i.discount_percentage,
      'qty', 1,
      'amount', i.amount,
      'folio_window', i.folio_window)) items
  FROM reservations r
  JOIN items i on r.reservation = i.reservation
GROUP BY r.reservation,r.customer,
  r.rate_code,
  r.property,
  r.company,
  r.folio,
  r.discount_percent,
  r.rate_code_rate,
  r.currency,
  r.number_of_guests,
  r.for_date,
  r.naming_series

        """
        invoices = frappe.db.sql(query , {"for_date" : for_date} , as_dict=True)
        return invoices
    def get_inhouse_reservations(self,business_date: int):
        query = """
            SELECT
                r.name AS reservation,
                r.guest,
                f.name AS folio,
                inv.name AS invoice,
                CONCAT(r.room_type , '-' , r.rate_code) new_item_name,
                p.company,
                r.adults number_of_guests,
                %(business_date)s for_date,
                s.default_pos_profile,
                r.rate_code,
                r.room_type,
                r.room,
                r.base_rate,
                CONCAT(r.room_type , '-' , r.rate_code) item_name,
                CONCAT(r.room_type , '-' , r.rate_code) item_code,
                CONCAT(r.room_type , '-' , r.rate_code) item_description,
                "Nos" stock_uom,
                rc.currency,
                coalesce(ce.exchange_rate ,1) exchange_rate,
                min(fw.name) folio_window,
                CONCAT(f.name , '-W-001') new_folio_window,
                CONCAT('PI-' , f.name , '-' , %(business_date)s , '-' , '.####') new_pos_invoice_naming_series
            FROM `tabReservation` r
            JOIN `tabProperty` p  on r.property = p.name
            JOIN `tabProperty Setting` s on r.property = s.name
            JOIN `tabFolio` f
                ON r.name = f.reservation
            JOIN `tabRate Code` rc on r.rate_code = rc.name
            LEFT join `tabFolio Window` fw  on f.name = fw.folio
            LEFT join `tabCurrency Exchange` ce on ce.from_currency = rc.currency
            LEFT JOIN `tabPOS Invoice` inv
                ON f.name  = inv.folio
               AND inv.for_date = %(business_date)s
            LEFT JOIN tabItem i on i.name = CONCAT(r.room_type , '-' , r.rate_code)
            WHERE r.reservation_status IN ('In House' , 'Departure')
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
        if auto_mark_no_show:
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
            AND r.arrival =s.business_date
        """, (property,))
        frappe.db.sql("""
            UPDATE `tabReservation` r
            JOIN `tabProperty Setting` s on r.property = s.name
            SET r.reservation_status = 'Departure'
            WHERE reservation_status = 'In House'
            AND r.property = %s
            AND r.departure = s.business_date
        """, (property,))

        # frappe.db.sql("""
        #     insert into room_date (
        #         room,
        #         for_date,
        #         room_status
        #     )
        #     select r.room , date_to_int(s.business_date) , 0
        #     FROM `tabReservation` r
        #     JOIN `tabProperty Setting` s on r.property = %s
        #     where r.reservation_status  IN ('In House' , 'Departure')
        #     ON DUPLICATE KEY UPDATE
        #         room_status = 0;
        # """, (property,))
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
                ("CHNA", arrival, departure, None, None)
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
