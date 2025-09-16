DELIMITER $$
DROP PROCEDURE IF EXISTS seed_room_rates$$
CREATE PROCEDURE seed_room_rates(
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
END$$
DELIMITER ;
