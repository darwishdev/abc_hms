frappe.views.calendar["Reservation"] = {
    field_map: {
        start: "arrival",
        end: "departure",
        id: "name",
        allDay: "all_day",
        title: "guest",
        status: "reservation_status",
    },
    style_map: {
        Public: "success",
        Private: "info",
    },
    order_by: "arrival",
};
