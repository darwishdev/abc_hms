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


DROP PROCEDURE IF EXISTS room_type_rate_list$$
CREATE PROCEDURE room_type_rate_list (
    IN p_date_from INT(8),
    IN p_date_to   INT(8),
    IN p_room_types TEXT
)
BEGIN
    -- Validate dates
    IF p_date_from > p_date_to OR LENGTH(p_date_from) != 8 OR LENGTH(p_date_to) != 8 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Date From must be earlier than Date To and both must be 8 digits (YYYYMMDD)';
    END IF;

    -- Clean input params
    SET p_room_types = NULLIF(TRIM(p_room_types), '');
    WITH rate_codes_data as (
      SELECT
        r.room_type,
        r.rate_code,
        rc.currency,
        coalesce(ce.exchange_rate , 1)  exchange_rate,
        SUM(r.rate) total_stay,
        AVG(r.rate) base_rate
          FROM
        room_type_rate r
      join  `tabRate Code` rc on r.rate_code = rc.name
      LEFT join  `tabCurrency Exchange` ce on rc.currency = ce.from_currency
      where r.for_date >= p_date_from and r.for_date < p_date_to
        AND (p_room_types IS NULL OR FIND_IN_SET(r.room_type, p_room_types))
      GROUP BY r.room_type,
        r.rate_code,
        rc.currency,
        ce.exchange_rate
      ) select
        r.room_type,
        r.rate_code,
        r.currency,
        r.exchange_rate,
        ROUND(r.base_rate , 2) base_rate,
        ROUND(r.total_stay ,2) total_stay,
        ROUND((r.base_rate * r.exchange_rate) , 2) base_rate_default_currency,
        ROUND((r.total_stay * r.exchange_rate) , 2) total_stay_default_currency
        from rate_codes_data r;
END$$

DELIMITER ;

