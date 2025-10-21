import json
from frappe.model.document import Document
from frappe.model.naming import make_autoname
import frappe
import time
import os
from frappe import render_template
from sentry_sdk.utils import json_dumps
from abc_hms.container import app_container
from abc_hms.exceptions.exceptions import AvailabilityError, RoomShareError
from utils.date_utils import date_to_int


class AvailabilityWarning(Exception):
    pass


class Reservation(Document):
    def autoname(self):
        property = self.as_dict()["property"]
        if not property:
            frappe.throw("Property field is required to generate name")
        self.name = make_autoname(f"{property}-.######")

    def get_availability(self):
        doctype_path = os.path.dirname(__file__)
        template_path = os.path.join(doctype_path, "availability.html")

        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()

        params = {
            "property": self.get("property"),
            "arrival": self.get("arrival"),
            "departure": self.get("departure"),
            "room_category": None,
            "discount_type": self.get("discount_type"),
            "discount_percent": self.get("discount_percent"),
            "discount_amount": self.get("discount_amount"),
            "room_type": getattr(self, "room_type", None),
            "rate_code": getattr(self, "rate_code", None),
        }
        data = app_container.reservation_usecase.reservation_availability_check(params)
        if self.get("room_type") != None and self.get("rate_code") != None:
            if data["rates"]:
                if len(data["rates"] > 0):
                    self.base_rate = data["rates"][0]["base_rate"]
                    self.rate_code_rate = data["rates"][0]["base_rate"]
                    self.currency = data["rates"][0]["currency"]
                    self.exchange_rate = data["rates"][0]["exchange_rate"]
                    self.total_stay = self.base_rate * self.nights
        return render_template(template_content, data)

    @frappe.whitelist()
    def get_business_date(self):
        property_business_date = frappe.db.get_value(
            "Property Setting", {"property": self.get("property")}, "business_date"
        )
        self._current_business_date = property_business_date
        if self.is_new():
            self.created_on_business_date = property_business_date
        return property_business_date

    def handle_sync(self, is_submit: bool):
        frappe.publish_progress(
            10,
            title="Saving Reservation",
            description="Check If Critical Fields Has Been Changed : Statred",
        )
        # raise AvailabilityError("Reservation update blocked: has errors2")
        if not is_submit:
            is_critical_effect = self.critical_fields_check()
            time.sleep(0.2)
            frappe.publish_progress(
                20,
                title="Saving Reservation",
                description="Check If Critical Fields Has Been Changed : Done",
            )
            if not is_critical_effect:
                time.sleep(0.02)
                frappe.publish_progress(
                    100,
                    title="Saving Reservation",
                    description="No Critical Fields Changed And Reservation Updated",
                )
                return
        self.reservation_date_sync()
        self.reservation_folio_sync()

    @frappe.whitelist()
    def reservation_status_update(self, new_status):
        if new_status == "Checked Out":
            folio = self.reservation_folio_find()
            balance = folio["balance"]
            if balance > 1:
                frappe.throw(f"Folio balance is not zero")
        self.reservation_status = new_status
        self.save()

    def before_submit(self):
        business_date = self.get_business_date()
        self.reservation_status = (
            "Confirmed" if self.arrival != business_date else "Arrival"
        )
        self.handle_sync(is_submit=True)

    def before_update_after_submit(self):
        self.handle_sync(is_submit=False)

    @frappe.whitelist()
    def critical_fields_check(self):
        if not self.name:
            return
        critical_fields = [
            "arrival",
            "departure",
            "docstatus",
            "room_type",
            "room",
            "ignore_availability",
            "allow_share",
        ]
        old_values = frappe.get_doc("Reservation", self.name, critical_fields)
        if not old_values:
            return
        for field in critical_fields:
            old_value = old_values.as_dict()[field]
            new_value = self.get(field)
            if field in ("arrival", "departure"):
                if old_value:
                    old_value = date_to_int(old_value)
                if new_value:
                    new_value = date_to_int(new_value)
            if old_value != new_value:
                return True

        return False

    @frappe.whitelist()
    def reservation_date_sync(self):
        skip_fields = ["modified", "creation", "modified_by", "owner", "idx", "doctype"]
        form = self.as_dict()
        filtered_form = {}

        frappe.publish_progress(
            50, title="Saving Reservation", description="Reservation Dates Sync Started"
        )
        for key, value in form.items():
            if key not in skip_fields:
                filtered_form[key] = value

        try:
            app_container.reservation_usecase.reservation_date_sync(filtered_form)
        except AvailabilityError as e:
            err_msg = str(e)
            frappe.publish_realtime(
                event="handle_error",
                message={
                    "message": err_msg,
                    "type": "Availability",
                    "frm": filtered_form,
                },
                user=frappe.session.user,  # or specific user
            )
            raise e

        except RoomShareError as e:
            err_msg = str(e)
            frappe.publish_realtime(
                event="handle_error",
                message={
                    "message": err_msg,
                    "type": "Room Sharing",
                    "frm": filtered_form,
                },
                user=frappe.session.user,  # or specific user
            )
            raise e
        finally:
            time.sleep(0.2)
            frappe.publish_progress(
                95,
                title="Saving Reservation",
                description="Reservation Dates Synced Successflly",
            )

    @frappe.whitelist()
    def reservation_folio_find(self):
        doc = frappe.get_doc("Folio", {"reservation": self.name})
        balance_data = doc.folio_find_balance()
        balance_dict = balance_data["balance"]
        balance_value = balance_dict["amount"] - balance_dict["paid"]
        # self._current_folio_balance = balance_value
        # self._current_folio_name = doc.name
        return {"balance": balance_value, "folio_name": doc.name}

    def reservation_folio_sync(self):
        if not frappe.db.exists("Folio", {"reservation": self.name}):
            folio = frappe.new_doc("Folio")
            folio.update({"pos_profile": "Main", "reservation": self.name})
            folio.save()
            frappe.publish_progress(
                100,
                title="Saving Reservation",
                description="Reservation Dates Synced Successflly",
            )
