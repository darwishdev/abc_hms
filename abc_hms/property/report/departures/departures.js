// Copyright (c) 2025, DarwishDev and contributors
// For license information, please see license.txt

frappe.query_reports["Departures"] = {
    filters: [
        {
            fieldname: "property",
            fieldtype: "Link",
            label: __("Property"),
            options: "Property",
            default: "CONA",
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
            options: "\nIn House\nChecked Out",
            reqd: 0,
            wildcard_filter: 0,
        },
    ],
};
