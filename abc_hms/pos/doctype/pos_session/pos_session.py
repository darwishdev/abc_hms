import frappe
from frappe.database.database import random, string
from frappe.model.document import Document

from utils.date_utils import int_to_date


class POSSession(Document):
    @frappe.whitelist()
    def get_current_bussiness_date(self):
        if not self.pos_profile:
            # frappe.throw("pos_profile is required")
            self.pos_profile = "Main"
        business_date = frappe.db.sql(
            """
        select date_to_int(s.business_date) business_date from `tabPOS Profile` p
            JOIN `tabProperty Setting` s on p.property = s.name and p.name = %s
        """,
            (self.pos_profile),
            pluck=["business_date"],
        )
        if not business_date or len(business_date) == 0:
            frappe.throw("pos_profile is required")
        return business_date[0]

    def pos_opening_entry_from_pos_session(self):
        return ""

    def validate(self):
        from abc_hms.container import app_container

        current_business_date = self.get_current_bussiness_date()
        if self.for_date != current_business_date:
            frappe.throw(
                f"Business date mismatch. Expected: {current_business_date} Got: {self.for_date}",
                title="Invalid Business Date",
            )
        opening_entry = frappe.db.exists(
            "POS Opening Entry",
            {
                "for_date": self.for_date,
                "pos_profile": self.pos_profile,
                "status": "Open",
            },
        )
        if not opening_entry:
            if self.auto_create_opening_entry or True:
                property = frappe.db.get_value(
                    "POS Profile", self.pos_profile, "property"
                )
                entry = app_container.pos_opening_entry_usecase.pos_opening_entry_upsert(
                    {
                        "doc": {
                            "docstatus": 1,
                            "user": frappe.session.user,
                            "property": property,
                            "for_date": self.for_date,
                            "pos_profile": self.pos_profile,
                            "period_start_date": f"{int_to_date(self.for_date)} 00:00:00",
                            "balance_details": [
                                {
                                    "mode_of_payment": "Cash",
                                    "opening_amount": 0,
                                }
                            ],
                        },
                        "commit": True,
                    }
                )
                if not entry:
                    frappe.throw(
                        f"POS Profile {self.pos_profile} has no POS Opening Entry for date {self.for_date}"
                    )

        # def autoname(self):
        # if self.pos_profile and not self.for_date:
        #     self.for_date = self.get_current_bussiness_date()

        owner = getattr(self, "owner", None) or frappe.session.user
        owner_abbr = frappe.get_value("User", owner, "cashier_abbriviation")
        if owner_abbr:
            owner = owner_abbr
        rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        self.name = f"S-{owner}-{self.pos_profile}-{self.for_date}-{rand}"
