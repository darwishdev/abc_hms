import frappe
from abc_hms.container import container

@frappe.whitelist(methods=["POST"] , allow_guest=True)
def cashier_login(cashier_code: int, cashier_password: str):
    return container.auth_usecase.cashier_login(cashier_code, cashier_password)
