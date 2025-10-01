// Copyright (c) 2025, DarwishDev and contributors
// For license information, please see license.txt

frappe.query_reports["In House"] = {
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
            fieldname: "reservation",
            fieldtype: "Link",
            label: __("Reservation"),
            options: "Reservation",
            reqd: 0,
            wildcard_filter: 0,
        },
        {
            fieldname: "guest",
            fieldtype: "Link",
            label: __("Guest"),
            options: "Customer",
            reqd: 0,
            wildcard_filter: 0,
        },
        {
            fieldname: "complementry",
            label: __("Complementary"),
            fieldtype: "Select",
            options: ["", "Yes", "No"],
        },
        {
            fieldname: "house_use",
            label: __("House Use"),
            fieldtype: "Select",
            options: ["", "Yes", "No"],
        },

        {
            fieldname: "reservation_status",
            fieldtype: "Select",
            label: __("Reservation Status"),
            options: "\nArrival\nIn House\nDeparture\nChecked Out",
            default: "In House",
            reqd: 0,
            wildcard_filter: 0,
        },
        {
            fieldname: "room_status",
            fieldtype: "Select",
            label: __("Room Status"),
            options: (function () {
                // Dynamically fetch room status options from the lookup table
                let options = "\n"; // Start with empty option
                frappe.call({
                    method: "abc_hms.room_date_lookup_list",
                    type: "GET",
                    args: {
                        lookup_types: "room_status",
                    },
                    async: false,
                    callback: function ({ message }) {
                        options = ["", ...Object.keys(message.room_status)];
                        console.log("response is", Object.keys(message.room_status));
                    },
                });
                return options;
            })(),
            reqd: 0,
            wildcard_filter: 0,
        },
        {
            fieldname: "is_arrival",
            fieldtype: "Check",
            label: __("Is Arrival"),
            reqd: 0,
            wildcard_filter: 0,
        },
        {
            fieldname: "is_departure",
            fieldtype: "Check",
            label: __("Is Departure"),
            reqd: 0,
            wildcard_filter: 0,
        },
    ],
};
