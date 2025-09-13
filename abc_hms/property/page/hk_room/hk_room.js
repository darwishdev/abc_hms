const render_table = (data) => {
    if (!data.length) {
        $("#hk-room-table").html("<p>No rooms found</p>");
        return;
    }

    let columns = Object.keys(data[0]).map((k) => ({
        id: k,
        name: frappe.utils.to_title_case(k),
        width: 150,
    }));

    const datatable = new DataTable("#hk-room-table", {
        columns: columns,
        data: data,
        layout: "fluid",
        inlineFilters: true,
        serialNoColumn: true,
    });
    return datatable;
};
const reload_table = (filter_controls) => {
    let filters = {};
    Object.keys(filter_controls).forEach((k) => {
        filters[k] = filter_controls[k].get_value();
    });

    // Require date_range
    if (!filters.date_range) {
        $("#hk-room-table").html(
            "<p class='text-muted'>Please select a Date Range to view rooms.</p>",
        );
        return; // stop here, don't fetch
    }

    console.log("filters:", filters);

    fetch_rooms(filters, function (data) {
        render_table(data);
    });
};
const fetch_lookups = () => {
    return new Promise((resolve, reject) => {
        frappe.call({
            method: "abc_hms.inventory_lookup_list",
            type: "get",
            args: {
                lookup_types: "ooo_status",
            },
            callback: function (r) {
                if (r.exc) {
                    frappe.msgprint({
                        title: __("Error"),
                        message: __("Server Error: " + r.exc),
                        indicator: "red",
                    });
                    reject(r.exec);
                }
                return resolve(r.message.ooo_status);
            },
        });
    });
};
const fetch_rooms = (args, callback) => {
    frappe.call({
        method: "abc_hms.room_status_list",
        type: "GET",
        args,
        callback: function (r) {
            if (r.message) {
                callback(r.message);
            } else {
                callback([]);
            }
        },
    });
};
const generate_filters = (df_array, parent) => {
    const filter_controls = {};
    df_array.forEach((df) => {
        let control = frappe.ui.form.make_control({
            df: df,
            parent: parent,
            render_input: true,
        });
        filter_controls[df.fieldname] = control;
    });
    return filter_controls;
};

// Render radios into the HTML field
const show_change_status_dialog = () => {
    fetch_lookups().then((ooo_status) => {
        // const options = Object.keys(resp).map((k) => k);
        const selectOptions = Object.entries(ooo_status)
            .map(([label, value]) => `${label}:${value}`)
            .join("\n");
        const d = new frappe.ui.Dialog({
            title: "Change Room Status",
            fields: [
                { label: "Date Range", fieldname: "date_range", fieldtype: "DateRange", reqd: 1 },
                { label: "Room", fieldname: "room", fieldtype: "Link", options: "Room", reqd: 1 },
                {
                    fieldname: "ooo_status_html",
                    fieldtype: "HTML",
                    req: 1,
                },
                {
                    label: "Reason",
                    fieldname: "reason",
                    fieldtype: "Link",
                    options: "OOO Reason",
                    req: 1,
                },
            ],
            primary_action_label: "Submit",
            primary_action(values) {
                try {
                    // ✅ get selected radio manually
                    const selected = d.$wrapper.find("input[name='ooo_status']:checked").val();
                    if (!selected) {
                        frappe.msgprint("Please select an Out of Order status");
                        return;
                    }
                    values.ooo_status = selected;

                    console.log("selected is here", selected);
                    frappe.call({
                        method: "abc_hms.inventory_upsert",
                        args: { payload: values },
                        callback: (r) => {
                            console.log("response is", r);
                            d.hide();
                        },
                    });
                } catch (error) {
                    console.error("failed to update inventory", error);
                }
            },
        });
        d.fields_dict.ooo_status_html.$wrapper.html(
            Object.entries(ooo_status)
                .map(
                    ([label, value]) =>
                        `<label style="display:block;margin-bottom:6px;">
                <input type="radio" name="ooo_status" value="${value}" ${value === 0 ? "checked" : ""}> ${label}
             </label>`,
                )
                .join(""),
        );
        d.show();
    });
};

frappe.pages["hk-room"].on_page_load = function (wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "House Keeping Rooms Control",
        single_column: true,
    });
    $(page.body).html(`
        <div class="p-4">
            <div class="hk-filters mb-4" id="hk-room-filters"></div>
            <div id="hk-room-table"></div>
        </div>
    `);
    page.set_primary_action("Change Status", () => {
        show_change_status_dialog();
    });

    page.set_secondary_action("Set OOO", () => {
        frappe.msgprint("Hello World");
    });

    page.add_menu_item("Refresh", () => {
        reload_table(filter_controls);
    });

    const filters_df = [
        {
            label: "Date Range",
            fieldtype: "DateRange",
            fieldname: "date_range",
            reqd: 1,
        },
        {
            label: "Property",
            class: "hk_filter",
            fieldtype: "Link",
            options: "Property",
            fieldname: "property",
        },
        {
            label: "Room Category",
            fieldtype: "Link",
            options: "Room Category",
            fieldname: "room_category",
        },
        {
            label: "Room Type",
            fieldtype: "Link",
            options: "Room Type",
            fieldname: "room_type",
        },
        {
            label: "HK Section",
            fieldtype: "Link",
            options: "House Keeping Section",
            fieldname: "hk_section",
        },
    ];

    filter_controls = generate_filters(filters_df, $("#hk-room-filters"));
    Object.values(filter_controls).forEach((control) => {
        console.log("consotler");
        control.df.onchange = () => reload_table(filter_controls);
    });
    reload_table(filter_controls);
};
