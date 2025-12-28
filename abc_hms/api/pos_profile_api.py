from dataclasses import asdict
import json
import frappe
from abc_hms.api.decorators import business_date_protected
from abc_hms.container import app_container
from utils.sql_utils import run_sql


@frappe.whitelist(methods=["GET"])
def profile_item_list():
    args = frappe.form_dict
    if not args.get("pos_profile"):
        raise frappe.ValidationError("profile is required")

    query = """
WITH items AS (
    SELECT
        ig.name            AS item_group,
        i.item_code,
        i.name,
        i.print_class,
        coalesce(MAX(price.price_list_rate) , 0.0) item_price,
        COALESCE(
            JSON_ARRAYAGG(
                CASE
                    WHEN modifier.name IS NOT NULL THEN
                        JSON_OBJECT(
                            'name', modifier.name,
                            'item_code', modifier.item_code,
                            'print_class', i.print_class,
                            'item_price', coalesce(modprice.price_list_rate , 0.0)
                        )
                END
            ),
            JSON_ARRAY()
        ) AS modifiers

    FROM `tabItem` i
    JOIN `tabItem Group` ig
        ON i.item_group = ig.name
  LEFT JOIN `tabItem Price` price
        ON price.item_code = i.item_code and price.price_list = 'Standard Selling'

    LEFT JOIN `tabItem` modifier
        ON modifier.variant_of = i.name
   LEFT JOIN `tabItem Price` modprice
        ON modprice.item_code = modifier.item_code and modprice.price_list = 'Standard Selling'
    WHERE i.variant_of IS NULL

    GROUP BY
        ig.name,
        i.item_code,
        i.name,
        price.price_list_rate,
  i.print_class
) SELECT
    ig.name AS group_name,
        JSON_ARRAY() children ,
        0 level ,
        null parent,
    JSON_ARRAYAGG(
        JSON_OBJECT(
            'item_code', i.item_code,
            'name', i.name,
            'item_price', i.item_price,
            'print_class', i.print_class,
            'modifiers', i.modifiers

        )
    ) AS items

FROM `tabItem Group` ig
JOIN items i
    ON ig.name = i.item_group

GROUP BY ig.name;
        """

    rows = frappe.db.sql(query, as_dict=True)

    # 🔥 Parse JSON fields
    for row in rows:
        if row.get("items"):
            row["items"] = json.loads(row["items"])
        else:
            row["items"] = []
    for row in rows:
        if row.get("children"):
            row["children"] = json.loads(row["children"])
        else:
            row["children"] = []

    return [{"group_name": "F&B", "children": rows}]


@frappe.whitelist(methods=["GET"])
@business_date_protected(allow_empty_date=True)
def porfile_mode_of_payment_list():
    result = app_container.pos_profile_usecase.profile_mode_of_payment_list(
        frappe.local.pos_profile
    )
    return result
