
import frappe
from frappe import _
from ..repo.pos_session_repo import PosSessionRepository



@frappe.whitelist()
def currency_list2(doctype, txt, searchfield, start, page_len, filters):
    currencies = frappe.db.sql("""
        SELECT 'EGP' as name , 1 as exchange_rate
        UNION
        SELECT DISTINCT c.name , e.exchange_rate
        FROM `tabCurrency` c
        JOIN `tabCurrency Exchange` e
            ON e.from_currency = c.name
        WHERE c.name LIKE %(txt)s
        ORDER BY name
        LIMIT %(start)s, %(page_len)s
    """, {
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    }, as_dict=True)

    # Return tuples (value, label) for Link field dropdown
    return [(c["name"], c["name"]) for c in currencies]
@frappe.whitelist()
def currency_list():
    currencies =  frappe.db.sql("""
        SELECT 'EGP' as name , 1 as exchange_rate
        UNION
         SELECT DISTINCT c.name , e.exchange_rate
        FROM `tabCurrency` c
        JOIN `tabCurrency Exchange` e
            ON e.from_currency = c.name
    """  , as_dict=True)
    return  currencies

@frappe.whitelist()
def session_find_active():
    repo = PosSessionRepository()
    filters = {
        "session_status": "Open",
        "created_by": frappe.session.user,
    }

    session = repo.session_find_active(filters)
    if not session:
        return None
    return session


@frappe.whitelist(allow_guest=False)
def session_open(pos_profile, company=None, opening_cash=0.0):
    user = frappe.session.user
    company = company or frappe.defaults.get_user_default("Company")

    # Check if already open session for user/profile
    if frappe.db.exists(
        "POS Session",
        {"created_by": user, "pos_profile": pos_profile, "session_status": "Open"},
    ):
        frappe.throw(
            _("There is already an open session for this user and POS Profile")
        )

    # ✅ Required fields
    today = frappe.utils.nowdate()

    # ✅ Create POS Opening Entry
    opening_entry = frappe.new_doc("POS Opening Entry")
    opening_entry.user = user
    opening_entry.pos_profile = pos_profile
    opening_entry.company = company
    opening_entry.opening_amount = opening_cash
    opening_entry.posting_date = today
    opening_entry.period_start_date = today

    # Add opening balance details (required)
    opening_entry.append(
        "balance_details",
        {
            "mode_of_payment": "Cash",  # or get from pos_profile default
            "amount": opening_cash,
        },
    )

    opening_entry.insert()
    opening_entry.submit()

    # ✅ Create POS Session
    session = frappe.new_doc("POS Session")
    session.created_by = user
    session.pos_profile = pos_profile
    session.opening_entry = opening_entry.name
    session.session_status = "Open"
    session.insert()

    return {
        "success": True,
        "session": session.name,
        "opening_entry": opening_entry.name,
    }


@frappe.whitelist(allow_guest=False)
def sessison_close(session_name, closing_cash=0.0):
    session = frappe.get_doc("POS Session", session_name)

    if session.session_status != "Open":
        frappe.throw(_("Session is not open."))

    # Create POS Closing Entry
    closing_entry = frappe.new_doc("POS Closing Entry")
    closing_entry.pos_opening_entry = session.opening_entry
    closing_entry.user = session.created_by
    closing_entry.pos_profile = session.pos_profile
    closing_entry.company = frappe.defaults.get_user_default("Company")
    closing_entry.closing_amount = closing_cash
    closing_entry.posting_date = frappe.utils.nowdate()
    closing_entry.insert()
    closing_entry.submit()

    # Mark session as closed
    session.closing_entry = closing_entry.name
    session.session_status = "Closed"
    session.save()

    return {
        "success": True,
        "session": session.name,
        "closing_entry": closing_entry.name,
    }


@frappe.whitelist()
def session_invoice_list(session_id: str):
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
            "table_number",
            "room_number",
            "posting_date",
            "creation",
        ],
        order_by="creation desc",
    )

    return {"success": True, "count": len(invoices), "orders": invoices}


