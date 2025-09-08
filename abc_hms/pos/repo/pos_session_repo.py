import frappe
from typing import  Dict


class PosSessionRepository:
    def session_find_active(self, filters: Dict):
        try:
            session = frappe.get_all(
                "POS Session",
                filters=filters,
                fields=["name", "pos_profile", "session_status", "opening_entry", "closing_entry"],
                limit=1,
                order_by="creation desc"
            )
            if not session:
                return None
            return session[0]
        except Exception as e:
            frappe.log_error(f"Error fetching active pos session: {str(e)}")
            raise
