frappe.pages["property-daily-sales"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Property Daily Sales",
        single_column: true,
    });

    $(page.body).html(`
		<div id="daily-sales-filters" class="form-section" style="margin-bottom: 20px;"></div>
		<div id="summary-cards" style="margin-bottom: 20px;"></div>
		<div id="invoice-table"></div>
	`);

    // Add page actions
    page.set_primary_action("Refresh", () => {
        reload_invoice_table(filter_controls);
    });

    page.add_menu_item("Export to Excel", () => {
        if (window.invoiceDataTable) {
            window.invoiceDataTable.exportToExcel();
        }
    });

    // Initialize filters and load data
    initialize_page(page);
};

const initialize_page = (page) => {
    const filters_df = [
        {
            label: "Date",
            fieldtype: "Date",
            fieldname: "for_date",
            reqd: 1,
            default: frappe.datetime.get_today(),
        },
        {
            label: "Customer",
            fieldtype: "Link",
            options: "Customer",
            fieldname: "customer",
        },
        {
            label: "Tax Status",
            fieldtype: "Select",
            options: "\nCorrect\nIssues",
            fieldname: "tax_status",
        },
    ];

    const filter_controls = generate_filters(filters_df, $("#daily-sales-filters"));

    // Add change events to filters
    Object.values(filter_controls).forEach((control) => {
        control.df.onchange = () => {
            reload_invoice_table(filter_controls);
            reload_summary_cards(filter_controls);
        };
    });

    // Load initial data
    reload_summary_cards(filter_controls);
    reload_invoice_table(filter_controls);
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

const reload_summary_cards = (filter_controls) => {
    const filters = {};
    Object.keys(filter_controls).forEach((k) => {
        filters[k] = filter_controls[k].get_value();
    });

    if (!filters.for_date) {
        $("#summary-cards").html(
            "<div class='text-muted'>Please select a date to view summary</div>",
        );
        return;
    }

    fetch_daily_summary(filters, (data) => {
        render_summary_cards(data);
    });
};

const reload_invoice_table = (filter_controls) => {
    const filters = {};
    Object.keys(filter_controls).forEach((k) => {
        filters[k] = filter_controls[k].get_value();
    });

    if (!filters.for_date) {
        $("#invoice-table").html(
            "<div class='text-muted'>Please select a date to view invoices</div>",
        );
        return;
    }

    fetch_invoices(filters, (data) => {
        render_invoice_table(data);
    });
};

const fetch_daily_summary = (filters, callback) => {
    frappe.call({
        method: "abc_hms.api.property_api.get_daily_summary",
        args: { filters },
        callback: function (r) {
            if (r.message) {
                callback(r.message);
            } else {
                callback(null);
            }
        },
    });
};

const fetch_invoices = (filters, callback) => {
    frappe.call({
        method: "abc_hms.api.property_api.get_invoice_data",
        args: { filters },
        callback: function (r) {
            if (r.message) {
                callback(r.message);
            } else {
                callback([]);
            }
        },
    });
};

const render_summary_cards = (data) => {
    if (!data) {
        $("#summary-cards").html("<div class='text-muted'>No data found for selected date</div>");
        return;
    }

    const cards_html = `
		<div class="row">
			<div class="col-sm-3">
				<div class="card">
					<div class="card-body text-center">
						<h6 class="text-muted">Total Gross</h6>
						<h3>${data.daily_total_gross || 0}</h3>
						<p class="text-muted small">MTD: ${data.mtd_total_gross || 0}</p>
					</div>
				</div>
			</div>
			<div class="col-sm-3">
				<div class="card">
					<div class="card-body text-center">
						<h6 class="text-muted">Total Net</h6>
						<h3>${data.daily_total_net || 0}</h3>
						<p class="text-muted small">MTD: ${data.mtd_total_net || 0}</p>
					</div>
				</div>
			</div>
			<div class="col-sm-3">
				<div class="card">
					<div class="card-body text-center">
						<h6 class="text-muted">Total Tax</h6>
						<h3>${data.daily_total_tax || 0}</h3>
						<p class="text-muted small">MTD: ${data.mtd_total_tax || 0}</p>
					</div>
				</div>
			</div>
			<div class="col-sm-3">
				<div class="card">
					<div class="card-body text-center">
						<h6 class="text-muted">Invoices</h6>
						<h3>${data.invoice_count || 0}</h3>
						<p class="text-muted small">Issues: ${data.issue_count || 0}</p>
					</div>
				</div>
			</div>
		</div>
		<div class="row" style="margin-top: 15px;">
			<div class="col-sm-6">
				<div class="card">
					<div class="card-body text-center">
						<h6 class="text-muted">Service Charge Tax</h6>
						<h3>${data.daily_service_charge_tax || 0}</h3>
						<div class="row">
							<div class="col-6">
								<p class="text-muted small">MTD: ${data.mtd_service_charge_tax || 0}</p>
							</div>
							<div class="col-6">
								<p class="text-muted small">YTD: ${data.ytd_service_charge_tax || 0}</p>
							</div>
						</div>
					</div>
				</div>
			</div>
			<div class="col-sm-6">
				<div class="card">
					<div class="card-body text-center">
						<h6 class="text-muted">VAT Tax</h6>
						<h3>${data.daily_vat_tax || 0}</h3>
						<div class="row">
							<div class="col-6">
								<p class="text-muted small">MTD: ${data.mtd_vat_tax || 0}</p>
							</div>
							<div class="col-6">
								<p class="text-muted small">YTD: ${data.ytd_vat_tax || 0}</p>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	`;

    $("#summary-cards").html(cards_html);
};

const render_invoice_table = (data) => {
    if (window.invoiceDataTable) {
        window.invoiceDataTable.destroy();
        window.invoiceDataTable = null;
    }

    if (!data.length) {
        $("#invoice-table").html(
            "<div class='text-muted'>No invoices found for the selected criteria</div>",
        );
        return;
    }

    const columns = [
        {
            id: "invoice_name",
            name: "Invoice",
            width: 180,
            format: (value) => {
                return `<a href="/app/sales-invoice/${value}">${value}</a>`;
            },
        },
        {
            id: "customer",
            name: "Customer",
            width: 150,
        },
        {
            id: "total_net",
            name: "Net Amount",
            width: 120,
        },
        {
            id: "total_gross",
            name: "Gross Amount",
            width: 120,
        },
        {
            id: "total_tax",
            name: "Total Tax",
            width: 120,
        },
        {
            id: "tax_difference",
            name: "Tax Difference",
            width: 120,
            format: (value) => {
                const color = value < 0 ? "red" : value > 0 ? "orange" : "green";
                return `<span style="color: ${color}">${value}</span>`;
            },
        },
        {
            id: "pi_total_difference",
            name: "PI Difference",
            width: 120,
            format: (value) => {
                const color = value < 0 ? "red" : value > 0 ? "orange" : "green";
                return `<span style="color: ${color}">${value}</span>`;
            },
        },
        {
            id: "pi_count",
            name: "PI Count",
            width: 80,
        },
        {
            id: "status",
            name: "Status",
            width: 100,
            format: (value) => {
                const color = value === "Correct" ? "green" : "red";
                return `<span style="color: ${color}">${value}</span>`;
            },
        },
    ];

    const datatable = new DataTable("#invoice-table", {
        columns: columns,
        data: data,
        layout: "fluid",
        inlineFilters: true,
        serialNoColumn: true,
        noDataMessage: "No invoices found",
    });

    // Store for export functionality
    window.invoiceDataTable = datatable;
};
