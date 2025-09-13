app_name = "abc_hms"
app_title = "ABC HMS"
app_publisher = "DarwishDev"
app_description = "Hospitality Management System for ABC Hotels"
app_email = "support@darwishdev.com"
required_apps = ["frappe/erpnext" , "frappe/hrms"]
app_license = "mit"
after_install = "abc_hms.setup.installer.after_install"
after_migrate = "abc_hms.setup.installer.after_migrate"
before_request = []


boot_session = "abc_hms.boot.get_business_date"
app_include_css = [
    "/assets/abc_hms/css/index.css"
]
app_include_js = [
    "/assets/abc_hms/js/nav-04.js"
]
fixtures = [
    {"doctype": "Customer"},
    {"doctype": "Room Type"},
    {"doctype": "Cancelation Policy"},
    {"doctype": "Rate Code"},
    {"doctype": "Property"},
    {"doctype": "Room"},
    {"doctype": "Amenity"},
    {"doctype": "Room Category"},
    {"doctype": "Bed Type"},
    {"doctype": "POS Profile"},
    # -- pos
    	{
		"doctype": "POS Profile",
	},
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

