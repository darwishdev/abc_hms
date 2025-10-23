DELIMITER ;;
CREATE OR REPLACE PROCEDURE reservation_inouse_invoices(IN p_current_date INT)
BEGIN
    WITH reservations AS (
        SELECT
            r.reservation_status,
            r.name reservation,
            (r.rate_code_rate * r.exchange_rate) rate_code_rate,
            r.room_type,
            r.exchange_rate,
            r.arrival,
            r.market_segment,
            r.discount_percent,
            r.nights,
            r.discount_amount,
            r.guest customer,
            r.departure,
            r.rate_code,
            (r.base_rate * r.exchange_rate) base_rate,
            r.property,
            p.company,
            CONCAT('F-', r.name, '-000001') folio,
            rc.currency,
            r.adults number_of_guests,
            p_current_date for_date,
            CONCAT('PI-F-', r.name, '-', p_current_date, '-.####') naming_series
        FROM `tabReservation` r
        JOIN `tabRate Code` rc ON r.rate_code = rc.name
        JOIN `tabProperty` p ON r.property = p.name
  WHERE date_to_int(r.arrival) <= p_current_date and
  date_to_int(r.departure) >= p_current_date
        and r.reservation_status = 'In House'
    ),
    pkg_items AS (
        SELECT
            r.reservation,
            0 pkgs_rate,
            pkgp.item_name,
            pkgp.item_code,
            pkgp.item_description,
            pkgp.uom stock_uom,
            pkgp.currency,
            pkgp.price_list_rate rate,
            1 qty,
            pkgp.price_list_rate  amount,
            p_current_date for_date,
            CONCAT(r.folio, '-W-001') folio_window
        FROM reservations r
        JOIN `tabRate PKG` rp ON r.rate_code = rp.parent
        JOIN `tabProperty Setting` s ON r.property = s.name
        JOIN `tabItem Price` pkgp ON pkgp.item_name = rp.pkg
            AND pkgp.price_list = s.default_price_list
            AND pkgp.valid_from <= r.arrival
            AND pkgp.valid_upto >= r.departure
        where date_to_int(r.departure) > p_current_date
 )     ,
 room_item AS (
        SELECT
            r.reservation,
            IF ((r.rate_code_rate - SUM(i.amount)) > 0 ,  r.rate_code_rate - SUM(i.amount) , 0) price_before_discount,
            SUM(i.amount) pkgs_rate,
            CONCAT(r.room_type, '-', r.rate_code) item_name,
            CONCAT(r.room_type, '-', r.rate_code) item_code,
            CONCAT(r.room_type, '-', r.rate_code) item_description,
            'Nos' stock_uom,
            id.income_account,
            r.currency,
            r.base_rate rate,
            1 qty,
            p_current_date for_date,
            CONCAT(r.folio, '-W-001') folio_window
        FROM reservations r
        JOIN pkg_items i ON r.reservation = i.reservation
        JOIN `tabItem Default` id ON r.market_segment = id.parent
            AND id.parenttype = 'Item Group'

        GROUP BY
            r.reservation,
            r.rate_code_rate,
            r.discount_amount,
            r.nights,
            r.room_type,
            r.rate_code,
            r.currency,
            r.rate_code_rate,
            r.base_rate
    ),room_discounts as (
      select
      reservation,
      IF((rate - pkgs_rate) > 0 , (rate - pkgs_rate), 0) rate ,
      IF((price_before_discount - rate ) > 0 , (price_before_discount - rate ), 0)  discount_amount
      FROM room_item
    ),
      prepared_room_item as (
      select
      r.reservation,
      d.rate,
      d.rate amount,
      d.discount_amount,
      (d.discount_amount * 100 / r.price_before_discount) discount_percentage,
      -- r.reservation,
      r.price_before_discount,
      r.pkgs_rate,
      r.item_name,
      r.item_code,
      r.item_description,
      r.stock_uom,
      r.income_account,
      r.currency,
      r.qty,
      p_current_date for_date,
      r.folio_window
      from room_item r join room_discounts d on r.reservation = d.reservation
      ),
    items AS (
        SELECT
            NULL income_account,
            reservation,
            0 discount_amount,
            0 discount_percentage,
            item_name,
            item_code,
            item_description,
            stock_uom,
            currency,
            rate,
            rate price_list_rate,
            qty,
            amount,
            p_current_date for_date,
            folio_window
        FROM pkg_items

        UNION

        SELECT
            income_account,
            reservation,
            discount_amount,
            discount_percentage,
            item_name,
            item_code,
            item_description,
            'Nos' stock_uom,
            currency,
             rate,
            price_before_discount price_list_rate,
            1 qty,
            amount,
            p_current_date for_date,
            folio_window
        FROM prepared_room_item
    )  ,resp as (
    SELECT
        SUM(i.amount) total_amount,
        r.rate_code_rate,
        r.base_rate,
        'Main' pos_profile,
        r.customer,
        r.rate_code,
        r.discount_percent,
        r.property,
        r.company,
        r.folio,
        r.currency,
        r.number_of_guests,
        r.for_date,
        r.naming_series,
        JSON_ARRAYAGG(JSON_OBJECT(
            'item_name', i.item_name,
            'price_list_rate', i.price_list_rate,
            'rate', i.rate,
            'discount_amount', i.discount_amount,
            'income_account', i.income_account,
            'for_date', p_current_date,
            'item_code', i.item_code,
            'item_description', i.item_description,
            'stock_uom', i.stock_uom,
            'discount_percentage', i.discount_percentage,
            'qty', 1,
            'amount', i.amount,
            'folio_window', i.folio_window)) items
    FROM reservations r
    JOIN items i ON r.reservation = i.reservation
    GROUP BY
        r.reservation,
        r.customer,
        r.rate_code,
        r.property,
        r.company,
        r.folio,
        r.discount_percent,
        r.rate_code_rate,
        r.currency,
        r.number_of_guests,
        r.for_date,
        r.naming_series)
      SELECT * FROM resp;
END;;
DELIMITER ;
