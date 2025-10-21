
DELIMITER ;;
CREATE OR REPLACE PROCEDURE `reservation_date_sync`(
    IN p_reservation VARCHAR(255),
    IN p_new_arrival DATE,
    IN p_new_departure DATE,
    IN p_new_docstatus INT,
    IN p_new_reservation_status VARCHAR(100),
    IN p_new_room_type VARCHAR(255),
    IN p_new_rate_code VARCHAR(255),
    IN p_new_room VARCHAR(255),
    IN p_new_rate_code_rate decimal(21,9),
    IN p_new_base_rate decimal(21,9),
    IN p_new_discount_type varchar(10),
    IN p_new_discount_value decimal(21,9),
    IN p_ignore_availability TINYINT(1),
    IN p_allow_room_sharing TINYINT(1)
)
proc_body: BEGIN

    DECLARE v_business_date DATE;
    DECLARE v_is_available_count TINYINT(1);
    DECLARE v_actual_room_type VARCHAR(255);
    DECLARE v_existing_reservations TEXT DEFAULT '';
    DECLARE v_occupied_room_count INT DEFAULT 0;
    DECLARE msg_text TEXT;
    DECLARE final_msg TEXT;


    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 msg_text = MESSAGE_TEXT;
        ROLLBACK;
        SET final_msg = CONCAT( 'reservation_sync: rolled back due to an error. Original: ', msg_text );
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = final_msg;
    END;

    START TRANSACTION;


    IF p_new_docstatus = 2 THEN
        DELETE FROM reservation_date WHERE reservation = p_reservation;
        COMMIT;
        LEAVE proc_body;
    END IF;


    SELECT pr.business_date
        INTO v_business_date
    FROM `tabProperty Setting` pr
    JOIN `tabReservation` r ON pr.name = r.property AND r.name = p_reservation
    LIMIT 1;


    IF p_new_arrival IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid dates: Arrival Is Required';
    END IF;
    IF p_new_departure IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid dates: Departure Is Required';
    END IF;
    IF p_new_arrival > p_new_departure THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid dates: arrival must be before departure';
    END IF;

    IF p_new_reservation_status NOT IN ('In House' , 'Departure') AND  p_new_arrival < v_business_date THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid dates: arrival must be >= business date';
    END IF;


    IF (p_new_room IS NULL AND (p_new_room_type IS NULL OR TRIM(p_new_room_type) = '')) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Either p_new_room or p_new_room_type must be provided';
    END IF;


    IF p_new_room IS NOT NULL THEN
        SELECT room_type INTO v_actual_room_type
        FROM tabRoom
        WHERE name = p_new_room
        LIMIT 1;

        IF v_actual_room_type IS NULL THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Room does not exist';
        END IF;
    ELSE
        SET v_actual_room_type = p_new_room_type;
    END IF;

    IF p_new_room IS NOT NULL AND p_allow_room_sharing = 0 THEN

        SELECT COUNT(DISTINCT rd.reservation),
               GROUP_CONCAT(DISTINCT rd.reservation SEPARATOR ', ')
        INTO v_occupied_room_count, v_existing_reservations
        FROM reservation_date rd
        JOIN `tabReservation` r ON rd.reservation = r.name
        WHERE rd.room = p_new_room
          AND rd.reservation != p_reservation
          AND rd.for_date >= p_new_arrival
          AND rd.for_date < p_new_departure
          AND r.docstatus != 2
          AND r.reservation_status NOT IN ('Canceled', 'No Show');

        IF v_occupied_room_count > 0 THEN
            SET msg_text = CONCAT('Room ', p_new_room, ' is already occupied by reservation(s): ',
                                v_existing_reservations, '. Do you want to share the room?');
            SIGNAL SQLSTATE '45001' SET MESSAGE_TEXT = msg_text;
        END IF;
    END IF;

    IF p_ignore_availability = 0 THEN
        WITH dates AS (
            SELECT for_date
            FROM dim_date
            WHERE for_date >= p_new_arrival AND for_date < p_new_departure
        ),
        rooms AS (
            SELECT r.room_type, COUNT(r.name) AS total_rooms
            FROM tabRoom r
            JOIN `tabRoom Type` rt ON r.room_type = rt.name
            WHERE rt.name = v_actual_room_type
            GROUP BY r.room_type
        ),
        ooo_rooms AS (
            SELECT r.room_type, COUNT(rd.room) AS total_ooo
            FROM room_date rd
            JOIN tabRoom r ON rd.room = r.name AND r.room_type = v_actual_room_type
            JOIN dates d ON rd.for_date = d.for_date
            WHERE rd.out_of_order_status > 0
            GROUP BY r.room_type
        ),
        reserved_rooms AS (
            SELECT rd.room_type, COUNT(*) AS total_reserved
            FROM reservation_date rd
            JOIN dates d ON rd.for_date = d.for_date
            WHERE rd.room_type = v_actual_room_type
            GROUP BY rd.room_type
        )
        SELECT (r.total_rooms - COALESCE(rr.total_reserved, 0) - COALESCE(ooo.total_ooo, 0)) > 0
        INTO v_is_available_count
        FROM rooms r
        LEFT JOIN ooo_rooms ooo ON r.room_type = ooo.room_type
        LEFT JOIN reserved_rooms rr ON r.room_type = rr.room_type
        LIMIT 1;

        IF v_is_available_count <= 0 AND 1 = 2 THEN
            SET msg_text = CONCAT('No availability for room_type ', v_actual_room_type);
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = msg_text;
        END IF;
    END IF;


    DELETE FROM reservation_date WHERE reservation = p_reservation;

    -- SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid dates: Arrival Is Required';
    INSERT INTO reservation_date (reservation, room_type, room ,rate_code,rate_code_rate , base_rate , discount_type , discount_value , for_date)
    SELECT p_reservation, v_actual_room_type, p_new_room ,p_new_rate_code , p_new_rate_code_rate,p_new_base_rate,p_new_discount_type,p_new_discount_value, d.for_date
    FROM dim_date d
    WHERE d.date_actual >= p_new_arrival AND d.date_actual < p_new_departure;



    COMMIT;

END proc_body ;;
DELIMITER ;

DELIMITER ;;
CREATE OR REPLACE PROCEDURE `reservation_date_bulk_upsert`(
     IN p_data JSON
)
BEGIN
    DROP TABLE IF EXISTS tmp_data;
    CREATE TEMPORARY TABLE tmp_data (
        reservation VARCHAR(255) COLLATE utf8mb4_unicode_ci,
        room_type VARCHAR(255) COLLATE utf8mb4_unicode_ci,
        room VARCHAR(255) COLLATE utf8mb4_unicode_ci,
        rate_code VARCHAR(255) COLLATE utf8mb4_unicode_ci,
        rate_code_rate DECIMAL(21,9),
        base_rate DECIMAL(21,9),
        discount_type VARCHAR(10) COLLATE utf8mb4_unicode_ci,
        discount_value DECIMAL(21,9),
        for_date INT(8)
    ) CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

    INSERT INTO tmp_data
    SELECT
        reservation,
        room_type,
        room,
        rate_code,
        rate_code_rate,
        base_rate,
        discount_type,
        discount_value,
        date_to_int(for_date) AS for_date
    FROM JSON_TABLE(
        p_data,
        "$[*]" COLUMNS (
            reservation VARCHAR(255) PATH "$.reservation",
            room_type VARCHAR(255) PATH "$.room_type",
            room VARCHAR(255) PATH "$.room",
            rate_code VARCHAR(255) PATH "$.rate_code",
            rate_code_rate DECIMAL(21,9) PATH "$.rate_code_rate",
            base_rate DECIMAL(21,9) PATH "$.base_rate",
            discount_type VARCHAR(10) PATH "$.discount_type",
            discount_value DECIMAL(21,9) PATH "$.discount_value",
            for_date VARCHAR(20) PATH "$.for_date"
        )
    ) AS jt;

    DELETE r
      FROM
      reservation_date r
      LEFT JOIN tmp_data d on r.reservation = d.reservation   and d.for_date = r.for_date
      WHERE  d.reservation is null;

    INSERT INTO reservation_date (
      reservation,
      room_type,
      room ,
      rate_code,
      rate_code_rate ,
      base_rate ,
      discount_type ,
      discount_value ,
      for_date
    )
    SELECT reservation,
      room_type,
      room ,
      rate_code,
      rate_code_rate ,
      base_rate ,
      discount_type ,
      discount_value ,
      for_date
    FROM tmp_data d  ON DUPLICATE KEY
    UPDATE
      room =  VALUES (room) ,
      room_type = VALUES (room_type),
      room  = VALUES (room),
      rate_code = VALUES (rate_code),
      rate_code_rate  = VALUES (rate_code_rate),
      base_rate  = VALUES (base_rate),
      discount_type  = VALUES (discount_type),
      discount_value  = VALUES (discount_value);




END ;;
DELIMITER ;
