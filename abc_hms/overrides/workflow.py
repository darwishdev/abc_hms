import frappe
from frappe.model.workflow import apply_workflow as _apply_workflow

@frappe.whitelist()
def apply_folio_workflow(doc, action):
    """
    Intercept workflow transitions for Folio doctype.
    """
    if isinstance(doc, str):
        doc = frappe.get_doc(frappe.parse_json(doc))

    if doc.doctype != "Folio":
        return _apply_workflow(doc, action)

    return doc.apply_workflow(doc,action)
    frappe.logger().info(f"[Folio Workflow] Action triggered: {action} for {doc.name}")

    # Example: run pre-action custom logic
    if action == "Require Deposit":
        handle_require_deposit(doc)
    elif action == "Create Full Payment":
        handle_full_payment(doc)
    elif action == "Merge Folio":
        handle_merge(doc)
    elif action == "Submit Folio":
        handle_submit(doc)

    # You can decide to:
    # 1️⃣ Skip default apply_workflow and set your own state manually, or
    # 2️⃣ Call the normal apply_workflow afterwards

    # Example: continue with normal workflow
    result = _apply_workflow(doc, action)

    # Example: run post-action logic
    frappe.logger().info(f"[Folio Workflow] Transition completed to {doc.folio_status}")

    return result


def handle_require_deposit(doc):
    frappe.logger().info(f"Handling deposit for folio {doc.name}")
    # your logic here (e.g. create a Payment Entry)
    pass


def handle_full_payment(doc):
    frappe.logger().info(f"Handling full payment for folio {doc.name}")
    pass


def handle_merge(doc):
    frappe.logger().info(f"Merging folio {doc.name}")
    pass


def handle_submit(doc):
    frappe.logger().info(f"Submitting folio {doc.name}")
    pass
