from typing import Dict
import frappe
from abc_hms.container import app_container


@frappe.whitelist()
def room_list_input(doctype, txt, searchfield, start, page_len, filters):
    print(txt)
    print(searchfield)
    print(start)
    print(page_len)
    # return (txt , searchfield,start,page_len)
    pay_master = False
    if filters:
        if filters["pay_master"]:
            pay_master = filters["pay_master"]
        return app_container.room_usecase.room_list_input(pay_master,txt,searchfield,start,page_len)
@frappe.whitelist()
def room_list(filters ):
    return app_container.room_usecase.room_list(filters)
