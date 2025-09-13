DELIMITER $$
DROP procedure IF EXISTS inventory_availability_check  $$
CREATE PROCEDURE inventory_availability_check (
    IN p_property VARCHAR(140),
    IN p_date_from int(8),
    IN p_date_to int(8),
    IN p_room_types TEXT,
    IN p_room_categories TEXT
)
BEGIN
    IF p_property IS NULL OR p_property = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Property is required';
    END IF;
    IF p_date_from > p_date_to OR LENGTH(p_date_from) != 8 OR LENGTH(p_date_to) != 8 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Date From must be earlier than Date To And Both Must Be 8 DIGITS';
    END IF;
    -- Clean input params
    SET p_room_types = NULLIF(TRIM(p_room_types), '');
    SET p_room_categories = NULLIF(TRIM(p_room_categories), '');

    WITH rooms AS (
        SELECT r.room_type, r.name
        FROM v_room r
        WHERE r.property = p_property
          AND (p_room_types IS NULL OR FIND_IN_SET(r.room_type, p_room_types))
        AND (p_room_categories IS NULL OR FIND_IN_SET(r.room_category, p_room_categories))
    ),
    room_totals AS (
        SELECT r.room_type, COUNT(r.name) AS total_rooms
        FROM rooms r
        GROUP BY r.room_type
    ),
    occupied AS (
        SELECT r.room_type, i.room
        FROM inventory i
        INNER JOIN rooms r ON i.room = r.name
        WHERE (i.physical_status = 1 OR i.ooo_status > 0)
          AND i.for_date >= p_date_from
          AND i.for_date < p_date_to
        GROUP BY i.room, r.room_type
    ),
    occ_totals AS (
        SELECT o.room_type, COUNT(o.room) AS total_occupied
        FROM occupied o
        GROUP BY o.room_type
    )
    SELECT
      r.room_type,
      (r.total_rooms - COALESCE(o.total_occupied, 0)) AS available
    FROM room_totals r
        LEFT JOIN occ_totals o ON r.room_type = o.room_type
END$$
DROP procedure IF EXISTS upsert_inventory_status$$
CREATE PROCEDURE `upsert_inventory_status` (
  IN p_room VARCHAR(140),
  IN p_user VARCHAR(140),
  IN p_date_from INT,
  IN p_date_to INT,
  IN p_physical_status INT,
  IN p_room_status INT,
  IN p_hk_status INT,
  IN p_service_status INT ,
  IN p_ooo_status INT ,
  IN p_ooo_reason TEXT
) BEGIN
INSERT INTO
  inventory (
    room,
    for_date,
    physical_status,
    room_status,
    hk_status,
    service_status,
    ooo_status
  )
SELECT
  p_room AS room,
  d.for_date,
  p_physical_status,
  p_room_status,
  p_hk_status,
  p_service_status,
  p_ooo_status
FROM
  dim_date d
WHERE
  d.for_date BETWEEN p_date_from AND p_date_to  ON DUPLICATE KEY
UPDATE
  physical_status = COALESCE(
    VALUES
      (physical_status),
     physical_status
  ),
  hk_status = COALESCE(
    VALUES
      (hk_status),
      physical_status
  ),
  room_status = COALESCE(
    VALUES
      (room_status),
      room_status
  ),
  service_status = COALESCE(
    VALUES
      (service_status),
      room_status
  ),
  ooo_status = COALESCE(
    VALUES
      (ooo_status),
      room_status
  );

  INSERT INTO inventory_log (
    room,
    user,
    reason,
    from_date,
    to_date,
    hk_status,
    room_status,
    ooo_status,
    ooo_reason,
    physical_status,
    service_status
  )
  VALUES (
    p_room,
    p_user,
    'Status Update',
    p_date_from,
    p_date_to,
    p_hk_status,
    p_room_status,
    p_ooo_status,
    p_ooo_reason,
    p_physical_status,
    p_service_status
  );
END$$
DELIMITER ;
