frappe.query_reports["Arrivals"] = {
    filters: [
        {
            fieldname: "property",
            fieldtype: "Link",
            label: __("Property"),
            options: "Property",
            default: "CHNA",
            reqd: 1, // This field is mandatory
            wildcard_filter: 0,
        },
        {
            fieldname: "date_filter",
            fieldtype: "Date",
            label: __("Date"),
            reqd: 0,
            wildcard_filter: 0,
            default: frappe.boot.business_date,
        },
        {
            fieldname: "reservation_status",
            fieldtype: "Select",
            label: __("Reservation Status"),
            options: "\nArrival\nIn House\nNo Show",
            reqd: 0,
            wildcard_filter: 0,
        },
    ],
};
