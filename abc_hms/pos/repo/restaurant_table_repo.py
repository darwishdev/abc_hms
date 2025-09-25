
import frappe
from typing import   List, Optional, cast

class RestaurantTableRepo:
    def table_list(self, restaurant:str):
        result = frappe.db.sql("""
            select
              a.name,
              a.display_name,
              a.sequance ,
              JSON_ARRAYAGG(
                      JSON_OBJECT(
                          'table_name', t.name,
                          'display_name', t.display_name
                      )
                    ) tables
              from

              `tabRestaurant Area` a
              join `tabRestaurant Table` t on a.name = t.restaurant_area
              where a.restaurant = %s order by a.sequance  , t.sequance;
        """, (restaurant,), as_dict=True)
        return result

