frappe.query_reports["HK Arrivals"] = {
    filters: [
        {
            fieldname: "property",
            fieldtype: "Link",
            label: __("Property"),
            options: "Property",
            default: "CHNA",
            reqd: 1,
            wildcard_filter: 0,
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
            fieldname: "reservation_status",
            label: __("Reservation Status"),
            fieldtype: "Select",
            options: "\nArrival\nIn House",
            default: "Arrival",
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
            fieldname: "room_status",
            fieldtype: "Select",
            label: __("Room Status"),
            options: (function () {
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
    ],

    onload: function (report) {
        report.page.add_inner_button(__("Update Room Status"), function () {
            // get selected rows
            const selected = getSelectedRows(report.datatable);

            if (!selected.length) {
                frappe.msgprint(__("Please select at least one room"));
                return;
            }

            // extract room numbers from selection
            const room_numbers = selected.map((row) => row.room);

            // open a dialog to pick new status
            const d = new frappe.ui.Dialog({
                title: __("Update Room Status"),
                fields: [
                    {
                        fieldname: "room_status",
                        label: __("Room Status"),
                        fieldtype: "Select",
                        options: ["Clean", "Dirty"], // or dynamically load from lookup
                        reqd: 1,
                    },
                ],
                primary_action_label: __("Update"),
                primary_action(values) {
                    d.hide();

                    // call your API with multiple rooms
                    frappe
                        .call("abc_hms.room_date_bulk_upsert", {
                            room_numbers,
                            for_date: 20250807, // you can make this dynamic from filter
                            updated_fields: {
                                room_status: values.room_status == "Clean" ? 1 : 0,
                            },
                            commit: true,
                        })
                        .then(() => {
                            frappe.show_alert({
                                message: __("Rooms updated successfully"),
                                indicator: "green",
                            });
                            report.refresh(); // reload report after update
                        })
                        .catch(() => {
                            frappe.show_alert({
                                message: __("Error updating rooms"),
                                indicator: "red",
                            });
                        });
                },
            });

            d.show();
        });
    },
    get_datatable_options(options) {
        options.checkboxColumn = true;
        options.multiSelect = true;
        options.getEditor = function (colIndex, rowIndex, value, parent, column, row, data) {
            if (column.fieldname === "room_status") {
                const $select = document.createElement("select");
                $select.classList.add("form-control");

                // populate dropdown
                ["Clean", "Dirty"].forEach((opt) => {
                    const option = document.createElement("option");
                    option.value = opt;
                    option.textContent = opt;
                    if (opt === value) option.selected = true;
                    $select.appendChild(option);
                });

                parent.appendChild($select);

                return {
                    initValue(val) {
                        $select.value = val || "";
                        $select.focus();
                    },
                    setValue(val) {
                        console.log("setting valuieeesss");
                        $select.value = val;
                        frappe
                            .call("abc_hms.room_date_bulk_upsert", {
                                room_numbers: [data.room],
                                for_date: 20250807,
                                updated_fields: {
                                    room_status: 1,
                                },
                                commit: true,
                            })
                            .then(({ message }) => {
                                frappe.show_alert({
                                    message: __("Room updated successfully"),
                                    indicator: "green",
                                });
                            })
                            .catch((e) => {
                                frappe.show_alert({
                                    message: __("Error updating room"),
                                    indicator: "red",
                                });
                            });
                    },
                    getValue() {
                        return $select.value;
                    },
                };
            }
        };

        return options;
    },
};

function getSelectedRows(datatable) {
    const selected = [];
    console.log(datatable);
    datatable.rowmanager.checkMap.forEach((checked, idx) => {
        if (checked) {
            console.log("sels", checked, idx);
            const row = datatable.datamanager.data[idx];

            console.log("sels", row);
            selected.push(row);
        }
    });
    return selected;
}
