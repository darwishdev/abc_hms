import frappe
import pymysql.cursors
import pymysql.cursors
from frappe import _
from frappe.utils import nowdate
from frappe.utils import today
from frappe.utils import today, getdate, add_days

from frappe import render_template
from frappe.utils import now_datetime, format_datetime
import os
from utils.date_utils import date_to_int


@frappe.whitelist()
def reservation_availability_check(
        property: str,
        arrival : str | int,
        departure : str | int ,
        room_categories : str | None =None,
        room_types : str | None =None,
        rate_code : str | None =None,
):
    conn = frappe.db.get_connection()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    # --- Step 1: Availability ---
    cur.execute(
        """
        CALL inventory_availability_check(%s, %s, %s, %s, %s)
        """,
        (property, date_to_int(arrival), date_to_int(departure), room_types, room_categories),
    )

    availability = cur.fetchall()

    # --- Early return if nothing available ---
    if not availability:
        cur.close()
        return {"availability": [], "rates": []}

    # --- Step 2: Extract room types ---
    room_type_list = ",".join([row["room_type"] for row in availability])

    # --- Step 3: Rates ---
    cur.execute(
        """
        CALL room_type_rate_list(%s, %s, %s)
        """,
        (date_to_int(arrival), date_to_int(departure), room_type_list),
    )
    rates = cur.fetchall()

    cur.close()

    return {
        "availability": availability,
        "rates": rates,
    }

@frappe.whitelist()
def render_hello_world_from_file(message="Hello World!", **kwargs):
    """
    Load HTML template from file and render it
    """
    try:
        # Get the absolute path to template file
        app_path = frappe.get_app_path('abc_hms')
        template_file_path = os.path.join(app_path,  'templates', 'includes' , 'hello_world.html')

        # Check if file exists
        if not os.path.exists(template_file_path):
            return f"❌ Template file not found at: {template_file_path}"

        # Read the template file
        with open(template_file_path, 'r', encoding='utf-8') as file:
            template_content = file.read()

        # Prepare context
        context = {
            'message': message,
            'title': kwargs.get('title', 'Hello World'),
            'user': frappe.session.user,
            'current_time': format_datetime(now_datetime()),
            'doc_type': kwargs.get('doc_type'),
            'doc_name': kwargs.get('doc_name'),
            'app_name': 'ABC HMS'
        }


        # Render template with context
        rendered_html = render_template(template_content, context)

        return {
            'success': True,
            'html': rendered_html,
            'template_path': template_file_path
        }

    except Exception as e:
        frappe.log_error(f"Template loading error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'html': f"<div style='color: red; padding: 20px;'>Error loading template: {str(e)}</div>"
        }

def get_doc_status(doc):
    """Get document status"""
    if doc.docstatus == 0:
        return 'Draft'
    elif doc.docstatus == 1:
        return 'Submitted'
    elif doc.docstatus == 2:
        return 'Cancelled'
    return 'Unknown'
