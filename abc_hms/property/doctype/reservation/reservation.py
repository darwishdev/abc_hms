from asyncio import sleep
import json
import time
from frappe.model.document import Document
from frappe.model.naming import make_autoname
import frappe
import os
from frappe import render_template
from sentry_sdk.utils import json_dumps
from abc_hms.container import app_container
from abc_hms.pos.doctype import folio
from utils import date_utils


class AvailabilityWarning(Exception):
    pass

class Reservation(Document):
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

    # def can_check_out(self):
    #     result = frappe.db.sql(
    #         """
    #         WITH items AS (
    #             SELECT
    #                 i.folio_window,
    #                 SUM(i.amount) AS amount
    #             FROM `tabPOS Invoice Item` i
    #             GROUP BY i.folio_window
    #         ), payments AS (
    #             SELECT
    #                 p.folio_window,
    #                 SUM(p.amount) AS amount
    #             FROM `tabSales Invoice Payment` p
    #             GROUP BY p.folio_window
    #         )
    #         SELECT
    #             fw.name AS folio_window,
    #             COALESCE(items.amount, 0) AS amount,
    #             COALESCE(payments.amount, 0) AS paid
    #         FROM `tabReservation` r
    #         JOIN `tabFolio` f ON f.reservation = r.name
    #         JOIN `tabFolio Window` fw ON fw.folio = f.name
    #         LEFT JOIN items ON fw.name = items.folio_window
    #         LEFT JOIN payments ON fw.name = payments.folio_window
    #         WHERE r.name = %s
    #         """,
    #         (self.name,),
    #         as_dict=True,
    #     )
    #
    #     if not result:
    #         return False  # no folio, cannot check out
    #
    #     row = result[0]
    #     total_amount = row.get("amount") or 0
    #     total_paid = row.get("paid") or 0
    #
    #     return total_amount == total_paid
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
                            "new_room": self.room,
                            "ignore_availability": self.ignore_availability,
                            "allow_room_sharing": self.allow_share
                    })
                    time.sleep(1.0)
                    frappe.publish_progress(90, title="Saving", description="Reservation Days Synced Successfully")
                    break
            time.sleep(1.0)

            super().save(*args, **kwargs)

            if self.reservation_status == "Confirmed":
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


