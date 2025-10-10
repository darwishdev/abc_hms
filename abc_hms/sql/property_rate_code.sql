
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `room_type_rate_bulk_upsert`(
  IN p_room_type varchar(114),
  IN p_rate_code varchar(114),
  IN p_rate decimal,
  IN p_date_from Date,
  IN p_date_to Date
)
BEGIN
  IF p_date_from > p_date_to THEN
    SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Date From must be earlier than Date To and both must be 8 digits (YYYYMMDD)';
  END IF;

INSERT INTO   room_type_rate (for_date,room_type,rate_code,rate)
SELECT d.for_date,p_room_type,p_rate_code,p_rate from dim_date d where d.date_actual between p_date_from and p_date_to
ON DUPLICATE KEY
UPDATE
  rate = p_rate;

END ;;
DELIMITER ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `room_type_rate_list`(
  IN p_property varchar(114),
  IN p_date_from Date,
  IN p_date_to Date,
  IN p_room_category varchar(114),
  IN p_room_types TEXT
)
BEGIN IF p_date_from > p_date_to THEN SIGNAL SQLSTATE '45000'
SET
  MESSAGE_TEXT = 'Date From must be earlier than Date To';

END IF;

SET
  p_room_types = NULLIF(TRIM(p_room_types), ''),
  p_room_category = NULLIF(TRIM(p_room_category), '');

WITH
  rate_codes_data as (
    SELECT
      rt.room_category,
      r.room_type,
      r.rate_code,
      rc.currency,
      coalesce(ce.exchange_rate, 1) exchange_rate,
      r.rate,
      d.date_actual date
    FROM
      room_type_rate r
      join `tabRate Code` rc on r.rate_code = rc.name
      JOIN `tabRoom Type` rt on rt.name = r.room_type
      JOIN dim_date d on r.for_date = d.for_date
      JOIN `tabRoom Category` c on rt.room_category = c.name
      LEFT join `tabCurrency Exchange` ce on rc.currency = ce.from_currency
    where
      d.date_actual >= p_date_from
      and d.date_actual <= p_date_to
      and rt.room_category = coalesce(p_room_category, rt.room_category)
      and c.property_name = p_property
      AND (
        p_room_types IS NULL
        OR FIND_IN_SET(r.room_type, p_room_types)
      )
  )
select
  r.room_category,
  r.room_type,
  r.rate_code,
  r.currency,
  r.exchange_rate,
  r.date,
  ROUND(r.rate, 2) base_rate,
  ROUND((r.rate * r.exchange_rate), 2) base_rate_default_currency
from
  rate_codes_data r
order by
  r.room_category,
  r.room_type,
  r.rate_code;

END ;;
DELIMITER ;
DELIMITER ;;
CREATE DEFINER=`root`@`localhost` PROCEDURE `room_type_rate_list_range`(
  IN p_property varchar(114),
  IN p_date_from date,
  IN p_date_to date,
  IN p_room_category varchar(114),
  IN p_room_rate_codes TEXT,
  IN p_room_types TEXT,
  IN p_discount_type VARCHAR(32),
  IN p_discount_percent DECIMAL(10,2),
  IN p_discount_amount DECIMAL(10,2)
)
BEGIN
  IF p_date_from > p_date_to THEN
  SIGNAL SQLSTATE '45000'
SET
  MESSAGE_TEXT = 'Date From must be earlier than Date To and both must be 8 digits (YYYYMMDD)';
END IF;

SET
  p_room_rate_codes = NULLIF(TRIM(p_room_rate_codes), ''),
  p_room_types = NULLIF(TRIM(p_room_types), '');

WITH
  rate_codes_data as (
    SELECT
      rt.room_category,
      r.room_type,
      r.rate_code,
      rc.currency,
      coalesce(ce.exchange_rate, 1) exchange_rate,
      SUM(r.rate) total_stay,
      AVG(r.rate) base_rate
    FROM
      room_type_rate r
      join `tabRate Code` rc on r.rate_code = rc.name
      JOIN `tabRoom Type` rt on rt.name = r.room_type
      JOIN `tabRoom Category` c on rt.room_category = c.name
      LEFT join `tabCurrency Exchange` ce on rc.currency = ce.from_currency
    where
      r.for_date >= p_date_from
      and r.for_date < p_date_to
      and rt.room_category = coalesce(p_room_category , rt.room_category)
      and c.property_name = p_property
      AND (
        p_room_rate_codes IS NULL
        OR FIND_IN_SET(r.rate_code, p_room_rate_codes)
      )
      AND (
        p_room_types IS NULL
        OR FIND_IN_SET(r.room_type, p_room_types)
      )
    GROUP BY
      r.room_type,
      r.rate_code,
      rc.currency,
      rt.room_category,
      ce.exchange_rate
  ) , response as (
select
  r.room_category,
  r.room_type,
  r.rate_code,
  r.currency,
  r.exchange_rate,
  coalesce(p_discount_percent , 0) discount_percent,
  IF(coalesce(p_discount_type , 'Value') = 'Value' , coalesce(p_discount_amount,0),(r.base_rate * coalesce(p_discount_percent , 0) / 100)) discount_value,
  ROUND(r.base_rate, 2) base_rate,
  ROUND(r.total_stay, 2) total_stay,
  ROUND((r.base_rate * r.exchange_rate), 2) base_rate_default_currency,
  ROUND((r.total_stay * r.exchange_rate), 2) total_stay_default_currency
from
  rate_codes_data r order by r.room_category,r.room_type,r.rate_code
  )
  select
  r.room_category,
  r.room_type,
  r.rate_code,
  r.currency,
  r.exchange_rate,
  r.base_rate,
  (r.base_rate - r.discount_value) discounted_base_rate,
  r.total_stay,
  r.base_rate_default_currency,
  (r.base_rate_default_currency - (r.discount_value * r.exchange_rate)) discounted_base_rate_default_currency,
  r.total_stay_default_currency,
  r.discount_percent,
  r.discount_value
  from response r;


END ;;
DELIMITER ;
