# Copyright (c) 2025, DarwishDev and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
    if not filters:
        filters = {}

    columns = [
        {"fieldname": "room", "label": "Room", "fieldtype": "Link", "options": "Room"},
        {"fieldname": "room_status", "label": "Room Status", "fieldtype": "Data"},
        {"fieldname": "base_rate", "label": "Base Rate", "fieldtype": "Currency"},
        {"fieldname": "nights", "label": "Nights", "fieldtype": "Int"},
        {"fieldname": "total_stay", "label": "Total Stay", "fieldtype": "Currency"},
        {"fieldname": "adults", "label": "Adults", "fieldtype": "Int"},
        {"fieldname": "children", "label": "Children", "fieldtype": "Int"},
        {"fieldname": "infants", "label": "Infants", "fieldtype": "Int"},
        {"fieldname": "persons", "label": "Persons", "fieldtype": "Int"},
        {"fieldname": "guest", "label": "Guest", "fieldtype": "Link", "options": "Customer"},
        {"fieldname": "name", "label": "Reservation", "fieldtype": "Link", "options": "Reservation"},
        {"fieldname": "arrival", "label": "Arrival", "fieldtype": "Date"},
        {"fieldname": "departure", "label": "departure", "fieldtype": "Date"},
        {"fieldname": "folio", "label": "Folio", "fieldtype": "Link", "options": "Folio"},
        {"fieldname": "folio_status", "label": "Folio Status", "fieldtype": "Data"},
        {"fieldname": "room_type", "label": "Room Type", "fieldtype": "Link", "options": "Room Type"},
        {"fieldname": "guest_comment", "label": "Guest Comments", "fieldtype": "Data"},
        {"fieldname": "reservation_comment", "label": "Reservation Comments", "fieldtype": "Data"},
        {"fieldname": "out_of_order_status", "label": "OOO Status", "fieldtype": "Data"},
        {"fieldname": "company_profile", "label": "Company Profile", "fieldtype": "Link", "options": "Customer"},
        {"fieldname": "travel_agent", "label": "Travel Agent", "fieldtype": "Link", "options": "Sales Partner"},
        {"fieldname": "out_of_order_reason", "label": "OOO Reason", "fieldtype": "Data"},
        {"fieldname": "creation", "label": "Created At", "fieldtype": "Datetime"}
    ]

    # Build dynamic conditions properly
    date_condition = filters.get('date_filter')
    property_value = filters.get('property', 'CONA')
    is_arrival = filters.get('is_arrival', False)
    is_departure = filters.get('is_departure', False)
    reservation_status = filters.get('reservation_status')
    room_status = filters.get('room_status')
    reservation= filters.get('reservation')
    guest = filters.get('guest')
    # Construct date condition for the CTE
    if date_condition:
        date_join_condition = f"AND d.date_actual = '{date_condition}'"
    else:
        date_join_condition = "AND d.date_actual = s.business_date"

    # Construct arrival/departure conditions
    arrival_condition = f"AND r.arrival = d.date_actual" if is_arrival else ""
    departure_condition = f"AND r.departure = d.date_actual" if is_departure else ""

    # Construct reservation status condition
    if reservation_status:
        status_condition = f"AND r.reservation_status = '{reservation_status}'"
    else:
        status_condition = ""
    if room_status:
        room_status_condition = f"AND (rd.room_status, 'Dirty') = '{room_status}'"
    else:
        room_status_condition = ""

    if reservation:
        reservation_condition = f"AND r.name = '{reservation}'"
    else:
        reservation_condition = ""

    if guest:
        guest_condition = f"AND r.guest = '{guest}'"
    else:
        guest_condition = ""
    query = f"""
    WITH date_filter AS (
        SELECT d.for_date, d.date_actual
        FROM dim_date d
        JOIN `tabProperty Setting` s ON s.property = '{property_value}'
            {date_join_condition}
    )
    SELECT
        r.room,
        COALESCE(rd.room_status, 'Dirty') AS room_status,
        r.base_rate,
        r.nights,
        (r.base_rate * r.nights) total_stay,
        r.adults,
        COALESCE(r.children, 0) children,
        COALESCE(r.infants, 0) infants,
        r.adults + COALESCE(r.children, 0) + COALESCE(r.infants, 0) persons,
        r.guest,
        r.name,
        r.arrival,
        r.departure,
        r.room_type,
        f.name folio,
        f.folio_status,
        COALESCE(GROUP_CONCAT(DISTINCT cc.comment SEPARATOR '</br>'), 'No Guest Comments') AS guest_comment,
        COALESCE(GROUP_CONCAT(DISTINCT rc.comment SEPARATOR '</br>'), 'No Reservation Comments') AS reservation_comment,
        COALESCE(rd.out_of_order_status, 'N/A') AS out_of_order_status,
        COALESCE(r.company_profile, 'N/A') AS company_profile,
        COALESCE(r.travel_agent, 'N/A') AS travel_agent,
        COALESCE(rd.out_of_order_reason, 'N/A') AS out_of_order_reason,
        r.creation
    FROM
        date_filter d
    JOIN
        `tabReservation` r ON r.arrival <= d.date_actual
            AND r.departure > d.date_actual
            {arrival_condition}
            {reservation_condition}
            {guest_condition}
            {departure_condition}
    JOIN
        `tabFolio` f ON f.reservation = r.name
    LEFT JOIN
        `tabGuest Comment` cc ON r.guest = cc.guest AND cc.reservation IS NULL
    LEFT JOIN
        `tabGuest Comment` rc ON r.guest = rc.guest AND rc.reservation = r.name
    LEFT JOIN
        v_room_date rd ON r.room = rd.room AND rd.for_date = d.for_date
    WHERE
        1=1
        {status_condition}
        {room_status_condition}
    GROUP BY
        r.room,
        rd.room_status,
        r.base_rate,
        r.nights,
        r.adults,
        r.children,
        r.infants,
        r.guest,
        r.name,
        r.arrival,
        r.departure,
        r.room_type,
        rd.out_of_order_status,
        r.company_profile,
        r.travel_agent,
        f.name,
        f.folio_status,
        rd.out_of_order_reason,
        r.creation;
    """
    print("Final query is:", query)
    data = frappe.db.sql(query, as_dict=1)
    return columns, data
