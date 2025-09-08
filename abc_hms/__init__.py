from .cashier.api.folio import (
    folio_window_upsert,
    folio_list,
    folio_find,
)


from .api.reservation import (
    check_in,
    set_room_type_assigned,
    get_dashboard_data,
    get_night_audit_candidates,
    run_night_audit
)

from .property.api.inventory import (
    get_availability,
    get_availability_grid_detailed,
    apply_reservation_inventory_api,
    get_availability_raw_data,
    get_availability_grid_grouped,
    get_room_type_rates_grid,
    get_availability_grid_simple,
    reallocate_inventory_from_assignments,
    get_room_type_inventory_rates,
    seed_room_type_inventory_rate_codes,
)
# from .pos.api.printing import get_cashier_printers_map
from .api.auth import (
        cashier_login
)
from .pos.api.auth import (
    cashier_logout,
)

from .pos.api.item import (
    item_list,
)

from .pos.api.pos_invoice import (
    pos_invoice_upsert,
    pos_invoice_item_void,
    pos_invoice_item_bulk_upsert,
)

from .pos.api.pos_session import (
    session_open,
    currency_list,
    session_find_active,
    sessison_close,
    session_invoice_list,
)

import frappe

# re-export these functions
__all__ = [
    "cashier_login",
    "session_open",
]

# mark them as whitelisted

# auth
cashier_login = frappe.whitelist(allow_guest=True)(cashier_login)
# item
item_list = frappe.whitelist()(item_list)
# invoice
pos_invoice_upsert = frappe.whitelist()(pos_invoice_upsert)
pos_invoice_upsert = frappe.whitelist()(pos_invoice_item_void)
pos_invoice_item_bulk_upsert = frappe.whitelist()(pos_invoice_item_bulk_upsert)
# session
cashier_logout = frappe.whitelist()(cashier_logout)
session_open = frappe.whitelist()(session_open)
currency_list = frappe.whitelist()(currency_list)
session_find_active = frappe.whitelist()(session_find_active)
sessison_close = frappe.whitelist()(sessison_close)
session_invoice_list = frappe.whitelist()(session_invoice_list)
# printing
# get_cashier_printers_map = frappe.whitelist()(get_cashier_printers_map)
# inventory

get_availability = frappe.whitelist()(get_availability)
get_availability_grid_detailed = frappe.whitelist()(get_availability_grid_detailed)
apply_reservation_inventory_api = frappe.whitelist()(apply_reservation_inventory_api)
get_availability_raw_data = frappe.whitelist()(get_availability_raw_data)
get_availability_grid_grouped = frappe.whitelist()(get_availability_grid_grouped)
get_room_type_rates_grid = frappe.whitelist()(get_room_type_rates_grid)
get_availability_grid_simple = frappe.whitelist()(get_availability_grid_simple)
reallocate_inventory_from_assignments = frappe.whitelist()(reallocate_inventory_from_assignments)
get_room_type_inventory_rates = frappe.whitelist()(get_room_type_inventory_rates)
seed_room_type_inventory_rate_codes = frappe.whitelist()(seed_room_type_inventory_rate_codes)

# reservation

check_in = frappe.whitelist()(check_in)
set_room_type_assigned = frappe.whitelist()(set_room_type_assigned)
get_dashboard_data = frappe.whitelist()(get_dashboard_data)
get_night_audit_candidates = frappe.whitelist()(get_night_audit_candidates)
run_night_audit = frappe.whitelist()(run_night_audit)

# folio
folio_window_upsert = frappe.whitelist()(folio_window_upsert)
folio_list = frappe.whitelist()(folio_list)
folio_find = frappe.whitelist()(folio_find)
