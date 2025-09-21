import frappe
from frappe.utils import add_days
from abc_hms.dto.property_setting_dto import PropertySettingBusinessDateFindResult, PropertySettingData, PropertySettingFindResult
from abc_hms.property.doctype.property_setting.property_setting import PropertySetting
from utils.date_utils import date_to_int
class PropertySettingRepo:
    def property_setting_upsert(self, docdata: PropertySetting, commit: bool = False) ->PropertySettingData:
        try:
            doc_id = docdata.get("name", None)
            if doc_id and frappe.db.exists("Property Setting", doc_id):
                doc: PropertySettingData = frappe.get_doc("Property Setting", doc_id)  # type: ignore
            else:
                doc: PropertySettingData = frappe.new_doc("Property Setting")  # type: ignore

            doc.update(docdata)
            doc.save()
            if commit:
                frappe.db.commit()

            return doc
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "PropertySetting Upsert Error")
            raise



    def property_setting_find(self, property_name: str) -> PropertySettingData:
            property_setting : PropertySettingData = frappe.db.sql("""
                SELECT
                p.company ,
                s.business_date ,
                date_to_int(s.business_date) business_date_int,
                s.default_pos_profile,
                s.default_rooms_item_group
                FROM `tabProperty Setting` s JOIN tabProperty p ON s.name = p.name WHERE s.name =
                %s
            """ , (property_name,) , as_dict=True)[0] # type: ignore
            return property_setting




    def property_setting_increase_business_date(self, property_name: str, commit: bool = False)-> PropertySettingData :
        try:
            # Reuse existing method to get current business date
            result = self.property_setting_find(property_name)
            current_date_str = result.get("business_date")

            # Compute next date
            next_date = add_days(current_date_str, 1)

            # Update business_date in DB directly
            frappe.db.set_value("Property Setting", property_name, "business_date", next_date)

            if commit:
                frappe.db.commit()

            return self.property_setting_find(property_name)

        except frappe.DoesNotExistError:
            frappe.throw(f"Property Setting not found: {property_name}")
            raise
        except Exception:
            frappe.log_error(frappe.get_traceback(), "PropertySetting IncreaseBusinessDateFind Error")
            raise
