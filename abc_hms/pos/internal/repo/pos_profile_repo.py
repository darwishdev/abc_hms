import  json
import frappe
class POSProfileRepo:
    def profile_mode_of_payment_list(self, pos_profile: str):
        return frappe.get_all(
            "POS Payment Method" ,
            {
                "parent" : pos_profile , "parenttype" : "POS Profile"
            },
            "mode_of_payment as name",
        )
    def profile_item_list(self , pos_profile: str):
        profile_groups = frappe.db.sql("""
        select item_group from `tabPOS Item Group` where parent = %s
        """ , (pos_profile) , pluck="name")
        results = []

        for group in profile_groups:
            groups_q = """
            -- Fixed query - corrected JOIN syntax for item prices
WITH RECURSIVE hierarchy AS (
    -- Get all descendants of F&B (ONLY from tabItem Group, not tabItem)
    SELECT name, parent_item_group, 1 as level
    FROM `tabItem Group`
    WHERE name = %s

    UNION ALL

    SELECT t.name, t.parent_item_group, h.level + 1
    FROM `tabItem Group` t  -- Only join with Item Groups, not Items
    JOIN hierarchy h ON t.parent_item_group = h.name
)

SELECT
    %s as group_name,
    (
        SELECT JSON_ARRAYAGG(
            JSON_OBJECT(
                'name', h1.name,
                'parent', h1.parent_item_group,
                'level', h1.level,
                'children', (
                    -- Get child GROUPS only (from hierarchy CTE)
                    SELECT CASE
                        WHEN COUNT(*) > 0 THEN JSON_ARRAYAGG(
                            JSON_OBJECT(
                                'name', h2.name,
                                'parent', h2.parent_item_group,
                                'level', h2.level,
                                'children', (
                                    -- Get grandchild GROUPS only
                                    SELECT CASE
                                        WHEN COUNT(*) > 0 THEN JSON_ARRAYAGG(
                                            JSON_OBJECT(
                                                'name', h3.name,
                                                'parent', h3.parent_item_group,
                                                'level', h3.level,
                                                'children', (
                                                    -- Get great-grandchild GROUPS only (level 4)
                                                    SELECT CASE
                                                        WHEN COUNT(*) > 0 THEN JSON_ARRAYAGG(
                                                            JSON_OBJECT(
                                                                'name', h4.name,
                                                                'parent', h4.parent_item_group,
                                                                'level', h4.level,
                                                                'children', NULL,
                                                                'items', (
                                                                    -- Items for level 4 (deepest level)
                                                                    SELECT CASE
                                                                        WHEN COUNT(*) > 0 THEN JSON_ARRAYAGG(
                                                                            JSON_OBJECT(
                                                                                'name', i.name,
                                                                                'item_group', i.item_group,
                                                                                'item_code', i.item_code,
                                                                                'item_price', ip.price_list_rate
                                                                            )
                                                                        )
                                                                        ELSE NULL
                                                                    END
                                                                    FROM `tabItem` i
                                                                    JOIN `tabItem Price` ip ON i.name = ip.item_code AND ip.price_list = 'Standard Selling'
                                                                    WHERE i.item_group = h4.name
                                                                )
                                                            )
                                                        )
                                                        ELSE NULL
                                                    END
                                                    FROM hierarchy h4
                                                    WHERE h4.parent_item_group = h3.name
                                                ),
                                                'items', (
                                                    -- Items for level 3 (only if it's a leaf - no level 4 children)
                                                    SELECT CASE
                                                        WHEN NOT EXISTS (SELECT 1 FROM hierarchy h4 WHERE h4.parent_item_group = h3.name)
                                                        AND COUNT(*) > 0 THEN JSON_ARRAYAGG(
                                                            JSON_OBJECT(
                                                                'name', i.name,
                                                                'item_group', i.item_group,
                                                                'item_code', i.item_code,
                                                                'item_price', ip.price_list_rate
                                                            )
                                                        )
                                                        ELSE NULL
                                                    END
                                                    FROM `tabItem` i
                                                    JOIN `tabItem Price` ip ON i.name = ip.item_code AND ip.price_list = 'Standard Selling'
                                                    WHERE i.item_group = h3.name
                                                )
                                            )
                                        )
                                        ELSE NULL
                                    END
                                    FROM hierarchy h3
                                    WHERE h3.parent_item_group = h2.name
                                ),
                                'items', (
                                    -- Items for level 2 (only if it's a leaf - no level 3 children)
                                    SELECT CASE
                                        WHEN NOT EXISTS (SELECT 1 FROM hierarchy h3 WHERE h3.parent_item_group = h2.name)
                                        AND COUNT(*) > 0 THEN JSON_ARRAYAGG(
                                            JSON_OBJECT(
                                                'name', i.name,
                                                'item_group', i.item_group,
                                                'item_code', i.item_code,
                                                'item_price', ip.price_list_rate
                                            )
                                        )
                                        ELSE NULL
                                    END
                                    FROM `tabItem` i
                                    JOIN `tabItem Price` ip ON i.name = ip.item_code AND ip.price_list = 'Standard Selling'
                                    WHERE i.item_group = h2.name
                                )
                            )
                        )
                        ELSE NULL
                    END
                    FROM hierarchy h2
                    WHERE h2.parent_item_group = h1.name
                ),
                'items', (
                    -- Items for level 1 (only if it's a leaf - no level 2 children)
                    SELECT CASE
                        WHEN NOT EXISTS (SELECT 1 FROM hierarchy h2 WHERE h2.parent_item_group = h1.name)
                        AND COUNT(*) > 0 THEN JSON_ARRAYAGG(
                            JSON_OBJECT(
                                'name', i.name,
                                'item_group', i.item_group,
                                'item_code', i.item_code,
                                'item_price', ip.price_list_rate
                            )
                        )
                        ELSE NULL
                    END
                    FROM `tabItem` i
                    JOIN `tabItem Price` ip ON i.name = ip.item_code AND ip.price_list = 'Standard Selling'
                    WHERE i.item_group = h1.name
                )
            )
        )
        FROM hierarchy h1
        WHERE h1.parent_item_group = %s
    ) as children;
            """
            items = frappe.db.sql(
                groups_q,
                (group,group,group),
                as_dict=True
            )
            for item in items:
                children = item.get("children")
                if children:
                    if isinstance(children, str):
                        try:
                            item["children"] = json.loads(children)
                        except json.JSONDecodeError:
                            # log it for debugging
                            frappe.logger().warning(f"Invalid JSON in children for item {item.get('name')}")
                            # fallback: leave it as raw string
                            item["children"] = children
            results.extend(items)  # push results from each group
        return results

