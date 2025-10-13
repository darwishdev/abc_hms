DELIMITER $$
DROP procedure IF EXISTS inventory_availability_check  $$
-- CREATE OR REPLACE PROCEDURE inventory_availability_check (
--     IN p_property VARCHAR(140),
--     IN p_date_from int(8),
--     IN p_date_to int(8),
--     IN p_room_types TEXT,
--     IN p_room_categories TEXT
-- )
-- BEGIN
--     IF p_property IS NULL OR p_property = '' THEN
--         SIGNAL SQLSTATE '45000'
--             SET MESSAGE_TEXT = 'Property is required';
--     END IF;
--     IF p_date_from > p_date_to OR LENGTH(p_date_from) != 8 OR LENGTH(p_date_to) != 8 THEN
--         SIGNAL SQLSTATE '45000'
--             SET MESSAGE_TEXT = 'Date From must be earlier than Date To And Both Must Be 8 DIGITS';
--     END IF;
--     -- Clean input params
--     SET p_room_types = NULLIF(TRIM(p_room_types), '');
--     SET p_room_categories = NULLIF(TRIM(p_room_categories), '');
--
-- WITH dates as(
--   select for_date from dim_date where for_date >= p_date_from and for_date < p_date_to
-- ),
--
--   rooms AS (
--         SELECT r.room_type, COUNT(r.name) total_rooms
--         FROM tabRoom r
--         join `tabRoom Type` rt on r.room_type = rt.name  and rt.pay_master is false
--         join `tabRoom Category` rc on rt.room_category = rc.name
--         WHERE rc.property_name = p_property
--         AND (p_room_categories IS NULL OR FIND_IN_SET(rc.name, p_room_categories))
--         AND (p_room_types IS NULL OR FIND_IN_SET(r.room_type, p_room_types))
--         GROUP BY r.room_type
--     ), ooo_rooms as (
--         select r.room_type , count(r.name) total_ooo
--         from room_date rd
--         join dates d
--         on rd.for_date = d.for_date
--         join tabRoom r
--         on r.name = rd.room
--         WHERE rd.out_of_order_status > 0
--         GROUP BY r.room_type
--     ),reserved_rooms as (
--         select rd.room_type , count(rd.for_date) total_reserved
--         from reservation_date rd
--         join dates d
--         on rd.for_date = d.for_date
--         GROUP BY rd.room_type
--     ),
--   resp as(
--   SELECT
--       r.room_type,
--       r.total_rooms  total_rooms,
--       COALESCE(ooo.total_ooo, 0)  total_ooo,
--       COALESCE(rr.total_reserved, 0)  total_reserved,
--       (r.total_rooms - COALESCE(rr.total_reserved, 0) - COALESCE(ooo.total_ooo, 0)) AS available
--
--     FROM rooms r
--     LEFT JOIN  ooo_rooms ooo on r.room_type = ooo.room_type
--     LEFT JOIN  reserved_rooms rr on r.room_type = rr.room_type
--     ) select * from resp;
-- END$$
--

CREATE OR REPLACE PROCEDURE inventory_availability_check (
    IN p_property VARCHAR(140),
    IN p_date_from date,
    IN p_date_to date,
    IN p_room_types TEXT,
    IN p_room_categories TEXT
)
BEGIN
    IF p_property IS NULL OR p_property = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Property is required';
    END IF;
    IF p_date_from > p_date_to  THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Date From must be earlier than Date To And Both Must Be 8 DIGITS';
    END IF;
    -- Clean input params
    SET p_room_types = NULLIF(TRIM(p_room_types), '');
    SET p_room_categories = NULLIF(TRIM(p_room_categories), '');

WITH dates as(
  select for_date from dim_date where for_date >= p_date_from and for_date < p_date_to
),

  rooms AS (
        SELECT r.room_type, COUNT(r.name) total_rooms
        FROM tabRoom r
        join `tabRoom Type` rt on r.room_type = rt.name  and rt.pay_master is false
        join `tabRoom Category` rc on rt.room_category = rc.name
        WHERE rc.property_name = p_property
        AND (p_room_categories IS NULL OR FIND_IN_SET(rc.name, p_room_categories))
        AND (p_room_types IS NULL OR FIND_IN_SET(r.room_type, p_room_types))
        GROUP BY r.room_type
    ), ooo_rooms as (
        select r.room_type , count(r.name) total_ooo
        from room_date rd
        join dates d
        on rd.for_date = d.for_date
        join tabRoom r
        on r.name = rd.room
        WHERE rd.out_of_order_status > 0
        GROUP BY r.room_type
    ),reserved_rooms as (
        select rd.room_type , count(rd.for_date) total_reserved
        from reservation_date rd
        join dates d
        on rd.for_date = d.for_date
        GROUP BY rd.room_type
    ),
  resp as(
  SELECT
      r.room_type,
      r.total_rooms  total_rooms,
      COALESCE(ooo.total_ooo, 0)  total_ooo,
      COALESCE(rr.total_reserved, 0)  total_reserved,
      (r.total_rooms - COALESCE(rr.total_reserved, 0) - COALESCE(ooo.total_ooo, 0)) AS available

    FROM rooms r
    LEFT JOIN  ooo_rooms ooo on r.room_type = ooo.room_type
    LEFT JOIN  reserved_rooms rr on r.room_type = rr.room_type
    ) select * from resp;
END$$

DROP PROCEDURE IF EXISTS room_type_availability_list;
CREATE OR REPLACE PROCEDURE room_type_availability_list(
    IN p_from DATE,
    IN p_to DATE,
    IN p_room_category VARCHAR(255),
    IN p_room_type VARCHAR(255)
)
BEGIN
    WITH
    dates_seq AS (
        SELECT
            date_actual,
            for_date
        FROM
            dim_date
        WHERE
            date_actual BETWEEN p_from AND p_to
    ),
    room_totals AS (
        SELECT
            rt.room_category,
            r.room_type,
            COUNT(r.name) total_rooms
        FROM
            `tabRoom Type` rt
            JOIN `tabRoom` r ON rt.name = r.room_type
        WHERE
            rt.room_category = COALESCE(p_room_category, rt.room_category)
            AND r.room_type = COALESCE(p_room_type, r.room_type)
        GROUP BY
            rt.room_category,
            r.room_type
    ),
    room_statuses AS (
        SELECT
            r.room_type,
            rd.for_date,
            SUM(
                CASE
                    WHEN rd.out_of_order_status > 0 THEN 1
                    ELSE 0
                END
            ) AS total_ooo
        FROM
            room_date rd
            JOIN dates_seq d ON rd.for_date = d.for_date
            JOIN tabRoom r ON rd.room = r.name
        GROUP BY
            r.room_type,
            rd.for_date
    ),
    reservations AS (
        SELECT
            rd.room_type,
            rd.for_date,
            COUNT(rd.room_type) total_occupied
        FROM
            reservation_date rd
            JOIN dates_seq d ON rd.for_date = d.for_date
        GROUP BY
            rd.room_type,
            rd.for_date
    ),
    resp AS (
        SELECT
            rt.room_category,
            rt.room_type,
            rt.total_rooms,
            JSON_OBJECT(
                'Free To Sell',
                JSON_ARRAYAGG(
                    JSON_OBJECT(
                        'date',
                        d.date_actual,
                        'value',
                        (
                            rt.total_rooms - COALESCE(rs.total_ooo, 0) - COALESCE(r.total_occupied, 0)
                        )
                    )
                ),
                'OOO',
                JSON_ARRAYAGG(
                    JSON_OBJECT(
                        'date',
                        d.date_actual,
                        'value',
                        COALESCE(rs.total_ooo, 0)
                    )
                ),
                'OOC',
                JSON_ARRAYAGG(
                    JSON_OBJECT(
                        'date',
                        d.date_actual,
                        'value',
                        COALESCE(r.total_occupied, 0)
                    )
                )
            ) details
        FROM
            dates_seq d
            CROSS JOIN room_totals rt
            LEFT JOIN room_statuses rs ON rt.room_type = rs.room_type
                AND rs.for_date = d.for_date
            LEFT JOIN reservations r ON r.room_type = rt.room_type
                AND r.for_date = d.for_date
        GROUP BY
            rt.room_category,
            rt.room_type,
            rt.total_rooms
    )
    SELECT
        r.room_category,
        JSON_ARRAYAGG(
            JSON_OBJECT(
                'room_type', r.room_type,
                'total_rooms', r.total_rooms,
                'details', r.details
            )
        ) data
    FROM resp r
    GROUP BY r.room_category;
END $$
DELIMITER ;














