
from typing import Optional
import frappe
from pymysql import InternalError

class AuthRepo:
    def user_find_pos_profiles(self, user_name: str):
        return  frappe.db.sql("""
                                select distinct
                                  pu.parent profile,
                                  pu.user,
                                  p.restaurant,
                                  pu.default,
                                  p.property,
                                  p.allow_partial_payment,
                                  p.customer default_customer,
                                  ps.name pos_session,
                                  s.default_pos_profile default_room_profile,
                                  s.business_date,
                                  date_to_int(s.business_date) business_date_int,
                                  p.allow_rate_change
                                  from tabUser u
                                  LEFT JOIN  `tabPOS Profile User` pu  on u.name = pu.user
                                  LEFT JOIN  `tabPOS Profile` p  on pu.parent = p.name
                                  LEFT JOIN  `tabProperty Setting` s  on p.property = s.name
                                  LEFT JOIN `tabPOS Session` ps on ps.for_date =
                                  date_to_int(s.business_date) and ps.pos_profile  = p.name and
                                  ps.owner = pu.user and ps.docstatus = 0
                                  WHERE u.name  = %s;
                              """ , (user_name,), as_dict=True)

    def user_find_by_cashier_code(self, code: str , password: str) -> str:
        user_name = frappe.db.get_value("User", {"cashier_code": code, "cashier_password" : password,"enabled": 1}, "name")
        if not user_name:
            raise KeyError(f"User with Cashier Code {code} not found.")

        return user_name
