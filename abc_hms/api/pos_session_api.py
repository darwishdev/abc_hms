import frappe
import json
from abc_hms.api.decorators import business_date_protected
from abc_hms.container import app_container
from abc_hms.dto.pos_session_dto import POSSessionFindForDateRequest, POSSessionDefaultsFindResponse, POSSessionFindForDateResponse, POSSessionUpsertRequest, POSSessionUpsertResponse
from abc_hms.pos.doctype.pos_session.pos_session import POSSession
from utils.date_utils import int_to_date

@frappe.whitelist()
def session_totals(session_id: str):
    if not session_id:
        frappe.throw(_("POS Session ID is required."))

    if not frappe.db.exists("POS Session", session_id):
        frappe.throw(_("POS Session {0} not found.").format(session_id))

    # Aggregate from POS Invoice
    totals = frappe.db.sql(
        """
        SELECT
            COUNT(name)                AS invoice_count,
            SUM(grand_total)           AS total_sales,
            SUM(paid_amount)           AS total_paid,
            SUM(grand_total - paid_amount) AS total_outstanding
        FROM `tabPOS Invoice`
        WHERE pos_session = %(session_id)s
    """,
        {"session_id": "POS-S-00003"},
        as_dict=True,
    )[0]

    # Default to 0 if None
    invoice_count = totals.invoice_count or 0
    total_sales = totals.total_sales or 0.0
    total_paid = totals.total_paid or 0.0
    total_outstanding = totals.total_outstanding or 0.0

    return {
        "success": True,
        "session_id": session_id,
        "invoice_count": invoice_count,
        "total_sales": total_sales,
        "total_paid": total_paid,
        "total_outstanding": total_outstanding,
    }
@frappe.whitelist()
def pos_session_invoice_list(session_id: str):
    if not session_id:
        frappe.throw(_("POS Session ID is required."))

    if not frappe.db.exists("POS Session", session_id):
        frappe.throw(_("POS Session {0} not found.").format(session_id))

    # ✅ Fetch invoices linked to this session
    invoices = frappe.get_all(
        "POS Invoice",
        filters={"pos_session": session_id},
        fields=[
            "name",
            "customer",
            "grand_total",
            "paid_amount",
            "status",
            "restaurant_table",
            "room_no",
            "posting_date",
            "creation",
        ],
        order_by="creation desc",
    )

    return {"success": True, "count": len(invoices), "orders": invoices}


@frappe.whitelist(methods=["GET"])
def pos_session_find_for_date()-> POSSessionFindForDateResponse:
    try:
        data = frappe.local.request.data
        payload: POSSessionFindForDateRequest = json.loads(data or "{}")
    except Exception as e:
        frappe.throw(f"Invalid JSON payload: {e}")
        return {"success" : False , "error" : f"{str(e)}"}

    result = app_container.pos_session_usecase.pos_session_find_for_date(payload.get("for_date") ,1)
    return result

@frappe.whitelist(methods=["POST" , "PUT"])
def pos_session_upsert()-> POSSession:
    try:
        data = frappe.local.request.data
        payload: POSSessionUpsertRequest = json.loads(data or "{}")
    except Exception as e:
        raise Exception(f"Invalid JSON payload: {e}")
    pos_profile =payload["doc"]["pos_profile"]
    # opening_entry = app_container.pos_opening_entry_usecase.pos_opening_entry_find_by_pos_profile(pos_profile,for_date)
    # if not opening_entry:
    #     app_container.pos_opening_entry_usecase.pos_opening_entry_upsert({
    #         "doc" : {
    #             "docstatus": 1,
    #             "user": frappe.session.user,
    #             "pos_profile": pos_profile,
    #             "period_start_date": f"{int_to_date(for_date)} 00:00:00",
    #             "balance_details": [{
    #                 "mode_of_payment": "Cash",
    #                 "opening_amount": 0,
    #             }],
    #         },
    #         "commit" : True
    #     })
    result = app_container.pos_session_usecase.pos_session_upsert(payload , True)
    return result


@frappe.whitelist(methods=["GET"])
def pos_session_find(pos_session: str):
    return app_container.pos_session_usecase.pos_session_find(pos_session)
@frappe.whitelist(methods=["GET"])
def pos_session_defaults_find(property_name: str) -> POSSessionDefaultsFindResponse:
    settings_resp = app_container.property_setting_usecase.property_setting_find(property_name)
    opening_entry:str = ""
    if settings_resp.get("success"):
        settings = settings_resp.get("doc")
        if settings:
            pos_profile = str(settings.get("default_pos_profile"))
            for_date = int(str(settings.get("business_date_int")))
            opening_entry = app_container.pos_opening_entry_usecase.pos_opening_entry_find_by_property(property_name)
            return {
                "success": True,
                "doc": {
                    "pos_profile": pos_profile,
                    "for_date": for_date,
                    "opening_entry": opening_entry,
                },
            }

    return {"success": True , "doc" : None}
