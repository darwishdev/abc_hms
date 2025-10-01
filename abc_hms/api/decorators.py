import json
import frappe
from functools import wraps
from frappe import _

def _deny(status: int, msg: str):
    frappe.local.response = getattr(frappe.local, "response", {}) or {}
    frappe.local.response["http_status_code"] = status
    raise PermissionError(_(msg))


def business_date_protected(fn):
    """
    Ensure that X-Business-Date and X-Pos-Profile headers are passed and valid.
    Usage:
        @frappe.whitelist()
        @business_date_protected
        def my_api(): ...
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        headers = frappe.local.request.headers
        business_date = headers.get("X-Business-Date")
        pos_profile = headers.get("X-Pos-Profile")

        if not business_date or not pos_profile:
            _deny(403, "Missing X-Business-Date or X-Pos-Profile headers.")

        # Validate POS Profile
        if not frappe.db.exists("POS Profile", pos_profile):
            _deny(403, "Invalid POS Profile.")

        real_business_date = frappe.db.sql("""
            SELECT date_to_int(s.business_date)
            FROM `tabProperty Setting` s
            JOIN `tabPOS Profile` p on s.name = p.property and p.name = %s
        """ , pos_profile , pluck=['business_date'])
        if not real_business_date or len(real_business_date) == 0:
            _deny(403, f"Business Date Not Set For Property ")
        if str(real_business_date[0]) != str(business_date):
            frappe.local.login_manager.logout()
            _deny(403, f"Business Date does not match POS Profile Current Business Date Is : {str(real_business_date[0])}")

        # Inject into frappe.local for later use
        frappe.local.business_date = business_date
        frappe.local.pos_profile = pos_profile

        return fn(*args, **kwargs)

    return wrapper
