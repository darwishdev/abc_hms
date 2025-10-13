frappe.listview_settings["Reservation"] = {
    get_indicator: function (doc) {
        const s =
            doc.reservation_status ||
            (doc.docstatus == 0 ? "Draft" : doc.docstatus == 1 ? "Submitted" : "Cancelled");

        //const is_due_out = doc.departure == ''
        // mapping -> [label, css_class, filter_string]
        const m = {
            Confirmed: [__("Confirmed"), "blue", "reservation_status,=,Confirmed"],
            "In House": [__("In House"), "green", "reservation_status,=,Checked In"],
            Arrival: [__("Arrival"), "orange", "reservation_status,=,Checked In"],
        };

        return m[s] || [__(s), "grey", `reservation_status,=,${s}`];
    },
};
