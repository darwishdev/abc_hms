
DELIMITER ;;
CREATE OR REPLACE PROCEDURE `seed_room_type_rate`(
    IN p_date_from INT,
    IN p_date_to   INT
)
BEGIN
    INSERT INTO room_type_rate (
        room_type,
        rate_code,
        rate,
        for_date
    )
    SELECT
        b.room_type,
        b.parent AS rate_code,
        b.base_price,
        d.for_date
    FROM `tabRate Code Room Type` b
    JOIN dim_date d
      ON d.for_date BETWEEN p_date_from AND p_date_to
    WHERE b.base_price > 0
    ON DUPLICATE KEY UPDATE
        rate = VALUES(rate);
END ;;
DELIMITER ;

DELIMITER ;;
CREATE OR REPLACE PROCEDURE `room_availability_list`(
  IN p_property VARCHAR(255),
  IN p_from DATE,
  IN p_to DATE,
  IN p_room_category VARCHAR(255),
  IN p_room_type VARCHAR(255)
)
BEGIN
DROP TEMPORARY TABLE IF EXISTS temp_reservations;
  -- Cleanup any leftovers
DROP TEMPORARY TABLE IF EXISTS
  temp_rooms;

DROP TEMPORARY TABLE IF EXISTS
  temp_dates;

DROP TEMPORARY TABLE IF EXISTS
  temp_room_details;

DROP TEMPORARY TABLE IF EXISTS
  temp_room_types;

DROP TEMPORARY TABLE IF EXISTS
  temp_room_categories;

-- ===============================================================
-- temp_rooms: filtered rooms
-- ===============================================================
CREATE TEMPORARY TABLE
  temp_rooms AS
SELECT
  rc.property_name,
  rt.room_category,
  rt.name AS room_type,
  r.name AS room_name
FROM
  `tabRoom Type` rt
  JOIN `tabRoom` r ON rt.name = r.room_type
  JOIN `tabRoom Category` rc ON rt.room_category = rc.name
WHERE
  rt.room_category = COALESCE(p_room_category, rt.room_category)
  AND rt.pay_master = 0
  AND rt.name = COALESCE(p_room_type, rt.name)
  AND rc.property_name = COALESCE(p_property, rc.property_name);

-- ===============================================================
-- temp_dates: the date range
-- ===============================================================
CREATE TEMPORARY TABLE
  temp_dates AS
SELECT
  date_actual,
  for_date
FROM
  dim_date
WHERE
  date_actual BETWEEN p_from AND p_to
ORDER BY
  date_actual;
-- ===============================================================
-- temp_reservations: the reservations with room within the data range date range
-- ===============================================================
CREATE TEMPORARY TABLE
  temp_reservations AS
SELECT rd.room , rd.for_date from reservation_date rd
  join temp_dates d on rd.for_date = d.for_date
  join temp_rooms r on rd.room = r.room_name;

-- ===============================================================
-- ROOM-LEVEL: JSON details per room per date + per-room aggregates
-- ===============================================================
CREATE TEMPORARY TABLE
  temp_room_details AS
SELECT
  t.room_category,
  t.room_type,
  t.room_name AS room,
  CAST(
    JSON_ARRAYAGG(
      JSON_OBJECT(
        'date',
        d.date_actual,
        'room_status',
        rd.room_status,
        'out_of_order_status',
        rd.out_of_order_status,
        'out_of_order_reason',
        rd.out_of_order_reason,
        'guest_service_status',
        rd.guest_service_status,
        'in_house',
        (r.room is not null)
      )
      ORDER BY
        d.date_actual
    ) AS CHAR CHARACTER SET utf8mb4
  ) AS details
FROM
  v_room_date rd
  JOIN temp_dates d ON rd.for_date = d.for_date
  JOIN temp_rooms t ON rd.room = t.room_name
  LEFT JOIN temp_reservations r ON rd.room = r.room and rd.for_date = r.for_date
GROUP BY
  t.room_category,
  t.room_type,
  t.room_name
ORDER BY
  t.room_category,
  t.room_type,
  t.room_name;

-- ===============================================================
-- ROOM-TYPE LEVEL: aggregates using SUM/COUNT (no JSON arrays)
-- ===============================================================
CREATE TEMPORARY TABLE
  temp_room_types AS
SELECT
  t.room_category,
  t.room_type,
  COUNT(DISTINCT t.room_name) AS total_rooms
FROM
  temp_rooms t
  LEFT JOIN temp_room_details rd ON rd.room = t.room_name
GROUP BY
  t.room_category,
  t.room_type
ORDER BY
  t.room_category,
  t.room_type;

-- ===============================================================
-- ROOM-CATEGORY LEVEL: aggregates across types (no JSON arrays)
-- ===============================================================
CREATE TEMPORARY TABLE
  temp_room_categories AS
SELECT
  rt.room_category,
  COUNT(DISTINCT rt.room_type) AS total_room_types,
  SUM(rt.total_rooms) AS total_rooms
FROM
  temp_room_types rt
GROUP BY
  rt.room_category
ORDER BY
  rt.room_category;

-- ===============================================================
-- RETURN THE THREE RESULT SETS
-- ===============================================================
-- 1) Room categories: aggregated numeric fields (no JSON)
SELECT
  rc.room_category,
  rc.total_room_types,
  rc.total_rooms
FROM
  temp_room_categories rc;

-- 2) Room types: aggregated numeric fields (no JSON), include redundant room_category
SELECT
  rt.room_category,
  rt.room_type,
  rt.total_rooms
FROM
  temp_room_types rt;

-- 3) Room-level: per room JSON details for each date
SELECT
  rd.room_category,
  rd.room_type,
  rd.room,
  rd.details,
  p_from AS date_from,
  p_to AS date_to
FROM
  temp_room_details rd
ORDER BY
  rd.room_category,
  rd.room_type,
  rd.room;


SELECT * FROM temp_reservations;

-- ===============================================================
-- Cleanup temp tables
-- ===============================================================
DROP TEMPORARY TABLE IF EXISTS
  temp_room_categories;

DROP TEMPORARY TABLE IF EXISTS
  temp_room_types;

DROP TEMPORARY TABLE IF EXISTS
  temp_room_details;

DROP TEMPORARY TABLE IF EXISTS
  temp_dates;

DROP TEMPORARY TABLE IF EXISTS
  temp_rooms;
DROP TEMPORARY TABLE IF EXISTS temp_reservations;

END ;;
DELIMITER ;

DELIMITER ;;
CREATE OR REPLACE PROCEDURE `room_date_upsert`(
  IN p_rooms_list JSON, -- array of room names as JSON: '["1001","3001"]'
  IN p_from_date Date,
  IN p_to_date Date,
  IN p_house_keeping_status INT,
  IN p_room_status INT,
  IN p_guest_service_status INT,
  IN p_out_of_order_status INT,
  IN p_out_of_order_reason TEXT,
  IN p_persons INT
)
BEGIN
INSERT INTO
  room_date (
    room,
    for_date,
    house_keeping_status,
    room_status,
    guest_service_status,
    out_of_order_status,
    out_of_order_reason,
    persons
  )
SELECT
  jt.room,
  d.for_date,
  p_house_keeping_status,
  p_room_status,
  p_guest_service_status,
  p_out_of_order_status,
  p_out_of_order_reason,
  p_persons
FROM
  JSON_TABLE(
    p_rooms_list,
    "$[*]" COLUMNS (room VARCHAR(50) PATH "$")
  ) AS jt
JOIN dim_date d on d.date_actual BETWEEN p_from_date and p_to_date
ON DUPLICATE KEY
UPDATE
  house_keeping_status = COALESCE(
    VALUES
      (house_keeping_status),
      house_keeping_status,
      0
  ),
  room_status = COALESCE(
    VALUES
      (room_status),
      room_status,
      0
  ),
  guest_service_status = COALESCE(
    VALUES
      (guest_service_status),
      guest_service_status,
      0
  ),
  out_of_order_status = COALESCE(
    VALUES
      (out_of_order_status),
      out_of_order_status,
      0
  ),
  out_of_order_reason = COALESCE(
    VALUES
      (out_of_order_reason),
      out_of_order_reason,
      ''
  ),
  persons = COALESCE(
    VALUES
      (persons),
      persons,
      0
  );

END ;;
DELIMITER ;
CREATE or replace VIEW v_room_date AS
SELECT
  rd.room,
  rd.for_date,
  r.room_type,
  r.hk_section,
  coalesce(rd.persons , 'N/A') persons,
  coalesce(rd.out_of_order_reason , 'N/A') out_of_order_reason,
  hks.lookup_key AS house_keeping_status,
  rs.lookup_key AS room_status,
  oos.lookup_key AS out_of_order_status,
  gss.lookup_key AS guest_service_status
FROM
  room_date rd
  JOIN tabRoom r on rd.room = r.name
  JOIN
  room_date_lookup hks ON hks.lookup_type = 'house_keeping_status' AND hks.lookup_value = COALESCE(rd.house_keeping_status, 0)
  JOIN
  room_date_lookup rs ON rs.lookup_type = 'room_status' AND rs.lookup_value = COALESCE(rd.room_status, 0)
  JOIN
  room_date_lookup oos ON oos.lookup_type = 'ooo_status' AND oos.lookup_value = COALESCE(rd.out_of_order_status, 0)
  JOIN
  room_date_lookup gss ON gss.lookup_type = 'service_status' AND gss.lookup_value = COALESCE(rd.guest_service_status, 0);
