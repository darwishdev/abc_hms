import frappe

def set_business_date():
    property_name = frappe.defaults.get_user_default("property")
    if not property_name:
        return

    business_date = frappe.db.get_value(
        "Property Setting",
        {"property": property_name},
        "business_date"
    )
    frappe.local.business_date = business_date
