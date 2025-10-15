frappe.listview_settings["Reservation"] = {
    add_fields: ["property", "reservation_status", "arrival", "business_date"],
    get_indicator: function (doc) {
        const s =
            doc.reservation_status ||
            (doc.docstatus == 0 ? "Draft" : doc.docstatus == 1 ? "Submitted" : "Cancelled");

        const m = {
            Confirmed: [__("Confirmed"), "blue", "reservation_status,=,Confirmed"],
            "In House": [__("In House"), "green", "reservation_status,=,Checked In"],
            Arrival: [__("Arrival"), "orange", "reservation_status,=,Checked In"],
        };

        return m[s] || [__(s), "grey", `reservation_status,=,${s}`];
    },

    onload: function (listview) {
        update_business_dates(listview);
    },
};

async function update_business_dates(listview) {
    const rows = listview.data || [];
    if (!rows.length) return;

    for (const row of rows) {
        if (!row.property) continue;

        try {
            const r = await frappe.db.get_value("Property Setting", row.property, "business_date");

            const business_date = r?.message?.business_date || "";
            const row_el = listview.$result.find(`[data-name="${row.name}"]`);
            if (row_el && !row_el.find(".col-busdate").length) {
                // Append a new cell for business date
                row_el.append(
                    `<div class="list-row-col ellipsis col-busdate" title="${business_date}">
                        ${frappe.format(business_date, { fieldtype: "Date" })}
                    </div>`,
                );
            }
        } catch (e) {
            console.error("Error fetching business date:", e);
        }
    }
}
