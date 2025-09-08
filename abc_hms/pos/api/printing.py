# import frappe
# from typing import List, Optional
# from ..repo.printing_repo import CashierDevicePrintersMap
# from . import printing_uc
#
# @frappe.whitelist(allow_guest=True, methods=["GET"])
# def get_cashier_printers_map(cashier_device_name: Optional[str] = None) -> List[CashierDevicePrintersMap]:
#     return printing_uc.get_cashier_printers_cache(cashier_device_name)
