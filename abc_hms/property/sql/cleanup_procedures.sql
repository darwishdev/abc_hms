DELIMITER $$
DROP PROCEDURE IF EXISTS property_tables_cleanup$$
CREATE PROCEDURE property_tables_cleanup()
BEGIN
TRUNCATE TABLE `tabPOS Opening Enry`;
TRUNCATE TABLE `tabPOS Closing Enry`;
TRUNCATE TABLE `tabSales Invoice Item`;
TRUNCATE TABLE `tabSales Invoice Payment`;
TRUNCATE TABLE `tabSales Invoice`;
TRUNCATE TABLE `tabPOS Invoice Item`;
TRUNCATE TABLE `tabPOS Invoice`;
TRUNCATE TABLE `tabFolio Window`;
TRUNCATE TABLE tabFolio;
TRUNCATE TABLE room_date;
TRUNCATE TABLE reservation_date;
TRUNCATE TABLE tabReservation;
UPDATE `tabProperty Setting` SET business_date = '2025-08-07';
END$$

DELIMITER ;
