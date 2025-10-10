from typing import List, Optional
import frappe
from sentry_sdk.utils import json_dumps
from abc_hms.dto.pos_session_dto import POSSession
from pymysql.err import IntegrityError

from utils.sql_utils import run_sql
class POSSessionRepo:
    def pos_session_find(self,pos_sesison:str):
        def sql_call(cur, _):
            cur.execute(
                """
                CALL pos_session_find(%s)
                """,
                (pos_sesison,),
            )
            item_details = cur.fetchall()
            if not cur.nextset():
                return {"item_details": item_details, "payment_details": []}
            payment_details = cur.fetchall()
            return {
                "item_details": item_details,
                "payment_details": payment_details
            }
        return run_sql(sql_call)
    def pos_session_upsert(self , docdata: POSSession, commit: bool = True)->POSSession:
        try:
            if  "name" not in docdata:
                pos_profiles = frappe.db.sql("""
                    SELECT name from `tabPOS Session` WHERE pos_profile = %s AND owner =
                    %s AND docstatus = 0
                    """,
                (docdata["pos_profile"] , frappe.session.user),
                pluck='name')
                if len(pos_profiles) > 0:
                    doc = frappe.get_doc("POS Session" , pos_profiles[0])
                    return doc
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

        except IntegrityError as e:
            raise frappe.DuplicateEntryError(f"{str(e)}")




    def pos_sessions_close_for_date_profile(self , for_date: int , profile : str):
        sessions = frappe.db.get_all("POS Session" , {
            "pos_profile" : profile,
            "docstatus" : 0,
            "for_date" : for_date,
        })
        for session in sessions:
            session_doc = frappe.get_doc("POS Session" ,  session["name"])
            session_doc.submit()
        return sessions
    def pos_sessions_close_crrent_date(self , property: str):
        query = """
            UPDATE `tabPOS Session` s
            JOIN `tabProperty Setting` ps on s.property = ps.name
            SET s.docstatus = 1
            WHERE s.property = %s and for_date = date_to_int(ps.business_date);
        """
        return frappe.db.sql(query, (property,))

    def pos_session_find_for_user(self , user: str , profile: str , docstatus: int ):
        query = """
            select s.name , s.owner as "user" , s.for_date  from `tabPOS Session` s
              join `tabPOS Profile` p on  p.name = s.pos_profile
              JOIN `tabProperty Setting` ps on p.property = ps.property and  s.for_date = date_to_int(ps.business_date)
              where s.owner = %s and s.pos_profile = %s and s.docstatus = %s
        """
        results = frappe.db.sql(query, (user , profile , docstatus) ,as_dict=True)
        return results
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
