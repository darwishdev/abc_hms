import os
from typing import Dict, List
from click import Path
import frappe
from pathlib import Path
from utils.customfield_utils import install_custom_fields
from utils.role_utils import seed_app_roles
from utils.sql_utils import run_sql_dir

SQL_DIR_PROPERTY = Path(frappe.get_app_path("abc_hms", "property",  "sql"))
SQL_DIR_POS = Path(frappe.get_app_path("abc_hms", "pos",  "sql"))
SQL_DIR_CASHIER = Path(frappe.get_app_path("abc_hms", "cashier",  "sql"))
CUSTOMFIELDS_PATH = os.path.join(frappe.get_app_path("abc_hms"),  "setup", "customfields")

ROLES_CONFIG = {
    "Property Manager": {
        "desk_access": True,
        "perms": {
            "Reservation": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "amend": 1, "delete": 1},
            "Folio": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "amend": 1},
            "Folio Window": {"read": 1, "write": 1, "create": 1, "amend": 1},
            "POS Invoice": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "amend": 1},
            "POS Session": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
            "Customer": {"read": 1, "write": 1, "create": 1, "delete": 1},
            "Mode of Payment": {"read": 1, "write": 1, "create": 1, "delete": 1},
            "Rate Code": {"read": 1, "write": 1, "create": 1, "delete": 1},
            "Room Type": {"read": 1, "write": 1, "create": 1, "delete": 1},
            "Property": {"read": 1, "write": 1, "create": 1, "delete": 1},
            "Room": {"read": 1, "write": 1, "create": 1, "delete": 1},
            "Room Category": {"read": 1, "write": 1, "create": 1, "delete": 1},
            "Room": {"read": 1, "write": 1, "create": 1, "delete": 1},
            "Bed Type": {"read": 1, "write": 1, "create": 1, "delete": 1},
            "Amenity": {"read": 1, "write": 1, "create": 1, "delete": 1},
            "Payment Entry": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
            "Sales Invoice": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
            "Journal Entry": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
        },
    },
    "Front Desk": {
        "desk_access": True,
        "perms": {
            "Customer": {"read": 1, "create": 1},
            "Reservation": {"read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1, "amend": 1},
            "Folio": {"read": 1, "write": 1, "create": 1},
            "Folio Window": {"read": 1, "write": 1, "create": 1},
            "POS Invoice": {"read": 1, "write": 1, "create": 1, "submit": 1},
            "POS Session": {"read": 1, "write": 1, "create": 1, "submit": 1},
            "Payment Entry": {"read": 1, "create": 1},
            "Room": {"read": 1},
            "Room Type": {"read": 1},
            "Rate Code": {"read": 1},
            "Cancelation Policy": {"read": 1},
            "Property": {"read": 1},
            "Mode of Payment": {"read": 1},
        },
    },
    "House Keeping": {
        "desk_access": True,
        "perms": {
            "Room": {"read": 1, "write": 1},                 # update room status (clean/dirty/inspected)
            "Reservation": {"read": 1},                # see which rooms are occupied
            "Room Type": {"read": 1},                        # see room types
            "Room Category": {"read": 1},                    # see room categories
            "House Keeping Section": {"read": 1, "write": 1, "create": 1}, # manage housekeeping sections if you use that
            "Property": {"read": 1},                         # read-only property info
        },
    },
}
def after_install():
    return {"ok" : True}
# Optional: run this on every migrate so changes apply during development
def after_migrate():
    install_custom_fields(CUSTOMFIELDS_PATH)
    run_sql_dir(SQL_DIR_PROPERTY)
    run_sql_dir(SQL_DIR_POS)
    run_sql_dir(SQL_DIR_CASHIER)
    seed_app_roles(ROLES_CONFIG, domain="conchahotel.com")
    return {"ok" : True}

