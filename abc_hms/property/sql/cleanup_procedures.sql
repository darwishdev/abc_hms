DELIMITER $$
DROP PROCEDURE IF EXISTS property_tables_cleanup$$
CREATE OR REPLACE PROCEDURE property_tables_cleanup()
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
-- TRUNCATE TABLE tabReservation;
TRUNCATE TABLE `tabGL Entry`;
UPDATE `tabProperty Setting` SET business_date = '2025-08-07';
END $$


DELIMITER ;
