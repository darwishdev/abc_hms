frappe.pages["room_availability"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Room Availability",
        single_column: true,
    });

    const dateController = window.createDateRangeController({
        fromKey: "date_from",
        nightsKey: "nights",
        toKey: "date_to",
        get: (key) => frm.doc[key],
        set: (key, value) => frm.set_value(key, value),
    });
    const filters = [
        {
            fieldname: "date_range",
            label: __("Date Range"),
            fieldtype: "DateRange",
            reqd: 1,
            default: [
                frappe.datetime.get_today(),
                frappe.datetime.add_days(frappe.datetime.get_today(), 37),
            ],
        },
        {
            fieldname: "property",
            label: __("Property"),
            default: "CHNA",
            fieldtype: "Link",
            options: "Property",
            reqd: 1,
        },
        {
            fieldname: "room_category",
            label: __("Room Category"),
            fieldtype: "Link",
            options: "Room Category",
        },
        {
            fieldname: "room_type",
            label: __("Room Type"),
            fieldtype: "Link",
            options: "Room Type",
        },
    ];

    filters.forEach((filter) => {
        page.add_field(filter);
    });

    page.set_primary_action(__("Search"), function () {
        load_availability_data();
    });
    page.set_secondary_action(__("Update Room Status"), function () {
        frappe.call({
            method: "abc_hms.room_date_lookup_list",
            type: "GET",
            args: {
                lookup_types: "room_status,house_keeping_status,service_status,ooo_status",
            },
            async: false,
            callback: function ({ message }) {
                const rs_options = ["", ...Object.keys(message.room_status)];
                const hk_options = ["", ...Object.keys(message.house_keeping_status)];
                const ss_options = ["", ...Object.keys(message.service_status)];
                const ooo_options = ["", ...Object.keys(message.ooo_status)];

                let _updatingDates = false;

                function parseIntSafe(v) {
                    const n = Number(v);
                    return Number.isFinite(n) ? Math.floor(n) : null;
                }

                function addDaysToDateString(dateStr, days) {
                    if (!dateStr) return null;
                    // convert to Date object using frappe helper and mutate
                    const d = frappe.datetime.str_to_obj(dateStr);
                    d.setDate(d.getDate() + days);
                    return frappe.datetime.obj_to_str(d);
                }
                function updateDates(changedBy) {
                    // guard: prevent recursive re-entry when we set_value programmatically
                    if (_updatingDates) return;
                    _updatingDates = true;

                    try {
                        const from = dialog.get_value("from"); // "YYYY-MM-DD" or null
                        const nightsRaw = dialog.get_value("nights"); // number or string
                        const to = dialog.get_value("to"); // "YYYY-MM-DD" or null

                        const nights = parseIntSafe(nightsRaw);

                        // Helper to set safely (only set when different)
                        function safeSet(field, value) {
                            const cur = dialog.get_value(field);
                            if (value === null || value === undefined) return;
                            if (String(cur) !== String(value)) {
                                dialog.set_value(field, value);
                            }
                        }

                        if (changedBy === "from") {
                            // If user changed "from" and nights exists -> set "to" = from + nights
                            if (from && Number.isFinite(nights)) {
                                const newTo = addDaysToDateString(from, nights);
                                safeSet("to", newTo);
                            } else if (from && to) {
                                // recalc nights = diff(to, from)
                                const diff = frappe.datetime.get_day_diff(to, from);
                                if (diff >= 0) safeSet("nights", diff);
                            }
                        } else if (changedBy === "nights") {
                            // If user changed nights and from exists -> set to
                            if (from && Number.isFinite(nights)) {
                                const newTo = addDaysToDateString(from, nights);
                                safeSet("to", newTo);
                            } else if (to && Number.isFinite(nights)) {
                                // if nights set & to exists -> recalc from = to - nights
                                const newFrom = addDaysToDateString(to, -nights);
                                safeSet("from", newFrom);
                            }
                        } else if (changedBy === "to") {
                            // If user changed To and From exists -> recalc nights
                            if (from && to) {
                                console.log("from , to", from, to, to < from);
                                if (to < from) {
                                    safeSet("nights", 0);
                                    safeSet("from", to);
                                    return;
                                }
                                const diff = frappe.datetime.get_day_diff(to, from);
                                if (diff >= 0) safeSet("nights", diff);
                            } else if (Number.isFinite(nights) && to) {
                                // from = to - nights
                                const newFrom = addDaysToDateString(to, -nights);
                                safeSet("from", newFrom);
                            }
                        }
                    } catch (err) {
                        console.error("updateDates error:", err);
                    } finally {
                        // release guard after updates
                        _updatingDates = false;
                    }
                }
                const dialog = new frappe.ui.Dialog({
                    title: "Enter Room Details",
                    fields: [
                        // Row 1: Room Type | Room
                        {
                            label: "Room Type",
                            fieldname: "room_type",
                            fieldtype: "Link",
                            options: "Room Type",
                            filters: { pay_master: false },
                        },
                        { fieldtype: "Column Break" },
                        {
                            label: "Room",
                            fieldname: "room",
                            fieldtype: "Link",
                            options: "Room",
                            reqd: 1,
                            get_query: () => {
                                const room_type = dialog.get_value("room_type");
                                if (room_type) return { filters: { room_type } };
                                return {
                                    filters: { pay_master: false },
                                    query: "abc_hms.room_list_input",
                                };
                            },
                        },

                        // Row 2: From | Nights | To
                        { fieldtype: "Section Break" },
                        {
                            label: "From",
                            fieldname: "from",
                            fieldtype: "Date",
                            onchange: () => updateDates("from"),
                            reqd: 1,
                        },
                        { fieldtype: "Column Break" },
                        {
                            label: "Nights",
                            onchange: () => updateDates("nights"),
                            fieldname: "nights",
                            fieldtype: "Int",
                            reqd: 1,
                        },
                        { fieldtype: "Column Break" },
                        {
                            label: "To",
                            onchange: () => updateDates("to"),
                            fieldname: "to",
                            fieldtype: "Date",
                            reqd: 1,
                        },

                        // Row 3: Room Status | Housekeeping Status
                        { fieldtype: "Section Break" },
                        {
                            label: __("Room Status"),
                            fieldname: "room_status",
                            fieldtype: "Select",
                            options: rs_options,
                        },
                        { fieldtype: "Column Break" },
                        {
                            label: __("Housekeeping Status"),
                            fieldname: "house_keeping_status",
                            fieldtype: "Select",
                            options: hk_options,
                        },

                        // Row 4: Service Status | OOO Status
                        { fieldtype: "Section Break" },
                        {
                            label: __("Service Status"),
                            fieldname: "service_status",
                            fieldtype: "Select",
                            options: ss_options,
                        },
                        { fieldtype: "Column Break" },
                        {
                            label: __("Out of Order Status"),
                            fieldname: "ooo_status",
                            fieldtype: "Select",
                            options: ooo_options,
                            onchange: () => {
                                const ooo_status = dialog.get_value("ooo_status");
                                const isOOO = ["OOO", "OOS"].includes(ooo_status);

                                // toggle visibility + required state
                                dialog.set_df_property("ooo_reason", "reqd", isOOO);
                                dialog.set_df_property("ooo_reason", "hidden", !isOOO);

                                if (!isOOO) {
                                    dialog.set_value("ooo_reason", "");
                                }
                            },
                        },

                        { fieldtype: "Column Break", fieldname: "ooo_col", hidden: 1 },
                        {
                            label: __("OOO Reason"),
                            fieldname: "ooo_reason",
                            fieldtype: "Data",
                            reqd: 0,
                            hidden: 1,
                            column: 12,
                        },
                    ],
                    primary_action_label: "Submit",
                    primary_action(values) {
                        const room_numbers = [values.room];
                        const room_status = message.room_status[values.room_status] || null;
                        const house_keeping_status =
                            message.house_keeping_status[values.house_keeping_status] || null;
                        const guest_service_status = message.service_status
                            ? message.service_status[values.service_status] || null
                            : null;
                        console.log("stis", message.out_of_order_status);
                        const out_of_order_status = message.ooo_status
                            ? message.ooo_status[values.ooo_status] || 0
                            : 0;
                        // Step 2: build the updated_fields map
                        const updated_fields = {
                            room_status,
                            house_keeping_status,
                            guest_service_status,
                            out_of_order_status,
                            out_of_order_reason:
                                ["OOO", "OOS"].includes(values.ooo_status) && values.ooo_reason
                                    ? values.ooo_reason
                                    : null,
                        };

                        // Clean up nulls (optional)
                        Object.keys(updated_fields).forEach(
                            (key) => updated_fields[key] == null && delete updated_fields[key],
                        );

                        // Step 3: build the payload
                        const payload = {
                            room_numbers,
                            from_date: values.from,
                            to_date: values.to,
                            updated_fields,
                            commit: true,
                        };
                        frappe.call("abc_hms.room_date_bulk_upsert", payload).then((res) => {
                            frappe.msgprint(__("Room status updated successfully."));
                            dialog.hide();
                            console.log("Response is here", res);
                        });
                        // dialog.hide();
                    },
                });

                dialog.show();
            },
        });
    });

    const $result_container = $('<div class="result-container" style="margin-top: 20px;"></div>');
    $(page.body).append($result_container);
    function load_availability_data() {
        console.log("loading data");
        const date_range = page.fields_dict.date_range.get_value();
        const property = page.fields_dict.property.get_value();
        const room_category = page.fields_dict.room_category.get_value();
        const room_type = page.fields_dict.room_type.get_value();

        // Validate required fields
        if (!date_range || !date_range[0] || !date_range[1]) {
            frappe.msgprint(__("Please select a date range"));
            return;
        }

        if (!property) {
            frappe.msgprint(__("Please select a property"));
            return;
        }

        const [p_from, p_to] = date_range;

        // Call the server method
        frappe.call({
            method: "abc_hms.room_availability_list",
            type: "GET",
            args: {
                p_from: p_from,
                p_to: p_to,
                p_property: property,
                p_room_category: room_category || null,
                p_room_type: room_type || null,
            },
            callback: function (r) {
                if (r.message) {
                    // Prepare context for Diary
                    const context = {
                        columns: ["group_1"],
                        options: {
                            from: p_from,
                            dates_column: "details",
                            subgroup_key: "data",
                            to: p_to,
                            view: "week",
                        },
                        data: r.message || [],
                    };

                    // Render Diary
                    new Diary($result_container[0], context);
                } else {
                    $result_container.html(`
                        <div class="alert alert-info" style="margin-top:20px;">
                            <i class="fa fa-info-circle"></i> No data found for the selected filters
                        </div>
                    `);
                }
            },
            error: function (r) {
                $result_container.html(`
                    <div class="alert alert-danger" style="margin-top:20px;">
                        <i class="fa fa-exclamation-triangle"></i>
                        Error loading data. Please check your filters and try again.
                    </div>
                `);
                console.error("Error:", r);
            },
        });
    }
};

class Diary {
    constructor(container, context) {
        this.container = container; // page.body
        this.options = context.options;
        this.start_date = this.options.from;
        this.context_columns = context.columns;
        this.subgroups_columns = context.subgroups_columns || [];
        this.window_start_date = new Date(this.options.from);
        this.from_date = new Date(context.options.from);
        this.to_date = new Date(context.options.to);
        this.window_end_date = this.end_date_from_view();
        this.columns = this.generate_columns([...context.columns, ...this.subgroups_columns]);
        this.context_data = context.data;
        // this.date_groups_config = this.get_date_groups_config();
        this.data = this.generate_data();

        // Render everything
        this.render_view_toolbar();
        this.render_template();
        this.render_diary();
    }

    diff_days(date1, date2) {
        // Create shallow copies so originals aren't mutated
        const d1 = new Date(date1);
        const d2 = new Date(date2);

        // Strip the time portion completely
        d1.setHours(0, 0, 0, 0);
        d2.setHours(0, 0, 0, 0);

        // Return integer difference in days
        return Math.round((d2 - d1) / 86400000); // 1000 * 60 * 60 * 24
    }
    render_view_toolbar() {
        let $toolbar = $(this.container).find("#tool-bar");

        // Toolbar already exists → just update
        if ($toolbar.length > 0) {
            $toolbar.find("button[data-view]").removeClass("btn-primary");
            $toolbar.find(`[data-view="${this.options.view}"]`).addClass("btn-primary");
            this.update_range_label();
            return; // exit early
        }

        const day_diff = this.diff_days(this.from_date, this.to_date);
        const month_button =
            day_diff >= 30
                ? `<button class="btn btn-default rounded btn-sm" data-view="month">Month</button>`
                : ``;

        $toolbar = $(`
        <div id='tool-bar' class="btn-group" style="margin-bottom: 10px; display: flex; gap: 6px; justify-content:flex-end; align-items: center;">
            <button class="btn btn-default btn-sm rounded nav-btn" style='max-width:7rem' data-action="prev">← Prev</button>
            <button class="btn btn-default btn-sm rounded nav-btn" style='max-width:7rem' data-action="next">Next →</button>
            <div class="btn-group" style="margin-left: 12px;">
                <button class="btn btn-default mr-2 rounded btn-sm" data-view="week">Week</button>
                ${month_button}
            </div>
            <span id="current-range" style="margin-left: 12px; font-size: 13px; opacity: 0.8;"></span>
        </div>
        <div id="filter-form" style="margin-top: 10px; display: flex; gap: 6px; align-items: center;"></div>
    `);

        $(this.container).prepend($toolbar);

        // Event bindings
        $toolbar.on("click", "button[data-view]", (e) => {
            const view_type = $(e.currentTarget).data("view");
            this.switch_view(view_type);
            $toolbar.find("button[data-view]").removeClass("btn-primary");
            $(e.currentTarget).addClass("btn-primary");
        });

        $toolbar.on("click", ".nav-btn", (e) => {
            const action = $(e.currentTarget).data("action");
            this.navigate_window(action);
        });

        // Initial update
        this.update_range_label();
    }

    refresh_view() {
        this.columns = this.generate_columns([...this.context_columns, ...this.subgroups_columns]);
        this.data = this.generate_data();
        $(this.container).find("#datatable-container").empty();
        this.render_diary();
        this.update_range_label();
    }

    add_days(date, days) {
        const result = new Date(date);
        result.setDate(result.getDate() + days);
        return result;
    }
    update_range_label() {
        const range = `${this.window_start_date.getDate()} → ${this.window_end_date.getDate()}`;
        $("#current-range").text(range);
    }

    // Utility to update Prev/Next button states
    update_nav_buttons() {
        const $toolbar = $(this.container).find("#tool-bar");
        const prev_disabled = this.window_start_date == this.from_date;
        const next_disabled = this.window_end_date == this.to_date;
        // const next_disabled = frappe.datetime.str_to_obj(this.window_end_date) >= to_limit;
        $toolbar.find(".nav-btn[data-action='prev']").prop("disabled", prev_disabled);
        $toolbar.find(".nav-btn[data-action='next']").prop("disabled", next_disabled);
    }
    navigate_window(direction) {
        const view = this.options.view;
        const boundary = direction === "prev" ? this.from_date : this.to_date;
        const old_date = direction === "prev" ? this.window_start_date : this.window_end_date;
        const date_days = view === "week" ? 7 : 30;
        const days_to_add = direction == "prev" ? date_days * -1 : date_days;
        let new_date = this.add_days(old_date, days_to_add);
        if (old_date == boundary) {
            console.log("boundary hit");
            return;
        }
        const boundary_exceeded = direction == "prev" ? new_date < boundary : new_date > boundary;
        if (boundary_exceeded) {
            new_date = boundary;
        }
        this.window_start_date = new_date;
        this.window_end_date = this.end_date_from_view();
        this.refresh_view();
        this.update_nav_buttons();
    }

    switch_view(view_type) {
        this.options.view = view_type;
        this.window_end_date = this.end_date_from_view();
        this.columns = this.generate_columns([...this.context_columns, ...this.subgroups_columns]);
        this.data = this.generate_data();
        $(this.container).find("#datatable-container").empty();
        this.render_diary();
    }

    generate_columns(columns) {
        const date_seq = this.date_sequence(this.window_start_date, this.window_end_date);
        return [...columns, "date_level_group", ...date_seq];
    }

    datatable_columns() {
        return this.columns.map((column) => {
            const dateObj = new Date(column);
            const column_is_date = !isNaN(dateObj.getTime()); // valid date check
            let label = column;
            function snakeToPascal(snakeStr) {
                return snakeStr
                    .split("_")
                    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(" ");
            }
            const result = {
                id: column,
                editable: false,
                resizable: false,
                sortable: false,
                freeze: 1,
                focusable: false,
                center: true,
                dropdown: false,
                width: 200,
            };

            if (column_is_date) {
                const day = dateObj.getDate();

                const dayName = dateObj.toLocaleDateString(undefined, { weekday: "short" }); // "Mon", "Tue", etc.
                label = `<div style='height:60px;font-size:.6rem'>${day}</br> (${dayName})</div>`;
                result["name"] = label;
                result["width"] = 170;
                result["freeze"] = 0;
                result["class"] = "date_column";
                return result;
            }
            return result;
        });
    }

    generate_date_row(group_name, current_row, date_values) {
        if (!date_values) {
            date_values = [];
        }
        const base_indent = this.options.subgroup_key ? 1 : 0;
        // const is_root_group = V gc
        const table_row = {
            date_level_group: group_name,
            indent: 0,
            // group_name == this.date_groups_config.default_group
            //     ? base_indent
            //     : base_indent + 1,
        };

        console.log("base indent", table_row);
        for (const column of this.context_columns) {
            table_row[column] = current_row[column];
        }
        for (const row_value of date_values) {
            const row_value_date = new Date(row_value.date);

            console.log(
                "columnsis",
                row_value_date >= this.window_start_date,
                row_value_date <= this.window_end_date,
            );
            if (
                row_value_date >= this.window_start_date &&
                row_value_date <= this.window_end_date
            ) {
                table_row[row_value.date] = row_value.value;
            }
        }

        return table_row;
    }
    generate_data() {
        let data = [];
        return this.context_data;
        for (const current_row of this.context_data) {
            if (this.options.subgroup_key) {
                const table_rows = this.generate_grouped_row(current_row);
                console.log("Group tab rows", table_rows);
                data = [...data, ...table_rows];
                continue;
            }

            const dates_column = current_row[this.options.dates_column];
            const table_rows = this.generate_date_rows(
                "",
                current_row,
                dates_column,
                this.context_columns,
            );
            data = [...data, ...table_rows];
        }
        return data;
    }

    get_date_groups_config() {
        // const data_arr = this.options.subgroup_key
        //     ? this.context_data[0][this.options.subgroup_key]
        //     : this.context_data;
        // const groups_map = {};
        // for (const current_row of data_arr) {
        //     const dates_column = current_row[this.options.dates_column];
        //     if (typeof dates_column === "object") {
        //         for (const row_value_key in dates_column) {
        //             groups_map[row_value_key] = 1;
        //         }
        //     }
        // }
        // const groups = Object.keys(groups_map);
        // const groups_without_first = groups.slice(1);
        // return { groups_map, default_group: groups[0], groups: groups_without_first };
    }

    date_sequence(from_date, to_date) {
        function formatDate(date) {
            const year = date.getFullYear();
            const month = String(date.getMonth() + 1).padStart(2, "0");
            const day = String(date.getDate()).padStart(2, "0");
            return `${year}-${month}-${day}`;
        }
        let start = from_date;
        let end = to_date;
        const dates = [];
        while (start <= end) {
            dates.push(formatDate(start));
            start = this.add_days(start, 1);
        }

        return dates;
    }

    end_date_from_view() {
        const view = this.options.view;
        const start = this.window_start_date;
        const date_days = view === "week" ? 7 : 30;
        let end = this.add_days(start, date_days);
        if (end > this.to_date) return this.to_date;
        return end;
    }

    render_template() {
        const html = `
            <div id="datatable-container" style="margin-top: 12px;"></div>
        `;
        $(html).appendTo(this.container);
    }

    render_diary() {
        const opts = {
            columns: this.datatable_columns(),
            data: this.data,
            treeView: true,
            freezeColumns: 2,
            layout: "fixed",
            clusterize: false,
        };
        this.datatable = new frappe.DataTable("#datatable-container", opts);
    }
}
