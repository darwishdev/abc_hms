// This goes in your dashboard's onload script or a separate JS file
frappe.dashboards["End Of Day"] = {
    onload: function (dashboard) {
        console.log("loaded");
        // Add custom buttons to the dashboard toolbar
        dashboard.page.add_action_item(
            __("View In House Report"),
            function () {
                frappe.set_route("query-report", "In House", {
                    property: frappe.boot.property || "CONA",
                    date_filter: frappe.datetime.now_date(),
                });
            },
            "octicon octicon-file-text",
        );

        dashboard.page.add_action_item(
            __("Export Dashboard"),
            function () {
                export_dashboard_data();
            },
            "octicon octicon-cloud-download",
        );

        dashboard.page.add_action_item(
            __("Refresh Data"),
            function () {
                dashboard.refresh();
            },
            "octicon octicon-sync",
        );

        // Add a primary button
        dashboard.page.add_primary_action(
            __("Quick Actions"),
            function () {
                show_quick_actions_dialog();
            },
            "octicon octicon-zap",
        );

        // Add menu items
        dashboard.page.add_menu_item(__("Night Audit"), function () {
            frappe.set_route("Form", "Night Audit", "new-night-audit-1");
        });

        dashboard.page.add_menu_item(__("Room Status"), function () {
            frappe.set_route("query-report", "Room Status Report");
        });

        // Custom CSS for better button styling
        $(`<style>
            .page-actions .btn {
                margin-left: 10px;
            }
            .dashboard-custom-section {
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        </style>`).appendTo("head");

        // Add custom section with buttons
        add_custom_dashboard_section(dashboard);
    },
};

function add_custom_dashboard_section(dashboard) {
    // Add a custom section to the dashboard
    const custom_section = $(`
        <div class="dashboard-custom-section">
            <div class="row">
                <div class="col-md-12">
                    <h5>Quick Actions</h5>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-primary" id="view-in-house">
                            <i class="fa fa-users"></i> View In House
                        </button>
                        <button type="button" class="btn btn-info" id="room-status">
                            <i class="fa fa-bed"></i> Room Status
                        </button>
                        <button type="button" class="btn btn-success" id="night-audit">
                            <i class="fa fa-clock-o"></i> Night Audit
                        </button>
                        <button type="button" class="btn btn-warning" id="export-reports">
                            <i class="fa fa-download"></i> Export Reports
                        </button>
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-md-6">
                    <div class="form-group">
                        <label>Property</label>
                        <select class="form-control" id="dashboard-property">
                            <option value="CONA">CONA</option>
                        </select>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="form-group">
                        <label>Business Date</label>
                        <input type="date" class="form-control" id="dashboard-date" value="${frappe.datetime.now_date()}">
                    </div>
                </div>
            </div>
        </div>
    `);

    // Insert after the dashboard header
    custom_section.insertAfter(dashboard.page.main.find(".page-head"));

    // Add event handlers
    $("#view-in-house").on("click", function () {
        const filters = get_dashboard_filters();
        frappe.set_route("query-report", "In House", filters);
    });

    $("#room-status").on("click", function () {
        const filters = get_dashboard_filters();
        frappe.set_route("query-report", "Room Status Report", filters);
    });

    $("#night-audit").on("click", function () {
        frappe.new_doc("Night Audit");
    });

    $("#export-reports").on("click", function () {
        show_export_dialog();
    });

    // Auto-refresh dashboard when filters change
    $("#dashboard-property, #dashboard-date").on("change", function () {
        const filters = get_dashboard_filters();
        // Update dashboard with new filters
        dashboard.refresh();
    });
}

function get_dashboard_filters() {
    return {
        property: $("#dashboard-property").val() || "CONA",
        date_filter: $("#dashboard-date").val() || frappe.datetime.now_date(),
    };
}

function export_dashboard_data() {
    const filters = get_dashboard_filters();

    frappe.call({
        method: "frappe.desk.query_report.export_query",
        args: {
            report_name: "In House",
            file_format_type: "Excel",
            filters: filters,
        },
        callback: function (r) {
            if (r.message) {
                window.open(r.message.file_url);
                frappe.show_alert({
                    message: __("Export completed successfully"),
                    indicator: "green",
                });
            }
        },
    });
}

function show_quick_actions_dialog() {
    const dialog = new frappe.ui.Dialog({
        title: __("Quick Actions"),
        fields: [
            {
                fieldtype: "HTML",
                fieldname: "actions_html",
                options: `
                    <div class="text-center">
                        <button class="btn btn-primary btn-lg btn-block mb-3" onclick="frappe.set_route('query-report', 'In House')">
                            <i class="fa fa-users"></i> View In House Guests
                        </button>
                        <button class="btn btn-info btn-lg btn-block mb-3" onclick="frappe.set_route('query-report', 'Arrivals')">
                            <i class="fa fa-plane"></i> Today's Arrivals
                        </button>
                        <button class="btn btn-warning btn-lg btn-block mb-3" onclick="frappe.set_route('query-report', 'Departures')">
                            <i class="fa fa-suitcase"></i> Today's Departures
                        </button>
                        <button class="btn btn-success btn-lg btn-block" onclick="frappe.new_doc('Night Audit')">
                            <i class="fa fa-clock-o"></i> Start Night Audit
                        </button>
                    </div>
                `,
            },
        ],
    });
    dialog.show();
}

function show_export_dialog() {
    const dialog = new frappe.ui.Dialog({
        title: __("Export Reports"),
        fields: [
            {
                fieldtype: "Select",
                fieldname: "report_type",
                label: __("Report Type"),
                options: ["In House", "Arrivals", "Departures", "Room Status Report"],
                reqd: 1,
            },
            {
                fieldtype: "Select",
                fieldname: "format",
                label: __("Format"),
                options: ["Excel", "CSV", "PDF"],
                default: "Excel",
                reqd: 1,
            },
        ],
        primary_action_label: __("Export"),
        primary_action: function (values) {
            const filters = get_dashboard_filters();

            frappe.call({
                method: "frappe.desk.query_report.export_query",
                args: {
                    report_name: values.report_type,
                    file_format_type: values.format,
                    filters: filters,
                },
                callback: function (r) {
                    if (r.message) {
                        window.open(r.message.file_url);
                        frappe.show_alert({
                            message: __("Export completed successfully"),
                            indicator: "green",
                        });
                        dialog.hide();
                    }
                },
            });
        },
    });
    dialog.show();
}
