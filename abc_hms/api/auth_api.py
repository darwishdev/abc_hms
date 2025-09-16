import frappe
from abc_hms.container import app_container

@frappe.whitelist(methods=["POST"] , allow_guest=True)
def cashier_login(cashier_code: int, cashier_password: str):
    return app_container.auth_usecase.cashier_login(cashier_code, cashier_password)
