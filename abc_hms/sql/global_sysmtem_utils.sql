DELIMITER ;;
CREATE OR REPLACE PROCEDURE `property_tables_cleanup`()
BEGIN
UPDATE tabSeries SET current = 0 WHERE name LIKE '%CHNA%';
TRUNCATE TABLE `tabPOS Opening Entry`;
TRUNCATE TABLE `tabPOS Closing Entry`;
TRUNCATE TABLE `tabPOS Session`;
TRUNCATE TABLE `tabPOS Invoice Merge Log`;
TRUNCATE TABLE `tabPOS Closing Entry`;
TRUNCATE TABLE `tabSales Invoice Item`;
TRUNCATE TABLE `tabSales Invoice Payment`;
TRUNCATE TABLE `tabSales Invoice`;
TRUNCATE TABLE `tabPOS Invoice Item`;
TRUNCATE TABLE `tabPOS Invoice`;
TRUNCATE TABLE `tabFolio Window`;
TRUNCATE TABLE tabFolio;
TRUNCATE TABLE room_date;
TRUNCATE TABLE reservation_date;
update `tabReservation` set reservation_status = 'In House';

TRUNCATE TABLE `tabGL Entry`;
UPDATE `tabProperty Setting` SET business_date = '2025-08-07';
END ;;
DELIMITER ;
DELIMITER ;;
CREATE OR REPLACE PROCEDURE reservations_fix () BEGIN
update
  `tabReservation` r
  join `tabRate Code` rc on r.rate_code = rc.name
  join room_type_rate rtr on rtr.room_type = r.room_type
  and rtr.rate_code = r.rate_code
  and rtr.for_date = date_to_int (r.arrival)
  LEFT join `tabCurrency Exchange` ex on rc.currency = ex.from_currency
  and ex.to_currency = 'EGP'
set
  rate_code_rate = IF(rtr.rate >= r.base_rate, rtr.rate, r.base_rate),
  r.total_stay = r.nights * r.base_rate,
  r.exchange_rate = coalesce(ex.exchange_rate , 1),
  discount_amount = IF(
    rtr.rate >= r.base_rate,
    rtr.rate - r.base_rate,
    0
  ),
  discount_type = IF(rtr.rate >= r.base_rate, 'Percent', Null),
  discount_reason = IF(rtr.rate >= r.base_rate, 'Owner', Null),
  discount_percent = IF(
    rtr.rate >= r.base_rate,
    ((rtr.rate - r.base_rate) / rtr.rate * 100),
    0
  );

END;;

DELIMITER ;
