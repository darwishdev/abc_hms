import frappe
from frappe import _
from frappe.utils.password import check_password
from frappe.core.doctype.user.user import generate_keys
from frappe.utils.password import get_decrypted_password
from frappe.sessions import Session
from frappe.utils import random_string, now_datetime

def cashier_login(cashier_code, cashier_password):
    try:
        user_name = ""
        if not user_name:
            frappe.throw(_("User Not Found"))
        user_doc = frappe.get_doc("User", user_name)

        api_key = user_doc.api_key
        api_secret = None

        if api_key:
            try:
                api_secret = get_decrypted_password("User", user_name, "api_secret")
            except:
                api_secret = None

        if not api_key or not api_secret:
            api_key = frappe.generate_hash(length=15)
            api_secret = frappe.generate_hash(length=15)
            user_doc.api_key = api_key
            user_doc.api_secret = api_secret
            user_doc.save(ignore_permissions=True)
            frappe.db.commit()

        # 5. Create authorization token
        token_value = f"{api_key}:{api_secret}"


        return {
            "success": True,
            "authorization": token_value,
            "token_type": "token",
            "user": user_name,
            "full_name": user_doc.full_name,
            "message": "Login successful"
        }

    except Exception as e:
        # Log the error for debugging
        frappe.log_error(f"Cashier login failed: {str(e)}", "Cashier Login Error")

        # Return proper error response
        frappe.local.response["http_status_code"] = 401
        return {
            "success": False,
            "message": str(e),
            "timestamp": now_datetime(),
        }

def cashier_logout():
    """Logout current user and destroy session"""
    if frappe.session.user == "Guest":
        return {"success": True, "message": _("Already logged out")}

    try:
        # Destroy the session
        frappe.local.login_manager.logout()

        # Clear cookies
        frappe.local.cookie_manager.delete_cookie("sid")
        frappe.local.cookie_manager.delete_cookie("csrf_token")

        return {
            "success": True,
            "message": _("Logout successful"),
            "timestamp": now_datetime(),
        }
    except Exception as e:
        frappe.log_error(f"Cashier logout failed: {str(e)}", "Cashier Logout Error")
        return {
            "success": False,
            "message": str(e),
            "timestamp": now_datetime(),
        }
