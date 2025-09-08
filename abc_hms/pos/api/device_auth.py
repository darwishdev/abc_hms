import frappe
from functools import wraps
from frappe import _

def _deny(status: int, msg: str):
    frappe.local.response = getattr(frappe.local, "response", {}) or {}
    frappe.local.response["http_status_code"] = status
    raise PermissionError(_(msg))

def device_protected(fn):
    """
    Ensure that X-Device-Id is passed in headers.
    Usage:
        @frappe.whitelist()
        @device_protected
        def my_api(): ...
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # fetch from request headers
        device_id = frappe.get_request_header("X-Device-Id")
        # inject device_id into kwargs for handler if needed
        if not device_id:
            _deny(403, "Missing X-Device-Id header.")

        if not frappe.db.exists("Cashier Device", {"name": device_id, "enabled": 1}):
            _deny(403, "Unauthorized or disabled device.")

        # Only store the device name
        frappe.local.device = device_id
        return fn(*args, **kwargs)

    return wrapper
