from frappe.model.document import Document
from frappe.model.naming import make_autoname
import frappe
import os
from frappe import render_template

from abc_hms.container import container

class Reservation(Document):
    def autoname(self):
        if not self.property:
            frappe.throw("Property field is required to generate name")
        # Prefix with property + 6 digit sequence
        self.name = make_autoname(f"{self.property.upper()}-.######")



    @frappe.whitelist()
    def get_availability(self):

        # Get template file path
        doctype_path = os.path.dirname(__file__)
        template_path = os.path.join(doctype_path, 'availability.html')

        # Read and render template
        with open(template_path, 'r', encoding='utf-8') as file:
            template_content = file.read()

        params = {
            "property": self.property,
            "arrival": self.arrival,
            "departure": self.departure,
            "room_categories":  None,
            "room_types": getattr(self, "room_types", None),
            "rate_code": getattr(self, "rate_code", None),
        }

        data = container.reservation_usecase.reservation_availability_check(params)
        return render_template(template_content, data)
