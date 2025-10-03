from asyncio import sleep
from datetime import timedelta
import json
import time
from frappe.model.document import Document
from frappe.model.naming import make_autoname
import frappe
import os
from frappe import render_template
from frappe.utils import getdate
from sentry_sdk.utils import json_dumps
from abc_hms.container import app_container
from abc_hms.pos.doctype import folio
from utils import date_utils


class AvailabilityWarning(Exception):
    pass

class Reservation(Document):
    def fix_total_stay(self):
        base_rate = self.base_rate or 0
        nights = self.nights or 0

        total_stay = base_rate * nights
        if total_stay < 0:
            total_stay = 0

        return total_stay

    def fix_discount_amount(self):
        base_rate = (self.base_rate * self.nights) or 0
        rate_code_rate = (self.rate_code_rate * self.nights) or 0
        return rate_code_rate - base_rate

    def fix_discount_percent(self):
        base_rate = (self.base_rate * self.nights) or 0
        rate_code_rate = (self.rate_code_rate * self.nights) or 0
        return  100 - ((base_rate / rate_code_rate) * 100)

    def fix_base_rate(self):
        total_stay = self.total_stay or 0
        nights = self.nights or 0
        discount_amount = self.discount_amount or 0

        if nights > 0:
            base_rate = (total_stay + discount_amount) / nights
        else:
            base_rate = 0

        return base_rate


    def fix_nights(self):
        arrival_date = self.arrival
        departure_date = self.departure

        if arrival_date and departure_date:
            arrival_date = getdate(arrival_date)
            departure_date = getdate(departure_date)
            return (departure_date - arrival_date).days
        return 0

    def fix_departure(self):
        arrival_date = self.arrival
        nights = self.nights or 0

        if arrival_date:
            arrival_date = getdate(arrival_date)
            departure_date = arrival_date + timedelta(days=nights)
            return departure_date
    def autoname(self):
        if not self.property:
            frappe.throw("Property field is required to generate name")
        self.name = make_autoname(f"{self.property}-.######")
    def validate_room_status(self):
        return True
    def handle_save_error(self, e):
        """Centralized error handling for save."""
        args = self.as_dict()
        exc_msg = str(e)
        import re
        original_match = re.search(r"Original:\s*(.*)", exc_msg, re.DOTALL)
        clean_msg = original_match.group(1).strip() if original_match else exc_msg

        title = "Availability Warning"
        primary_action = {
            "label": "Ignore",
            "server_action": "abc_hms.ignore_and_resave",
            "hide_on_success": True,
            "args": json.dumps({**args, "ignore_availability": 1}, default=str),
        }

        if "already occupied" in exc_msg:
            title = "Room Already Occupied"
            clean_msg = clean_msg  # full original message
            primary_action = {
                "label": "Allow Share",
                "server_action": "abc_hms.ignore_and_resave",
                "hide_on_success": True,
                "args": json.dumps({**args, "allow_share": 1}, default=str),
            }

        frappe.throw(
            clean_msg,
            title=title,
            primary_action=primary_action
        )
    @frappe.whitelist()
    def get_business_date(self):
        property_business_date = frappe.db.get_value(
            "Property Setting",
            {"property": self.get("property")},
            "business_date"
        )
        self.created_on_business_date = property_business_date


    def save(self , *args , **kwargs):
        try:
            frappe.publish_progress(10, title="Saving", description="Syncing Reservation Dates")

            frappe.db.begin()

            if self.is_new():
                super().save(*args, **kwargs)
                frappe.publish_progress(100, title="Saving", description="Reservation Created Successfully")
                return
            if self.reservation_status == "Checked Out":
                folio = frappe.get_doc("Folio" ,{"reservation" : self.name})
                folio.submit()
            property_business_date = frappe.db.get_value(
                "Property Setting",
                {"property": self.get("property")},
                "business_date"
            )

            # Auto-mark arrival if arrival date equals property business date
            if self.docstatus == 1 and self.reservation_status == 'Confirmed' and date_utils.date_to_int(property_business_date) == date_utils.date_to_int(self.get("arrival")):
                self.reservation_status = "Arrival"

            critical_fields = [
                "arrival",
                "departure",
                "docstatus",
                "room_type",
                "room",
                "ignore_availability",
                "allow_share",
            ]

            for field in critical_fields:
                old_value = self.get_db_value(field)  # value in DB
                new_value = self.get(field)           # current value in memory
                if field in ("arrival", "departure"):
                    if old_value:
                        old_value = date_utils.date_to_int(old_value)
                    if new_value:
                        new_value = date_utils.date_to_int(new_value)

                if old_value != new_value:
                    print("changed is" , old_value , new_value , field)

                    frappe.publish_progress(60, title="Saving", description="Syncing Reservation Dates")
                    app_container.reservation_usecase.reservation_sync({
                            "reservation": self.name,
                            "new_arrival": self.arrival,
                            "new_departure": self.departure,
                            "new_docstatus": self.docstatus,
                            "new_reservation_status": self.reservation_status,
                            "new_room_type": self.room_type,
                            "new_rate_code": self.rate_code,
                            "new_room": self.room,
                            "ignore_availability": self.ignore_availability,
                            "allow_room_sharing": self.allow_share
                    })
                    time.sleep(1.0)
                    frappe.publish_progress(90, title="Saving", description="Reservation Days Synced Successfully")
                    break
            time.sleep(1.0)

            super().save(*args, **kwargs)

            if self.reservation_status in  ("Confirmed" , "Arrival"):
                self.ensure_folio()
            frappe.publish_progress(100, title="Saving", description="Reservation Days Synced Successfully")
            frappe.db.commit()
        except Exception as e:
            frappe.db.rollback()
            self.handle_save_error(e)
    @frappe.whitelist()
    def ensure_all_folios(self):
        reservations = frappe.get_all("Reservation")
        result = []
        for reservation in reservations:
            docstatus = frappe.get_value("Reservation" , reservation.name , 'docstatus')
            if docstatus != 2:
                result.append(reservation)
                folio = self.ensure_folio_with_name(reservation.name)
                result.append(folio)

        frappe.db.commit()
        return {"res" : result}

    def remove_folio(self):
        folio_name = f"f-{self.name}"
        if frappe.db.exists("Folio", folio_name):
            folio_doc = frappe.get_doc("Folio", folio_name)
            folio_doc.delete(ignore_permissions=True)
            frappe.publish_progress(98, title="Saving", description="Folio created for reservation")


    def ensure_folio_with_name(self , name: str):
        folio = frappe.get_doc("Folio" , {"reservation": name}) if frappe.db.exists("Folio" ,{"reservation":name}) else None
        if folio:
            return folio
        folio= frappe.new_doc("Folio")
        folio.update({
            "pos_profile": "Main",
            "reservation": name
        })
        folio.save()
        return folio
    def ensure_folio(self):
        if not frappe.db.exists("Folio", {"reservation": self.name}):
            folio= frappe.new_doc("Folio")
            folio.update({
                "pos_profile": "Main",
                "reservation": self.name
            })
            folio.save()
            frappe.publish_progress(98, title="Saving", description="Folio created for reservation")

    # This function must be whitelisted so the dialog button can call it.
    @frappe.whitelist()
    def get_availability(self):
        doctype_path = os.path.dirname(__file__)
        template_path = os.path.join(doctype_path, 'availability.html')

        with open(template_path, 'r', encoding='utf-8') as file:
            template_content = file.read()

        params = {
            "property": self.get("property"),
            "arrival": self.get("arrival"),
            "departure": self.get("departure"),
            "room_categories":  None,
            "room_types": getattr(self, "room_types", None),
            "rate_code": getattr(self, "rate_code", None),
        }

        data = app_container.reservation_usecase.reservation_availability_check(params)
        return render_template(template_content, data)


    @frappe.whitelist()
    def sync_arrival_departure_nights(self, changed_field: str):
        if changed_field in ("nights" , "arrival"):
            self.departure = self.fix_departure()
        elif changed_field == "departure":
            self.nights = self.fix_nights()

        self.total_stay = self.fix_total_stay()
        self.discount_amount = self.fix_discount_amount()
    @frappe.whitelist()
    def apply_discount(self, changed_field: str):
        if changed_field == "base_rate":
            self.total_stay = self.fix_total_stay()
            if self.base_rate != self.rate_code_rate and self.rate_code_rate != 0:
                self.discount_amount = self.fix_discount_amount()
                self.discount_percent = self.fix_discount_percent()
            else:
                self.discount_amount = None
                self.discount_percent = None
        if changed_field == "discount_percent":
            self.base_rate = self.rate_code_rate - ( self.rate_code_rate * (self.discount_percent / 100))
            self.total_stay = self.fix_total_stay()
            self.discount_amount = self.fix_discount_amount()
        if changed_field == "discount_amount":
            self.base_rate = self.rate_code_rate - (self.discount_amount / self.nights)
            self.total_stay = self.fix_total_stay()
            self.discount_percent = self.fix_discount_percent()
