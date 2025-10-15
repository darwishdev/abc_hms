
import frappe
@frappe.whitelist(methods=["GET"])
def printer_list_by_pos_profile(pos_profile):
    data = frappe.db.sql("""
       WITH printers_data as (
          select JSON_ARRAYAGG(pri.ip_address) ip_addresses_array , pri.print_class
        from `tabPOS Profile` p
        join `tabRestaurant` r on p.restaurant = r.name
        join `tabRestaurant Production Area` pa on r.name = pa.parent
        join `tabProduction Area` a on a.name = pa.production_area
        join `tabProduction Area Printer` pr on a.name = pr.parent
        join `tabPrinter` pri on pri.name = pr.printer
        where p.name = %s
        group by pri.print_class
        ) select JSON_OBJECTAGG(print_class, ip_addresses_array) printers from printers_data
    """,(pos_profile or frappe.local.pos_profile) , as_dict=True)




    if len(data) == 0:
        return
    return  frappe.parse_json(data[0]["printers"])

