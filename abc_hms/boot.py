
import frappe

def get_business_date(bootinfo):
    property_setting = frappe.db.get_value(
        "Property Setting",
        {"property": frappe.defaults.get_user_default("property")},
        "business_date"
    )
    bootinfo.business_date = property_setting
