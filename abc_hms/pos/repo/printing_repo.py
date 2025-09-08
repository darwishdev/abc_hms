import frappe
from typing import  Dict, List, Optional, cast
from typing_extensions import TypedDict

class PrintClass(TypedDict):
    preparation_printer: str
    connection_info: str
    backup_printer: str
    backup_connection_info: str

class CashierDevicePrintersMap(TypedDict):
    cashier_device_name: str
    print_classes: Dict[str, PrintClass]

class PrintingRepository:
    def get_cashier_device_printers_map(self, cashier_device_name: Optional[str] = None) -> List[CashierDevicePrintersMap]:
        try:
            result = frappe.db.sql("""
                SELECT cashier_device_name, print_class print_classes
                FROM `cashier_device_printers_map`
                WHERE cashier_device_name = IFNULL(%s, cashier_device_name)
                ORDER BY cashier_device_name
            """, (cashier_device_name,), as_dict=True)

            return cast(List[CashierDevicePrintersMap], result or [])

        except Exception as e:
            frappe.log_error(f"Error fetching cashier device printers map: {str(e)}")
            raise
