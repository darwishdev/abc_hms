import frappe

def execute(filters=None):
    if not filters:
        filters = {}

    columns = [
        {"fieldname": "room", "label": "Room", "fieldtype": "Link", "options": "Room"},
        {"fieldname": "room_status", "label": "Room Status", "fieldtype": "Data"},
        {"fieldname": "base_rate", "label": "Base Rate", "fieldtype": "Currency"},
        {"fieldname": "guest", "label": "Guest", "fieldtype": "Link", "options": "Customer"},
        {"fieldname": "name", "label": "Reservation", "fieldtype": "Link", "options": "Reservation"},
        {"fieldname": "departure", "label": "Departure", "fieldtype": "Date"},
        {"fieldname": "room_type", "label": "Room Type", "fieldtype": "Link", "options": "Room Type"},
        {"fieldname": "guest_comment", "label": "Guest Comments", "fieldtype": "Data"},
        {"fieldname": "reservation_comment", "label": "Reservation Comments", "fieldtype": "Data"},
        {"fieldname": "out_of_order_status", "label": "OOO Status", "fieldtype": "Data"},
        {"fieldname": "company_profile", "label": "Company Profile", "fieldtype": "Link", "options": "Customer"},
        {"fieldname": "travel_agent", "label": "Travel Agent", "fieldtype": "Link", "options": "Sales Partner"},
        {"fieldname": "out_of_order_reason", "label": "OOO Reason", "fieldtype": "Data"},
        {"fieldname": "creation", "label": "Created At", "fieldtype": "Datetime"}
    ]

    # Build dynamic conditions
    date_condition = f"'{filters.get('date_filter')}'" if filters.get('date_filter') else "s.business_date"
    property_value = filters.get('property', 'CONA')  # Default to 'CONA' if not provided
    reservation_status_condition = f"r.reservation_status = '{filters.get('reservation_status')}'" if filters.get('reservation_status') else "1=1"

    query = f"""
    WITH date_filter AS (
        SELECT d.for_date, d.date_actual
        FROM dim_date d
        JOIN `tabProperty Setting` s ON s.property = '{property_value}'
            AND d.date_actual = COALESCE({date_condition}, s.business_date)
    )
    SELECT
        r.room,
        COALESCE(rd.room_status, 'Dirty') AS room_status,
        r.base_rate,
        r.guest,
        r.name,
        r.departure,
        r.room_type,
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
        tabReservation r ON r.arrival = d.date_actual
    LEFT JOIN
        `tabGuest Comment` cc ON r.guest = cc.guest AND cc.reservation IS NULL
    LEFT JOIN
        `tabGuest Comment` rc ON r.guest = rc.guest AND rc.reservation = r.name
    LEFT JOIN
        v_room_date rd ON r.room = rd.room AND rd.for_date = d.for_date
    WHERE
        {reservation_status_condition}
    GROUP BY
        r.room,
        rd.room_status,
        r.base_rate,
        r.guest,
        r.name,
        r.departure,
        r.room_type,
        rd.out_of_order_status,
        r.company_profile,
        r.travel_agent,
        rd.out_of_order_reason,
        r.creation;
    """

    print("Final query is:", query)
    data = frappe.db.sql(query, as_dict=1)
    return columns, data
