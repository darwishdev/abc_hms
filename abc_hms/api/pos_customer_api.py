import frappe


@frappe.whitelist(methods=["GET"])
def customer_list(pos_profile):
    data = frappe.db.sql(
        """
        WITH customer_addresses AS (
            SELECT
                c.name AS customer_name,

                COALESCE(
                    JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'name', a.name,
                            'address_title', a.address_title,
                            'address_type', a.address_type,
                            'address_line1', a.address_line1,
                            'address_line2', a.address_line2,
                            'city', a.city,
                            'state', a.state,
                            'country', a.country,
                            'pincode', a.pincode,
                            'phone', a.phone,
                            'email_id', a.email_id,
                            'is_primary_address', a.is_primary_address,
                            'is_shipping_address', a.is_shipping_address
                        )
                    ),
                    JSON_ARRAY()
                ) AS addresses

            FROM `tabCustomer` c
            LEFT JOIN `tabDynamic Link` dl
                ON dl.link_doctype = 'Customer'
                AND dl.link_name = c.name
            LEFT JOIN `tabAddress` a
                ON a.name = dl.parent
                AND dl.parenttype = 'Address'

            GROUP BY c.name
        )

        SELECT
            g.customer_group,

            JSON_ARRAYAGG(
                JSON_OBJECT(
                    'name', c.name,
                    'salutation', c.salutation,
                    'customer_type', c.customer_type,
                    'territory', c.territory,
                    'addresses', COALESCE(ca.addresses, JSON_ARRAY())
                )
            ) AS customers

        FROM `tabPOS Customer Group` g
        LEFT JOIN `tabCustomer` c
            ON c.customer_group = g.customer_group
        LEFT JOIN customer_addresses ca
            ON ca.customer_name = c.name

        WHERE g.parent = %s
          AND g.parenttype = 'POS Profile'

        GROUP BY g.customer_group;
        """,
        (pos_profile or frappe.local.pos_profile,),
        as_dict=True,
    )

    # 🔥 Parse JSON strings returned by MariaDB
    for row in data:
        if isinstance(row.get("customers"), str):
            row["customers"] = frappe.parse_json(row["customers"])

    return data


@frappe.whitelist(methods=["POST", "PUT"])
def customer_upsert(payload: dict):
    customer_data = payload.get("customer")
    addresses = payload.get("addresses", [])

    if not customer_data:
        frappe.throw("customer is required")

    # -----------------------------
    # 1️⃣ Upsert Customer
    # -----------------------------
    customer_name = customer_data.get("name")

    if customer_name and frappe.db.exists("Customer", customer_name):
        customer = frappe.get_doc("Customer", customer_name)
    else:
        customer = frappe.new_doc("Customer")

    customer.update(customer_data)
    customer.save(ignore_permissions=True)

    # -----------------------------
    # 2️⃣ Upsert Addresses
    # -----------------------------
    saved_addresses = []

    for addr in addresses:
        address_name = addr.get("name")

        if address_name and frappe.db.exists("Address", address_name):
            address = frappe.get_doc("Address", address_name)
        else:
            address = frappe.new_doc("Address")

        # # Basic fields
        address.update(addr)

        # -----------------------------
        # 🔗 Dynamic Link to Customer
        # -----------------------------
        # address.links = [{"link_doctype": "Customer", "link_name": customer.name}]
        address.links = []  # clear old links (important for upsert)
        address.append(
            "links", {"link_doctype": "Customer", "link_name": customer.name}
        )
        address.save(ignore_permissions=True)
        saved_addresses.append(address.name)

    frappe.db.commit()

    return {"customer": customer.name, "addresses": saved_addresses}
