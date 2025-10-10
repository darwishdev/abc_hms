from typing import List, Callable, Optional
import frappe
from functools import wraps
from frappe import _


def _deny(status: int, msg: str):
    """Properly set response status and throw PermissionError"""
    frappe.local.response = getattr(frappe.local, "response", {}) or {}
    frappe.local.response["http_status_code"] = status
    frappe.local.response["message"] = msg
    raise frappe.PermissionError(_(msg))


def business_date_protected(_fn: Optional[Callable] = None, *, allow_empty_date: bool = False):
    """
    Ensure that X-Business-Date and X-Pos-Profile headers are passed and valid.
    Usage:
        @business_date_protected
        def my_api(): ...

        or

        @business_date_protected(allow_empty_date=True)
        def my_api(): ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            headers = frappe.local.request.headers
            business_date = headers.get("X-Business-Date")
            pos_profile = headers.get("X-Pos-Profile")
            pos_session = headers.get("X-Pos-Session")

            if not pos_profile:
                _deny(403, "Missing X-Pos-Profile header.")

            if not allow_empty_date and not business_date:
                _deny(403, "Missing X-Business-Date header.")

            # Validate POS Profile
            if pos_session and len(pos_session) > 0:
                if not frappe.db.exists("POS Session", pos_session):
                    _deny(403, "Invalid POS Session.")
            if not frappe.db.exists("POS Profile", pos_profile):
                _deny(403, "Invalid POS Profile.")

            if not allow_empty_date:
                real_business_date: List[str] = frappe.db.sql(
                    """
                    SELECT date_to_int(s.business_date)
                    FROM `tabProperty Setting` s
                    JOIN `tabPOS Profile` p on s.name = p.property and p.name = %s
                    """,
                    pos_profile,
                    pluck=True  # returns list of first column values
                ) # type: ignore

                if not real_business_date or len(real_business_date) == 0:
                    _deny(403, "Business Date Not Set For Property.")

                if str(real_business_date[0]) != str(business_date):
                    frappe.local.login_manager.logout()
                    _deny(403, f"Business Date does not match POS Profile. Current Business Date is {str(real_business_date[0])}")

            # Inject into frappe.local
            frappe.local.business_date = business_date
            frappe.local.pos_profile = pos_profile
            frappe.local.pos_session = pos_session

            return fn(*args, **kwargs)

        return wrapper

    # Support both @business_date_protected and @business_date_protected(...)
    if callable(_fn):
        return decorator(_fn)
    return decorator
