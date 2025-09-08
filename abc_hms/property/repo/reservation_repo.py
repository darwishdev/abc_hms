
from typing import Optional
import frappe
from pymysql import InternalError

class AuthRepo:
    def user_find_by_cashier_code(self, code: str , password: str) -> str:
        try:
            user_name = frappe.db.get_value("User", {"cashier_code": code, "cashier_password" : password,"enabled": 1}, "name")
            if not user_name:
                raise KeyError(f"User with Cashier Code {code} not found.")

            return f"{user_name}"
        except Exception as e:
            frappe.log_error(f"Error fetching active pos session: {str(e)}")
            raise InternalError(f"UNEXPECTED ERROR: {str(e)}")
