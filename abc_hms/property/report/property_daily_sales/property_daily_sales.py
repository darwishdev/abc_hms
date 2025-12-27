import frappe

from utils.sql_utils import run_sql


def execute(filters=None):
    filters = filters or {}
    for_date = filters.get("for_date")

    if not for_date:
        frappe.throw("Please select a For Date to run this report.")

    # -----------------------------------------------
    # Stored Procedure Call Using run_sql() Pattern
    # -----------------------------------------------

    def procedure_call(cur, conn):
        # Important: clear any previous result sets
        # because MariaDB procedures return multiple result sets
        cur.execute("CALL get_property_daily_sales(%s)", (for_date,))

        # Fetch the first result set (the ONLY one that matters)
        result = cur.fetchall()

        # Consume remaining empty result sets safely
        while cur.nextset():
            cur.fetchall()

        return result

    # Execute the procedure through Frappe's DB wrapper
    rows = run_sql(procedure_call)

    if not rows:
        return [], []

    row = rows[0]

    # -----------------------------------------------
    # SAME LOGIC AS BEFORE FOR MEASURES
    # -----------------------------------------------

    measures = [
        {
            "label": "Total Gross",
            "daily": "daily_total_gross",
            "mtd": "mtd_total_gross",
            "ytd": "ytd_total_gross",
        },
        {
            "label": "Total Net",
            "daily": "daily_total_net",
            "mtd": "mtd_total_net",
            "ytd": "ytd_total_net",
        },
        {
            "label": "Total Tax",
            "daily": lambda r: (r.get("daily_service_charge_tax") or 0)
            + (r.get("daily_vat_tax") or 0),
            "mtd": lambda r: (r.get("mtd_service_charge_tax") or 0)
            + (r.get("mtd_vat_tax") or 0),
            "ytd": lambda r: (r.get("ytd_service_charge_tax") or 0)
            + (r.get("ytd_vat_tax") or 0),
        },
        {
            "label": "Service Charge Tax",
            "daily": "daily_service_charge_tax",
            "mtd": "mtd_service_charge_tax",
            "ytd": "ytd_service_charge_tax",
        },
        {
            "label": "VAT Tax",
            "daily": "daily_vat_tax",
            "mtd": "mtd_vat_tax",
            "ytd": "ytd_vat_tax",
        },
    ]

    data = []
    for measure in measures:
        daily_value = (
            measure["daily"](row)
            if callable(measure["daily"])
            else row.get(measure["daily"])
        )
        mtd_value = (
            measure["mtd"](row) if callable(measure["mtd"]) else row.get(measure["mtd"])
        )
        ytd_value = (
            measure["ytd"](row) if callable(measure["ytd"]) else row.get(measure["ytd"])
        )

        data.append(
            {
                "label": measure["label"],
                "date_value": daily_value or 0,
                "mtd_value": mtd_value or 0,
                "ytd_value": ytd_value or 0,
            }
        )

    columns = [
        {"fieldname": "label", "label": "Measure", "fieldtype": "Data", "width": 250},
        {
            "fieldname": "date_value",
            "label": "Date Value",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "fieldname": "mtd_value",
            "label": "MTD Value",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "fieldname": "ytd_value",
            "label": "YTD Value",
            "fieldtype": "Currency",
            "width": 150,
        },
    ]

    return columns, data
