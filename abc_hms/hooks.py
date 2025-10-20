app_name = "abc_hms"
app_title = "ABC HMS"
app_publisher = "DarwishDev"
app_description = "Hospitality Management System for ABC Hotels"
app_email = "support@darwishdev.com"
required_apps = ["frappe/erpnext"]
app_license = "mit"
after_install = "abc_hms.setup.installer.after_install"
after_migrate = "abc_hms.setup.installer.after_migrate"

override_doctype_class = {
    "POS Opening Entry": "abc_hms.overrides.pos_opening_entry.CustomPOSOpeningEntry",
    "Sales Invoice": "abc_hms.overrides.sales_invoice.CustomSalesInvoice",
    "POS Invoice": "abc_hms.overrides.pos_invoice.CustomPOSInvoice",
}

# override_whitelisted_methods = {
#     "frappe.model.workflow.apply_workflow": "abc_hms.overrides.workflow.apply_folio_workflow"
# }
boot_session = "abc_hms.boot.get_business_date"
app_include_css = ["/assets/abc_hms/css/nav-52.css"]
app_include_js = ["/assets/abc_hms/js/nav-9.js", "/assets/abc_hms/js/date_fields_2.js"]
fixtures = [
    {"doctype": "Company"},
    {"doctype": "Sales Partner Type"},
    {"doctype": "Reservation"},
    {"doctype": "Folio"},
    {"doctype": "Folio Window"},
    {"doctype": "Sales Partner"},
    {
        "dt": "Workspace Link",
        "filters": [["parent", "in", ["EOD", "Administration", "PMS"]]],
    },
    {
        "dt": "Workspace",
        "filters": [["name", "in", ["EOD", "Administration", "PMS"]]],
    },
    {"doctype": "Custom HTML Block"},
    {
        "doctype": "Item",
        "filters": [
            [
                "item_group",
                "in",
                [
                    "F&B",
                    "Rooms",
                ],
            ]
        ],
    },
    {
        "doctype": "Item Group",
        "filters": [
            [
                "name",
                "in",
                [
                    "F&B",
                    "Rooms",
                ],
            ]
        ],
    },
    {
        "doctype": "Custom HTML Block",
        "filters": [
            [
                "name",
                "in",
                [
                    "F&End Of Day",
                    "Rooms",
                ],
            ]
        ],
    },
    {"doctype": "Customer"},
    {"doctype": "Bed Type"},
    {"doctype": "Room Category"},
    {"doctype": "Room Type"},
    {"doctype": "Room"},
    {"doctype": "Mode of Payment"},
    {"doctype": "Rate Category"},
    {"doctype": "Rate Code"},
    {"doctype": "Rate Code Room Type"},
    {"doctype": "POS Profile"},
    {"doctype": "POS Profile User"},
    {"doctype": "Sales Taxes and Charges Template"},
    {"doctype": "Workflow State"},
    {"doctype": "Workflow Action Master"},
    {"doctype": "Workflow"},
    {"doctype": "Workflow"},
    {"doctype": "Cancelation Policy"},
    {"doctype": "Property"},
    {"doctype": "Property Setting"},
    {"doctype": "Item Group"},
    {"doctype": "Item"},
    {"doctype": "Restaurant"},
    {"doctype": "Restaurant Area"},
    {"doctype": "Restaurant Table"},
    {"doctype": "Amenity"},
    {
        "doctype": "Warehouse",
    },
    {
        "doctype": "Print Class",
    },
    {
        "doctype": "Cashier Printer",
    },
    {
        "doctype": "Cashier Device",
    },
    {
        "doctype": "Preparation Printer",
    },
    {
        "doctype": "Preparation Printer Print Class",
    },
    {
        "doctype": "Production Area",
    },
    {
        "doctype": "Production Area Preparation Printer",
    },
    {
        "doctype": "Casheir Device Production Area",
    },
]
