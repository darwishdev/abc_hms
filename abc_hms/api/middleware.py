import frappe
from frappe import _

def pos_request_interceptor():
    if frappe.request.path.startswith("/api/method/"):
        method_name = frappe.request.path.replace("/api/method/", "", 1)
        if method_name in frappe.guest_methods:
            return

    # Extract headers
    headers = frappe.local.request.headers
    business_date = headers.get("X-Business-Date")
    pos_profile = headers.get("X-Pos-Profile")

    if not business_date or not pos_profile:
        frappe.throw(_("Missing required headers: X-Business-Date or X-Pos-Profile"), frappe.AuthenticationError)

    # Validate against DB
    pos_doc = frappe.get_doc("POS Profile", pos_profile)

    if str(pos_doc.business_date) != str(business_date):
        # Logout user if mismatch
        frappe.local.login_manager.logout()
        frappe.throw(_("Invalid Business Date for POS Profile"), frappe.AuthenticationError)

    # Inject into frappe.local.context (custom)
    if not hasattr(frappe.local, "context"):
        frappe.local.context = {}

    frappe.local.context["business_date"] = business_date
    frappe.local.context["pos_profile"] = pos_profile

