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
            property_setting  = frappe.db.sql("""
                SELECT
                p.company ,
                s.business_date ,
                date_to_int(s.business_date) business_date_int,
                s.default_pos_profile,
                s.default_rooms_item_group
                FROM `tabProperty Setting` s JOIN tabProperty p ON s.name = p.name WHERE s.name =
                %s
            """ , (property_name,) , as_dict=True)
            if not property_setting or len(property_setting) == 0:
                raise frappe.NotFound(f"Property {property_name} Not Found Or Not Configured")
            return property_setting[0] # type: ignore




    def property_setting_increase_business_date(self, property_name: str, commit: bool = False)-> PropertySettingData :
        try:
            # Reuse existing method to get current business date
            property_setting_doc = frappe.get_doc("Property Setting" , property_name)
            property_setting_doc.update({"business_date" : add_days(property_setting_doc.business_date, 1)})
            property_setting_doc.save()
            if commit:
                frappe.db.commit()

            return self.property_setting_find(property_name)

        except frappe.DoesNotExistError:
            frappe.throw(f"Property Setting not found: {property_name}")
            raise
        except Exception:
            frappe.log_error(frappe.get_traceback(), "PropertySetting IncreaseBusinessDateFind Error")
            raise
