

import frappe
from abc_hms.container import app_container


@frappe.whitelist(methods=["POST"])
def room_type_rate_bulk_upsert(
            room_type,
            rate_code,
            rate,
            from_date,
            to_date,
):
    return app_container.rate_code_usecase.room_type_rate_bulk_upsert(
        room_type,
        rate_code,
        rate,
        from_date,
        to_date,
        True
    )


@frappe.whitelist(methods=["GET","POST"])
def rate_code_room_type_list(
            rate_code,
):
    return app_container.rate_code_usecase.rate_code_room_type_list(
        rate_code,
    )

@frappe.whitelist(methods=["POST"])
def room_type_rate_bulk_upsert_json(
        date_from,
        date_to,
        rate,
        items,
):
    return app_container.rate_code_usecase.room_type_rate_bulk_upsert_json(
        date_from,
        date_to,
        rate,
        items,
    )
