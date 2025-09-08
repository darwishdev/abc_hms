import frappe

from .device_auth import device_protected
from .pos_session import session_find_active

@frappe.whitelist()
def item_list():
    """
    Return nested item groups and items for active POS Profile session.
    Traverses from POS Profile groups down to leaf-level items.
    """
    session = session_find_active()

    # Get POS Profile item groups
    pos_groups = frappe.db.get_all(
        'POS Item Group',
        {"parent": session.pos_profile, 'parenttype': "POS Profile"},
        "name,item_group"
    )

    if not pos_groups:
        return {"ok": False, "message": "No item groups found for POS Profile"}

    # Get all item group IDs from POS Profile
    pos_group_ids = [group.item_group for group in pos_groups]

    # Build complete hierarchy starting from POS groups
    hierarchy = build_complete_hierarchy(pos_group_ids)

    return {
        "ok": True,
        "pos_profile": session.pos_profile,
        "groups": hierarchy
    }

def build_complete_hierarchy(root_group_ids):
    """
    Build complete nested hierarchy from root groups down to items.
    """
    hierarchy = []

    for group_id in root_group_ids:
        group_tree = build_group_with_children(group_id)
        if group_tree:
            hierarchy.append(group_tree)

    return hierarchy

def build_group_with_children(group_id, visited=None):
    """
    Recursively build group tree with all children and leaf-level items.
    """
    if visited is None:
        visited = set()

    # Prevent infinite recursion
    if group_id in visited:
        return None
    visited.add(group_id)

    # Get group details
    group_data = frappe.db.get_value(
        "Item Group",
        group_id,
        ["name", "item_group_name", "parent_item_group", "is_group"],
        as_dict=True
    )

    if not group_data:
        return None

    # Build group structure
    group_tree = {
        "item_group_id": group_data.name,
        "item_group_name": group_data.item_group_name,
        "is_group": group_data.is_group,
        "child_groups": [],
        "items": []
    }

    if group_data.is_group:
        # Get child groups
        child_groups = frappe.db.get_all(
            "Item Group",
            filters={"parent_item_group": group_id},
            fields=["name", "item_group_name", "is_group"]
        )

        # Recursively build child groups
        for child in child_groups:
            child_tree = build_group_with_children(child.name, visited.copy())
            if child_tree:
                group_tree["child_groups"].append(child_tree)

    # Always check for items at this level (leaf or non-leaf)
    items = get_items_for_group(group_id)
    group_tree["items"] = items

    return group_tree

def get_items_for_group(group_id):
    """
    Get all items for a specific item group.
    """
    items = frappe.db.get_all(
        "Item",
        filters={
            "item_group": group_id,
            "disabled": 0
        },
        fields=[
            "name", "item_name", "description",
            "stock_uom", "standard_rate", "disabled"
        ]
    )

    # Format items for response
    formatted_items = []
    for item in items:
        formatted_items.append({
            "item_code": item.name,
            "item_name": item.item_name,
            "description": item.description,
            "uom": item.stock_uom,
            "rate": float(item.standard_rate) if item.standard_rate else 0.0,
            "disabled": item.disabled
        })

    return formatted_items

# Alternative optimized version using single query
def item_list_optimized():
    """
    Optimized version using the view we created earlier.
    """
    session = session_find_active()

    # Use the view query we created earlier
    rows = frappe.db.sql(
        """
        SELECT
            pp.name                 AS pos_profile,
            ig.name                 AS item_group_id,
            ig.item_group_name      AS item_group_name,
            ig.parent_item_group    AS parent_group,
            ig.is_group,
            -- Add level calculation
            CASE
                WHEN ig.parent_item_group IS NULL THEN 0
                WHEN parent_ig.parent_item_group IS NULL THEN 1
                WHEN grandparent_ig.parent_item_group IS NULL THEN 2
                WHEN great_grandparent_ig.parent_item_group IS NULL THEN 3
                ELSE 4
            END AS level,
            i.name                  AS item_code,
            i.item_name,
            i.description,
            i.stock_uom,
            i.standard_rate,
            i.disabled
        FROM `tabPOS Profile` pp
        JOIN `tabPOS Item Group` ppg
            ON ppg.parent = pp.name
        JOIN `tabItem Group` ig
            ON ig.name = ppg.item_group
        -- Recursive joins for hierarchy levels
        LEFT JOIN `tabItem Group` parent_ig
            ON parent_ig.name = ig.parent_item_group
        LEFT JOIN `tabItem Group` grandparent_ig
            ON grandparent_ig.name = parent_ig.parent_item_group
        LEFT JOIN `tabItem Group` great_grandparent_ig
            ON great_grandparent_ig.name = grandparent_ig.parent_item_group
        -- Include all child groups in hierarchy
        LEFT JOIN `tabItem Group` child_groups
            ON child_groups.parent_item_group = ig.name
            OR child_groups.parent_item_group IN (
                SELECT name FROM `tabItem Group`
                WHERE parent_item_group = ig.name
            )
        LEFT JOIN `tabItem` i
            ON i.item_group = COALESCE(child_groups.name, ig.name)
            AND i.disabled = 0
        WHERE pp.disabled = 0 AND pp.name = %s
        ORDER BY level, ig.item_group_name, i.item_name
        """,
        (session.pos_profile,),
        as_dict=True,
    )

    if not rows:
        return {"ok": False, "message": "No items found for POS Profile"}

    # Use the build_group_tree function we created earlier
    hierarchy = build_group_tree_optimized(rows)

    return {
        "ok": True,
        "pos_profile": session.pos_profile,
        "groups": hierarchy
    }

@frappe.whitelist()
def get_pos_item_hierarchy():
    """
    API endpoint wrapper for item_list function.
    """
    try:
        return item_list()
    except Exception as e:
        frappe.log_error(f"Failed to get POS item hierarchy: {str(e)}", "POS Item Hierarchy Error")
        return {
            "ok": False,
            "message": str(e)
        }
