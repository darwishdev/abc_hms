frappe.query_reports["Front Desk Arrivals"] = {
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
            fieldname: "reservation",
            fieldtype: "Link",
            label: __("Reservation"),
            options: "Reservation",
            reqd: 0,
            wildcard_filter: 0,
        },
        {
            fieldname: "room_assigned",
            label: __("Room Assigned"),
            fieldtype: "Select",
            options: "\nYes\nNo",
        },
        {
            fieldname: "reservation_status",
            label: __("Reservation Status"),
            fieldtype: "Select",
            options: "\nArrival\nIn House",
            default: "Confirmed",
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
    ],
    get_datatable_events(events) {
        console.log("eventssss", events);
        events.onCellEdit = (cell, rowIndex, colIndex, value, oldValue) => {
            console.log("Edited:", {
                row: options.data[rowIndex],
                column: options.columns[colIndex].id,
                value,
                oldValue,
            });
        };
        return events;
    },

    getEditor: function (colIndex, rowIndex, value, parent, column, row, data) {
        // colIndex, rowIndex of the cell being edited
        // value: value of cell before edit
        // parent: edit container (use this to append your own custom control)
        // column: the column object of editing cell
        // row: the row of editing cell
        // data: array of all rows
        console.log("get editor");
        const control = frappe.ui.form.make_control({
            parent: parent,
            df: {
                label: "",
                fieldname: doctype,
                fieldtype: "Link",
                options: doctype,
            },
            render_input: true,
            only_input: true,
        });

        let oldValue = "";

        return {
            // called when cell is being edited
            initValue(value) {
                control.input.focus();
                control.input.value = value;
                oldValue = value;
            },
            // called when cell value is set
            setValue(newValue) {
                // ----------- Do whatever is needed here.
                control.input.value = newValue;
            },
            // value to show in cell
            getValue() {
                return control.input.value;
            },
        };
    },
    get_datatable_options(options) {
        options.getEditor = function (colIndex, rowIndex, value, parent, column, row, data) {
            if (column.fieldname === "room") {
                console.log("Creating input editor for Room...");

                // create input
                const $input = document.createElement("input");
                $input.type = "text";
                $input.classList.add("form-control"); // optional bootstrap style
                parent.appendChild($input);

                return {
                    // when editing starts
                    initValue(val) {
                        $input.value = val || "";
                        $input.focus();
                    },
                    // when cell is updated programmatically
                    setValue(val) {
                        console.log(
                            "value changed setVal",
                            row[colIndex],
                            data.name,
                            colIndex,
                            val,
                            row,
                            rowIndex,
                            data,
                        );
                        frappe.call({
                            method: "frappe.client.set_value",
                            args: {
                                doctype: "Reservation",
                                name: data.name,
                                fieldname: "room",
                                value: val,
                            },
                            callback: function (r) {
                                if (!r.exc) {
                                    frappe.show_alert({
                                        message: __("Room updated successfully"),
                                        indicator: "green",
                                    });
                                } else {
                                    $input.value = val || "";
                                    frappe.show_alert({
                                        message: __("Error updating room"),
                                        indicator: "red",
                                    });
                                }
                            },
                        });
                    },
                    // return final value for the cell
                    getValue() {
                        console.log("value changed here getVal");
                        return $input.value;
                    },
                };
            }
        };

        return options;
    },
    onload: function (report) {
        report.page.add_inner_button(__("Save Rooms"), function () {
            console.log(report);
            const data = report.data;
            const reservation_room = {};

            // Iterate through the data to find changed rooms
            data.forEach((row) => {
                if (row.room) {
                    reservation_room[row.name] = row.room;
                }
            });
            console.log(reservation_room);
        });
    },
};
