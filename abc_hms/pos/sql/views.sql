
DROP VIEW IF EXISTS v_item_defaults;
drop view if exists restaurant_menu;
drop view if exists cashier_device_printers_map;
DROP VIEW IF  EXISTS restaurant_areas;
drop view if  exists pos_invoice_view;
CREATE VIEW v_item_defaults AS
SELECT
    i.name             AS item_code,
    i.item_name,
    i.description,
    i.stock_uom,
    i.standard_rate,
    i.item_group,
    igd.income_account,
    igd.selling_cost_center AS cost_center
FROM `tabItem` i
LEFT JOIN `tabItem Default` igd
  ON igd.parent = i.item_group
  AND igd.parenttype = 'Item Group'
  AND igd.parentfield = 'item_group_defaults';
--
-- CREATE VIEW IF NOT EXISTS restaurant_areas as
-- WITH restaurant_areas AS (
--     SELECT a.restaurant, a.name area, t.name table_code, t.display_name,
--            a.sequance as area_seq, t.sequance as table_seq
--     FROM `tabRestaurant Area` a
--     JOIN `tabRestaurant Table` t ON a.name = t.restaurant_area
--     WHERE restaurant = 'Beach Restaurant'
-- )
-- SELECT
--     area,
--     JSON_ARRAYAGG(
--         JSON_OBJECT(
--             'table_code', table_code,
--             'display_name', display_name
--         )
--         ORDER BY table_seq  -- This maintains the order
--     ) AS area_tables
-- FROM restaurant_areas
-- GROUP BY area, area_seq
-- ORDER BY area_seq;



create view if not exists restaurant_menu as
WITH RECURSIVE menu AS (
    -- Base case: Get top-level item groups from the restaurant menu
    SELECT m.name AS menu_name,
           mi.item_group,
           g.parent_item_group,
           g.is_group,
           1 AS level,
           CAST(mi.item_group AS CHAR(1000)) AS hierarchy_path
    FROM `tabRestaurant Menu` m
    JOIN `tabRestaurant Menu Item Group` mi ON m.name = mi.parent
    JOIN `tabItem Group` g ON mi.item_group = g.name

    UNION ALL

    -- Recursive case: Get child item groups
    SELECT menu.menu_name,
           ig.name AS item_group,
           ig.parent_item_group,
           ig.is_group,
           menu.level + 1 AS level,
           CONCAT(menu.hierarchy_path, ' > ', ig.name) AS hierarchy_path
    FROM menu
    JOIN `tabItem Group` ig ON menu.item_group = ig.parent_item_group
    WHERE menu.is_group = 1  -- Only continue recursion for groups
),

-- Get all item groups in the hierarchy
all_groups AS (
    SELECT DISTINCT menu_name, item_group, is_group, level, hierarchy_path
    FROM menu
)

-- Final query: Join with items and prices for leaf groups only
SELECT
    ag.menu_name,
    ag.level,
    ag.hierarchy_path,
    ig.name AS group_name,
    i.name AS item_name,
    i.image AS item_image,
    COALESCE(i.print_class, ig.print_class) AS print_class,
    ip.price_list_rate,
    ip.uom
FROM all_groups ag
JOIN `tabItem Group` ig ON ag.item_group = ig.name
JOIN `tabItem` i ON ig.name = i.item_group
JOIN `tabItem Price` ip ON i.name = ip.item_code
WHERE ag.is_group = 0  -- Only show items from leaf groups (non-group items)
ORDER BY ag.menu_name, ag.level, ig.name, i.name;


create view if not exists cashier_device_printers_map as
WITH cashier_device_data AS (
    SELECT DISTINCT
        d.name AS cashier_device_name,
        papp.preparation_printer,
        pppc.print_class,
        pp_backup.name backup_printer,
        pp_backup.port_number backup_printer_port,
        pp_backup.ip_adress backup_printer_ip,
        pp.ip_adress print_ip,
        pp.port_number printer_port
    FROM `tabCashier Device` d
    JOIN `tabCasheir Device Production Area` pa ON d.name = pa.parent
    JOIN `tabProduction Area Preparation Printer` papp ON pa.production_area = papp.parent
    JOIN `tabPreparation Printer` pp ON pp.name = papp.preparation_printer
    JOIN `tabPreparation Printer` pp_backup ON pp.fallback_printer = pp_backup.name
    JOIN `tabPreparation Printer Print Class` pppc ON papp.preparation_printer = pppc.parent
)

SELECT
    cashier_device_name,
        JSON_OBJECTAGG(
            print_class,
            JSON_OBJECT(
                'preparation_printer', preparation_printer,
                'connection_info', CONCAT(print_ip, ':', printer_port),
                'backup_printer', backup_printer,
                'backup_connection_info', CONCAT(backup_printer_ip, ':', backup_printer_port)
            )
        ) as print_class
FROM cashier_device_data
GROUP BY cashier_device_name
ORDER BY cashier_device_name;

create view if not exists pos_invoice_view as
select
p.amount payment_amount,
p.mode_of_payment,
i.name invoice_name,
i.total invoice_total,
i.table_number,
i.paid_amount,
i.status,
i.room_number,
i.pos_session,
i.total_qty,
it.item_code,
it.name item_name,
ii.rate,
ii.amount,
ii.item_group,
ii.uom ,
ii.discount_percentage ,
ii.discount_amount ,
ii.distributed_discount_amount,
COALESCE(it.print_class , ig.print_class) print_class
FROM `tabPOS Invoice` i
 join `tabPOS Invoice Item` ii on ii.parent = i.name
 join `tabItem Group` ig on ii.item_group = ig.name
 join `tabSales Invoice Payment` p on p.parent = i.name
join `tabItem` it on ii.item_code = it.name;

DROP VIEW IF EXISTS v_pos_profile_catalog;
CREATE VIEW v_pos_profile_catalog AS
SELECT
    pp.name                 AS pos_profile,
    ppg.parent              AS pos_profile_name,
    ig.name                 AS item_group_id,
    ig.item_group_name      AS item_group_name,
    ig.parent_item_group    AS parent_group,
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
LEFT JOIN `tabItem` i
    ON i.item_group = ig.name
WHERE pp.disabled = 0;



select * from v_pos_profile_catalog;
