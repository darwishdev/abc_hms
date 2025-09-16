CREATE TABLE IF NOT EXISTS dim_date (
  date_id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
  next_day_id            INT UNSIGNED NULL,
  date_actual            DATE NOT NULL,
  next_day_actual        DATE NULL,
  for_date               INT NOT NULL,
  epoch                  BIGINT NOT NULL,
  day_suffix             VARCHAR(4) NOT NULL,
  day_name               VARCHAR(9) NOT NULL,
  day_of_week            INT NOT NULL,
  day_of_month           INT NOT NULL,
  day_of_quarter         INT NOT NULL,
  day_of_year            INT NOT NULL,
  week_of_month          INT NOT NULL,
  week_of_year           INT NOT NULL,
  week_of_year_iso       CHAR(10) NOT NULL,
  month_actual           INT NOT NULL,
  month_name             VARCHAR(9) NOT NULL,
  month_name_abbreviated CHAR(3) NOT NULL,
  quarter_actual         INT NOT NULL,
  quarter_name           VARCHAR(9) NOT NULL,
  year_actual            INT NOT NULL,
  first_day_of_week      DATE NOT NULL,
  last_day_of_week       DATE NOT NULL,
  first_day_of_month     DATE NOT NULL,
  last_day_of_month      DATE NOT NULL,
  first_day_of_quarter   DATE NOT NULL,
  last_day_of_quarter    DATE NOT NULL,
  first_day_of_year      DATE NOT NULL,
  last_day_of_year       DATE NOT NULL,
  mmyyyy                 CHAR(6) NOT NULL,
  mmddyyyy               CHAR(10) NOT NULL,
  weekend_indr           TINYINT(1) NOT NULL,
  PRIMARY KEY (date_id),
  UNIQUE KEY uk_date_actual (date_actual),
  UNIQUE KEY uk_for_date (for_date),
  KEY idx_year_month (year_actual, month_actual),
  KEY idx_week (year_actual, week_of_year),
  KEY idx_first_of_periods (first_day_of_month, first_day_of_quarter, first_day_of_year),
  CONSTRAINT fk_dim_date_next FOREIGN KEY (next_day_id) REFERENCES dim_date(date_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS room_date_lookup (
    id INT AUTO_INCREMENT PRIMARY KEY,
    lookup_type VARCHAR(50) NOT NULL,   -- e.g. 'room status', 'house keeping status'
    lookup_key VARCHAR(50) NOT NULL,    -- e.g. 'vacant', 'clean'
    lookup_value INT NOT NULL,          -- e.g. 0, 1
    UNIQUE KEY unique_lookup (lookup_type, lookup_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS
  `room_date_log` (
    `room` varchar(140) NOT NULL,
    `user` varchar(140) NOT NULL,
    `reason` varchar(140) NOT NULL,
    `from_date` int(8) NOT NULL,
    `to_date` int(8) NOT NULL,
    `out_of_order_status` int(1),
    `out_of_order_reason` TEXT
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS
  `room_date` (
    `room` varchar(255) NOT NULL,
    `for_date` int(8) NOT NULL,
    `persons` int(1),
    `house_keeping_status` int(1) , -- {0 : vancant , 1 : occ},
    `room_status` int(1) , -- {0 : dirty , 1 : clean , 2 : inspected},
    `out_of_order_status` int(1) , -- {0 : in order, 1 : ooo , 2 : ooc },
    `out_of_order_reason` TEXT, -- {0 : in order, 1 : ooo , 2 : ooc },
    `guest_service_status` int(1) , -- {0 : no_status , 1 : dnd  , 2 : make up},
    UNIQUE KEY `uq_room_for_date` (`room`, `for_date`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS
  `reservation_date` (
    `reservation` varchar(255) NOT NULL,
    `room_type` varchar(255) NOT NULL,
    `for_date` int(8) NOT NULL,
    UNIQUE KEY `uq_room_for_date` (`reservation`, `for_date`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


CREATE OR REPLACE TABLE room_type_rate (
    room_type VARCHAR(140) NOT NULL,
    rate_code VARCHAR(140) NOT NULL,
    rate DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    for_date INT(8) NOT NULL,
    PRIMARY KEY (room_type, rate_code, for_date)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;
DROP TABLE IF EXISTS reservation_date;
CREATE TABLE
  `reservation_date` (
    `reservation` varchar(255) NOT NULL,
    `room_type` varchar(255) NOT NULL,
    `room` varchar(255),
    `for_date` int(8) NOT NULL,
    UNIQUE KEY uq_room_for_date (reservation, room , for_date)
  ) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

