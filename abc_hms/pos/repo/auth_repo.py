
from typing import Optional
import frappe
from pymysql import InternalError

class AuthRepo:
    def user_find_pos_profiles(self, user_name: str) -> str:
        return  frappe.db.sql("  select  group_concat(parent) profiles  , pu.user  from tabUser u LEFT JOIN  `tabPOS Profile User` pu  on u.name = pu.user group by user")
    def user_find_by_cashier_code(self, code: str , password: str) -> str:
        user_name = frappe.db.get_value("User", {"cashier_code": code, "cashier_password" : password,"enabled": 1}, "name")
        if not user_name:
            raise KeyError(f"User with Cashier Code {code} not found.")

        return user_name
