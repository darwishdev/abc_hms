import frappe

def execute():
    # 1. Get the DocField for 'status' in 'POS Invoice'
    doctype_name = "POS Invoice"
    fieldname = "status"

    # Use frappe.get_doc to retrieve the DocField
    status_field = frappe.get_doc("DocField", {"parent": doctype_name, "fieldname": fieldname})

    # 2. Check if 'Merged' is already present
    current_options = status_field.options.split('\n')
    new_option = "Merged"

    if new_option not in current_options:
        # 3. Append the new status option to the list
        current_options.append(new_option)

        # 4. Reconstruct the options string and update the DocField
        status_field.options = '\n'.join(current_options)

        # 5. Save the updated DocField
        status_field.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.msgprint(f"'{new_option}' status option added to {doctype_name}.")
