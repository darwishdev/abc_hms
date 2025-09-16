app_name = "abc_hms"
app_title = "ABC HMS"
app_publisher = "DarwishDev"
app_description = "Hospitality Management System for ABC Hotels"
app_email = "support@darwishdev.com"
required_apps = ["frappe/erpnext" , "frappe/hrms"]
app_license = "mit"
after_install = "abc_hms.setup.installer.after_install"
after_migrate = "abc_hms.setup.installer.after_migrate"


boot_session = "abc_hms.boot.get_business_date"
app_include_css = [
    "/assets/abc_hms/css/index.css"
]
app_include_js = [
    "/assets/abc_hms/js/nav-05.js"
]
fixtures = [

    {"doctype": "Company"},
    {
        "doctype": "Account" ,
        "filters": [
            ["name", "in", [
                "1310 - City Ledger - CH",
                "1320 - Guest Ledger - CH",
                "1330 - Visa - CH",
                "4120 - Room Revenue - CH",
                "4130 - F&B Revenue - CH",
                "2310 - Service Charge - CH",
                "2320 - Municipality - CH",
                "2330 - VAT - CH"
            ]]
        ]},
    {"doctype": "Customer"},
    {"doctype": "Bed Type"},
    {"doctype": "Room Category"},
    {"doctype": "Room Type"},
    {"doctype": "Room"},
    {"doctype": "Mode of Payment"},

    {"doctype": "Rate Category"},
    {"doctype": "Rate Code"},
    {"doctype": "POS Profile"},
    {"doctype": "Sales Taxes and Charges Template"},
    {"doctype": "Workflow State"},
    {"doctype": "Workflow Action"},
    {"doctype": "Workflow"},
    {"doctype": "Workflow"},
    {"doctype": "Cancelation Policy"},
    {"doctype": "Property"},
    {"doctype": "Property Setting"},
    {"doctype": "Item Group"},
    {"doctype": "Item"},
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

