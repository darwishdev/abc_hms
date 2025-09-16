from frappe.model.document import Document
from frappe.model.naming import make_autoname
import frappe
import os
from frappe import render_template
from frappe.model.workflow import apply_workflow
from pymysql import err as pymysql_err
from abc_hms.container import app_container


class AvailabilityWarning(Exception):
    pass

class Reservation(Document):
    def autoname(self):
        if not self.property:
            frappe.throw("Property field is required to generate name")
        self.name = make_autoname(f"{self.property.upper()}-.######")

    def on_submit(self):
        try:
            app_container.reservation_usecase.reservation_sync_days(self.as_dict()    , 0 , 0)
        except pymysql_err.OperationalError as e:
            frappe.throw(
                f"""AVAILABILITY_ERROR {str(e)}""",
                title="Availability Warning",
                primary_action={
                    "label": "Ignore",
                    "client_action": "ignore_availability_action"
                }
            )

    def on_update_after_submit(self):
        if self.reservation_status != "In House":
            self._critical_fields = ["arrival", "departure","nights", "room_type_assigned", "room_type", "room", "docstatus"]
            self._original_values = {f: self.get_db_value(f) for f in self._critical_fields}
            self._fields_changed = any(self.has_value_changed(f) for f in self._critical_fields)

        if getattr(self, "_fields_changed", False):
            try:
                self._run_reservation_sync(ignore_availability=0)
                self.show_availability_warning("warnign")
            except pymysql_err.OperationalError as e:

                if e.args[0] == 1644:
                    # Rollback only changed fields
                    for f, val in self._original_values.items():
                        setattr(self, f, val)
                    self.db_update()

                    msg = str(e)
                    if "No availability" in msg:
                    #     frappe.confirm(
                    #         msg,
                    #         lambda: None,  # Close action (do nothing)
                    #         lambda: ignore_availability_function(),  # Ignore availability action
                    #         title="Availability Warning",
                    #         primary_label="Ignore Availability",
                    #         secondary_label="Close"
                    #     )
                        self.show_availability_warning("warnign")
                        #   frappe.throw(str(e), title="Availability Warning", exc="AvailabilityWarning")
                    else:
                        frappe.throw(f"Reservation update failed: {msg}")
                else:
                    raise

    @frappe.whitelist()
    def get_availability(self):
        doctype_path = os.path.dirname(__file__)
        template_path = os.path.join(doctype_path, 'availability.html')

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

        data = app_container.reservation_usecase.reservation_availability_check(params)
        return render_template(template_content, data)
