import  json, os
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields, frappe

def install_custom_fields(custom_dir: str):
    for fname in os.listdir(custom_dir):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(custom_dir, fname)
        with open(path) as f:
            fields = json.load(f)

        # Use filename as-is (with spaces), don’t force .title()
        doctype = os.path.splitext(fname)[0].replace("_", " ")

        if not frappe.db.exists("DocType", doctype):
            frappe.throw(f"Invalid Doctype from customefields filename: {doctype}")

        fieldmap = {doctype: fields}
        try:
            create_custom_fields(fieldmap, update=True)
        except:
            pass
