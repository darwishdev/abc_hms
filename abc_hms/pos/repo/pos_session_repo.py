from typing import List, Optional
import frappe
from abc_hms.dto.pos_session_dto import POSSession
class POSSessionRepo:
    def pos_session_upsert(self , docdata: POSSession, commit: bool = True)->POSSession:
        doc_id = docdata.get('name' , None)
        if doc_id and frappe.db.exists("POS Session", doc_id):
            doc: POSSession = frappe.get_doc("POS Session", doc_id) # type: ignore
        else:
            doc: POSSession = frappe.new_doc("POS Session") # type: ignore
        doc.update(docdata)
        doc.save()
        if commit:
            frappe.db.commit()

        return doc




    def pos_sessions_close_crrent_date(self , property: str):
        query = """
            UPDATE `tabPOS Session` s
            JOIN `tabProperty Setting` ps on s.property = ps.name
            SET s.docstatus = 1
            WHERE s.property = %s and for_date = date_to_int(ps.business_date);
        """
        return frappe.db.sql(query, (property,))

    def pos_session_list_for_current_date(self , property: str):
        query = """
            SELECT
                ps.name AS session,
                ps.owner
            FROM `tabProperty Setting` s
            JOIN `tabPOS Session` ps on ps.for_date = date_to_int(s.business_date) and ps.docstatus
            = 0
            WHERE s.name = %(property)s;
        """
        results = frappe.db.sql(query, {"property": property},as_dict=True)
        return results

    def pos_session_list(self , filters: Optional[POSSession])-> Optional[List[POSSession]]:
        docs = frappe.get_all("POS Session", filters=filters, limit=1)
        return docs
