
import frappe
@frappe.whitelist(methods=["GET"])
def customer_list(pos_profile):
    data = frappe.db.sql("""
    select g.customer_group  ,
          JSON_ARRAYAGG(
          JSON_OBJECT(
                      'name',c.name,
                      'salutation',c.salutation,
                      'customer_type', c.customer_type,
                      'territory', territory
                  )
          ) customers

          FROM
          `tabPOS Customer Group` g
        left join tabCustomer c on c.customer_group = g.customer_group
        where parent = %s and parenttype = 'POS Profile'
        group by g.customer_group;
    """,(pos_profile or frappe.local.pos_profile) , as_dict=True)
    for row in data:
        if isinstance(row.get("customers"), str):
            try:
                row["customers"] = frappe.parse_json(row["customers"])
            except Exception:
                row["customers"] = []

    return data



@frappe.whitelist(methods=["POST","PUT"])
def customer_upsert(doc: dict):
    customer_name = doc.get("name")
    if customer_name and frappe.db.exists("Customer", customer_name):
        customer_doc= frappe.get_doc("Customer", customer_name) # type: ignore
    else:
        customer_doc= frappe.new_doc("Customer")  # type: ignore
    customer_doc.update(doc)
    customer_doc.save(ignore_permissions=True)
    frappe.db.commit()
    return doc

