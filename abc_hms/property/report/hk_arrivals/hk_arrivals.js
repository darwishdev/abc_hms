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
            fieldname: "hk_sesction",
            fieldtype: "Link",
            label: __("HK Sesction"),
            options: "House Keeping Section",
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
        frappe
            .call({
                method: "abc_hms.property_setting_find",
                type: "GET",
                args: { property_name: "CHNA" },
            })
            .then(({ message }) => {
                report._business_date = message.business_date;

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
                                    from_date: report._business_date, // you can make this dynamic from filter
                                    to_date: report._business_date, // you can make this dynamic from filter
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
            });
    },
    get_datatable_options(options) {
        options.checkboxColumn = true;
        options.multiSelect = true;
        options.getEditor = function (colIndex, rowIndex, value, parent, column, row, data) {
            const business_date = row[2].content;
            //frappe.throw(`${JSON.stringify(row)})`);
            if (column.fieldname === "discrepency") {
                const $input = document.createElement("input");
                $input.type = "number";
                $input.classList.add("form-control");
                $input.step = "1";
                $input.min = "0";
                // set initial value right away (datatable may call initValue too)
                if (value !== undefined && value !== null) $input.value = value;

                // append to parent cell
                parent.appendChild($input);

                // call update helper
                const updateRoom = (val) => {
                    // ensure number (or null if empty)
                    const parsed = val === "" ? null : Number(val);
                    frappe
                        .call("abc_hms.room_date_bulk_upsert", {
                            room_numbers: [data.room],
                            from_date: business_date,
                            to_date: business_date,
                            updated_fields: {
                                persons: parsed,
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
                };

                // update on change/blur so it's responsive
                $input.addEventListener("change", (e) => updateRoom(e.target.value));
                $input.addEventListener("blur", (e) => updateRoom(e.target.value));

                return {
                    initValue(val) {
                        // datatable may call this to set initial displayed value
                        $input.value = val === undefined || val === null ? "" : val;
                        $input.focus();
                    },
                    setValue(val) {
                        // called when the datatable wants to update the editor programatically
                        $input.value = val === undefined || val === null ? "" : val;
                        // optionally call updateRoom here if you want saving to happen when datatable invokes setValue
                        updateRoom($input.value);
                    },
                    getValue() {
                        return $input.value;
                    },
                };
            }
            if (column.fieldname === "guest_service_status") {
                const $select = document.createElement("select");
                $select.classList.add("form-control");
                const options = ["No Status", "Make Up", "DND"];

                // populate dropdown
                options.forEach((opt) => {
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
                        const guest_service_status = options.indexOf(val);
                        //frappe.throw(`va${val}`);
                        frappe
                            .call("abc_hms.room_date_bulk_upsert", {
                                room_numbers: [data.room],
                                from_date: business_date, // you can make this dynamic from filter
                                to_date: business_date, // you can make this dynamic from filter

                                updated_fields: {
                                    guest_service_status,
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
            if (column.fieldname === "house_keeping_status") {
                const $select = document.createElement("select");
                $select.classList.add("form-control");
                const options = ["Vacant", "OCC"];
                // populate dropdown
                options.forEach((opt) => {
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
                        const house_keeping_status = options.indexOf(val);
                        //frappe.throw(`va${val}`);
                        frappe
                            .call("abc_hms.room_date_bulk_upsert", {
                                room_numbers: [data.room],
                                from_date: business_date, // you can make this dynamic from filter
                                to_date: business_date, // you can make this dynamic from filter

                                updated_fields: {
                                    house_keeping_status,
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
            if (column.fieldname === "room_status") {
                const $select = document.createElement("select");
                $select.classList.add("form-control");
                const options = ["Dirty", "Clean", "Inspected"];
                // populate dropdown
                options.forEach((opt) => {
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
                        const room_status = options.indexOf(val);
                        //frappe.throw(`va${val}`);
                        frappe
                            .call("abc_hms.room_date_bulk_upsert", {
                                room_numbers: [data.room],
                                from_date: business_date, // you can make this dynamic from filter
                                to_date: business_date, // you can make this dynamic from filter

                                updated_fields: {
                                    room_status,
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
