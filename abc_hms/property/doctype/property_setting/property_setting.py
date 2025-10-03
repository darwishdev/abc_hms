import json
import frappe
from frappe.model.document import Document


class PropertySetting(Document):
    def validate_arrivals(self):
        arrivals = frappe.db.sql("""
            SELECT r.name , r.reservation_status from tabReservation r WHERE r.reservation_status = 'Arrival'
        """ , as_dict=True)
        if len(arrivals) > 0:
            frappe.throw(f"Arrivals found for current business date {json.dumps(arrivals)}" , exc=frappe.ValidationError)
            raise frappe.ValidationError(f"Arrivals Found for data {for_date}" )

    def validate_departures(self):
        departures = frappe.db.sql("""
            SELECT r.name from tabReservation r WHERE r.reservation_status = 'Departure'
        """ , as_dict=True)
        if len(departures) > 0:
            frappe.throw(f"Departures  found for current business date  {json.dumps(departures)}" , exc=frappe.ValidationError)
            raise frappe.ValidationError(f"Arrivals Found for data {for_date}" )

    def validate_sessions(self , for_date: str):
        sessions = frappe.db.sql("""
            SELECT s.name from `tabPOS Session` s WHERE s.for_date = date_to_int(%s) AND s.docstatus
            = 0
        """ , for_date , as_dict=True)
        if len(sessions) > 0:
            frappe.throw(f"Session Found for data {json.dumps(sessions)}" , exc=frappe.ValidationError)
            raise frappe.ValidationError(f"Sessions  found for current business date {for_date}" )

    def validate(self):
        original_value = frappe.db.get_value("Property Setting" , self.name , "business_date")
        self.validate_arrivals()
        self.validate_sessions(original_value)
        self.validate_departures()
