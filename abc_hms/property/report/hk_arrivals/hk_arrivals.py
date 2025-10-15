import frappe
def execute(filters=None):
    if not filters:
        filters = {}

    columns = [
        {"fieldname": "business_date", "label": "Business Date", "fieldtype": "Date"},
        {"fieldname": "room",  "label": "Room", "fieldtype": "Link", "options": "Room"},
        {"fieldname": "room_status","editable" : True , "label": "Room Status", "fieldtype": "Data"},
        {"fieldname": "house_keeping_status","editable" : True , "label": "HK Status", "fieldtype": "Data"},

        {"fieldname": "discrepency","editable" : True , "label": "Discrepency", "fieldtype": "Int"},
        {"fieldname": "guest_service_status","editable" : True , "label": "Guest Service Status",
         "fieldtype": "Data"},

        {"fieldname": "vip_level",  "label": "VIP Level", "fieldtype": "Int"},
        {"fieldname": "nights", "label": "Nights", "fieldtype": "Int"},
        {"fieldname": "adults", "label": "Adults", "fieldtype": "Int"},
        {"fieldname": "children", "label": "Children", "fieldtype": "Int"},
        {"fieldname": "infants", "label": "Infants", "fieldtype": "Int"},
        {"fieldname": "guest", "label": "Guest", "fieldtype": "Link", "options": "Customer"},
        {"fieldname": "name", "label": "Reservation", "fieldtype": "Link", "options": "Reservation"},
        {"fieldname": "departure", "label": "departure", "fieldtype": "Date"},
        {"fieldname": "room_type", "label": "Room Type", "fieldtype": "Link", "options": "Room Type"},
        {"fieldname": "guest_comment", "label": "Guest Comments", "fieldtype": "Data"},
        {"fieldname": "reservation_comment", "label": "Reservation Comments", "fieldtype": "Data"},
        {"fieldname": "company_profile", "label": "Company Profile", "fieldtype": "Link", "options": "Customer"},
        {"fieldname": "travel_agent", "label": "Travel Agent", "fieldtype": "Link", "options":"Sales Partner"},
        {"fieldname": "reservation_status", "label": "Reservation Status", "fieldtype": "Data"}
    ]

    # Build dynamic conditions properly
    property_value = filters.get('property')
    room_status = filters.get('room_status')
    reservation= filters.get('reservation')
    guest = filters.get('guest')
    reservation_status = filters.get('reservation_status')
    room_status_condition = f"AND (rd.room_status, 'Dirty') = '{room_status}'" if room_status else ""
    reservation_condition = f"AND r.name = '{reservation}'" if reservation else ""
    guest_condition = f"AND r.guest = '{guest}'" if guest else ""
    reservation_status_condition = f"AND r.reservation_status = '{reservation_status}'" if reservation_status else ""
    room_assigned_condition = "AND r.room IS NOT NULL"

    query = f"""
    WITH property_settings AS (
        SELECT s.business_date , date_to_int(s.business_date) for_date
        from `tabProperty Setting` s where s.name = '{property_value}'
    )
    SELECT
        s.business_date,
        r.room,
        COALESCE(rd.house_keeping_status, 'N\A') AS house_keeping_status,
        COALESCE(rd.persons, 'N\A') AS discrepency,
        COALESCE(rd.guest_service_status, 'N\A') AS guest_service_status,
        COALESCE(rd.room_status, 'Dirty') AS room_status,
        r.base_rate,
        r.nights,
        r.adults,
        COALESCE(r.children, 0) children,
        COALESCE(r.infants, 0) infants,
        r.guest,
        r.name,
        r.room_type,
        c.vip_level,
        r.departure,
        COALESCE(GROUP_CONCAT(DISTINCT cc.comment SEPARATOR '</br>'), 'No Guest Comments') AS guest_comment,
        COALESCE(GROUP_CONCAT(DISTINCT rc.comment SEPARATOR '</br>'), 'No Reservation Comments') AS reservation_comment,
        COALESCE(r.company_profile, 'N/A') AS company_profile,
        COALESCE(r.travel_agent, 'N/A') AS travel_agent,
        COALESCE(rd.out_of_order_status, 'N/A') AS out_of_order_status,
        COALESCE(rd.out_of_order_reason, 'N/A') AS out_of_order_reason,
        r.reservation_status
    FROM
        property_settings s
    JOIN
        `tabReservation` r ON r.arrival = s.business_date

    JOIN
        `tabCustomer` c ON c.name = r.guest
    LEFT JOIN
        `tabGuest Comment` cc ON r.guest = cc.guest AND cc.reservation IS NULL
    LEFT JOIN
        `tabGuest Comment` rc ON r.guest = rc.guest AND rc.reservation = r.name
    LEFT JOIN
        v_room_date rd ON r.room = rd.room AND rd.for_date = s.for_date
    WHERE
        1=1
        {room_status_condition}
        {reservation_condition}
        {guest_condition}
        {reservation_status_condition}
        {room_assigned_condition}
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
        s.business_date,
        r.room_type,
        rd.out_of_order_status,
        r.company_profile,
        r.travel_agent,
        rd.out_of_order_reason,
        r.creation
    ORDER BY r.room;
    """
    data = frappe.db.sql(query, as_dict=1)
    return columns, data
