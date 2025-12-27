frappe.pages["Property Daily Sales"].on_page_load = function (wrapper) {
    // Create the page layout
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Daily Sales Dashboard",
        single_column: true,
    });

    // Filter area
    let filter_area = $('<div class="filter-area mb-3">').appendTo(page.main);

    // Date picker
    let date_field = frappe.ui.form.make_control({
        parent: filter_area,
        df: {
            fieldname: "for_date",
            fieldtype: "Date",
            label: "Business Date",
        },
        render_input: true,
    });

    // Table container
    let table_container = $('<div class="daily-sales-table mt-3">').appendTo(page.main);

    // Fetch and render data
    function fetch_and_render(for_date) {
        frappe.call({
            method: "my_app.api.get_daily_sales_summary",
            args: { for_date: for_date },
            callback: function (r) {
                table_container.empty();

                let data = r.message;
                if (!data || data.length === 0) {
                    table_container.html("<p>No data for this date</p>");
                    return;
                }

                // Build HTML table
                let table = $('<table class="table table-bordered">');
                table.append("<thead><tr><th>Measure</th><th>Value</th></tr></thead>");
                let tbody = $("<tbody>");
                data.forEach((row) => {
                    tbody.append(`<tr><td>${row.key}</td><td>${row.value}</td></tr>`);
                });
                table.append(tbody);
                table_container.append(table);
            },
        });
    }

    // On date change
    date_field.$input.on("change", () => {
        fetch_and_render(date_field.get_value());
    });

    // Initial load
    fetch_and_render(frappe.datetime.get_today());
};
