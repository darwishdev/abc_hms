frappe.views.gantt["Reservation"] = {
    field_map: {
        start: "arrival", // start date field
        end: "departure", // end date field
        id: "name", // unique identifier
        title: "room", // display label (room, guest, etc.)
        progress: "progress", // optional numeric field (0–100)
        dependencies: "depends_on", // optional
    },
    options: {
        header_height: 50,
        column_width: 30,
        step: 24 * 60 * 60 * 1000, // one day
        view_modes: ["Day", "Week", "Month"],
        bar_height: 20,
        bar_corner_radius: 3,
        arrow_curve: 5,
    },
    get_events_method: "frappe.desk.gantt.get_events",
};
