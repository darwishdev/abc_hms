import frappe
from typing import List, Optional
from ..repo.printing_repo import PrintingRepository, CashierDevicePrintersMap


class PrintingUsecase:
    def __init__(self, repo: PrintingRepository) -> None:
        self.repo = repo

    def get_cashier_printers_cache(
        self, cashier_device_name: Optional[str] = None
    ) -> List[CashierDevicePrintersMap]:
        if cashier_device_name and not self._validate_cashier_device(cashier_device_name):
            return []
        return self.repo.get_cashier_device_printers_map(cashier_device_name)

    def _validate_cashier_device(self, cashier_device_name: str) -> bool:
        return bool(frappe.db.exists("Cashier Device", cashier_device_name))
