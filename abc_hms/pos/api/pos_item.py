import frappe
from collections import defaultdict
from abc_pos.api.device_auth import device_protected  # adjust import to your path
def build_group_tree(rows, parent=None):
    """
    Build a recursive nested tree structure from flat SQL rows.

    Args:
        rows: List of dictionaries from SQL query
        parent: Parent group name (None for root level, which will be "All Item Groups")

    Returns:
        List of nested group dictionaries with items and sub-groups
    """
    tree = []

    # If parent is None, find the actual root groups from data
    if parent is None:
        # Find groups that appear as parent_group but not as item_group_name
        all_groups = {row['item_group_name'] for row in rows}
        all_parents = {row['parent_group'] for row in rows if row['parent_group']}

        # Root groups are parents that don't appear as groups themselves
        # OR the most common parent_group (like "All Item Groups")
        parent_counts = {}
        for row in rows:
            if row['parent_group']:
                parent_counts[row['parent_group']] = parent_counts.get(row['parent_group'], 0) + 1

        # Use the most common parent as root, or find true roots
        if parent_counts:
            root_parent = max(parent_counts, key=parent_counts.get)
            parent = root_parent

    # Get unique groups at this level
    groups_at_level = {}
    items_by_group = {}

    # First pass: organize data by groups and collect items
    for row in rows:
        group_name = row['item_group_name']
        parent_group = row['parent_group']

        # Check if this group belongs at current level
        if parent_group == parent:
            # Initialize group if not seen before
            if group_name not in groups_at_level:
                groups_at_level[group_name] = {
                    'item_group_id': row['item_group_id'],
                    'item_group_name': group_name,
                    'parent_group': parent_group,
                    'items': [],
                    'sub_groups': []
                }
                items_by_group[group_name] = []

            # Add item to this group if it exists (item_code is not NULL)
            if row['item_code'] is not None:
                item = {
                    'item_code': row['item_code'],
                    'item_name': row['item_name'],
                    'description': row['description'],
                    'stock_uom': row['stock_uom'],
                    'standard_rate': float(row['standard_rate']) if row['standard_rate'] else 0.0,
                    'disabled': row['disabled']
                }
                items_by_group[group_name].append(item)

    # Second pass: build tree with recursion
    for group_name, group_data in groups_at_level.items():
        # Add items to this group
        group_data['items'] = items_by_group[group_name]

        # Recursively get sub-groups
        group_data['sub_groups'] = build_group_tree(rows, parent=group_name)

        tree.append(group_data)

    return tree

@frappe.whitelist()
def pos_profile_items_list(pos_profile: str):
    """
    Return nested item group + item catalog for a POS Profile.
    Uses SQL view `v_pos_profile_catalog`.
    """
    rows = frappe.db.sql(
        """
        SELECT
            pos_profile,
            item_group_id,
            item_group_name,
            parent_group,
            item_code,
            item_name,
            description,
            stock_uom,
            standard_rate,
            disabled
        FROM v_pos_profile_catalog
        WHERE pos_profile = %s
        ORDER BY item_group_name, item_code
        """,
        (pos_profile,),
        as_dict=True,
    )

    if not rows:
        return {"ok": False, "message": f"No catalog found for profile {pos_profile}"}

    # Build nested tree (root groups = those without parent_group or parent_group = None)
    tree = build_group_tree(rows, parent=None)

    return {
        "ok": True,
        "pos_profile": pos_profile,
        "catalog": tree
    }

# Test function to see the structure
@frappe.whitelist()
def test_pos_catalog_structure():
    """Test function to see the nested structure"""
    result = pos_profile_items_list("Main Cashier")

    def print_tree(groups, indent=0):
        """Helper to print tree structure"""
        for group in groups:
            print("  " * indent + f"GROUP: {group['item_group_name']}")

            # Print items in this group
            for item in group['items']:
                print("  " * (indent + 1) + f"ITEM: {item['item_code']} - {item['item_name']}")

            # Print sub-groups recursively
            if group['sub_groups']:
                print_tree(group['sub_groups'], indent + 1)

    if result['ok']:
        print_tree(result['catalog'])

    return result
