DELIMITER $$
DROP PROCEDURE IF EXISTS folio_list_filtered $$
CREATE OR REPLACE PROCEDURE folio_list_filtered(
    IN p_pos_profile TEXT,
    IN p_docstatus INT ,
    IN p_reservation TEXT,
    IN p_guest TEXT ,
    IN p_room TEXT ,
    IN p_arrival_from DATE,
    IN p_arrival_to DATE,
    IN p_departure_from DATE,
    IN p_departure_to DATE
)
BEGIN
    WITH folios AS (
        SELECT
            r.room,
            fw.name folio_window,
            f.restaurant_table,
            f.name folio,
            r.name reservation,
            r.arrival,
            r.departure,
            r.guest
        FROM tabFolio f
        JOIN `tabFolio Window` fw
            ON f.name = fw.folio
        LEFT JOIN tabReservation r
            ON f.reservation = r.name
        WHERE f.pos_profile = COALESCE(p_pos_profile, f.pos_profile)
          AND f.docstatus = COALESCE(p_docstatus, f.docstatus)
          AND (r.name IS NULL OR r.name = COALESCE(p_reservation, r.name))
          AND (p_guest IS NULL OR r.guest LIKE CONCAT('%', p_guest, '%'))
          AND (r.name IS NULL OR r.room = COALESCE(p_room, r.room))
          AND (r.name IS NULL OR r.arrival >= COALESCE(p_arrival_from, r.arrival))
          AND (r.name IS NULL OR r.arrival <= COALESCE(p_arrival_to, r.arrival))
          AND (r.name IS NULL OR r.departure >= COALESCE(p_departure_from, r.departure))
          AND (r.name IS NULL OR r.departure <= COALESCE(p_departure_to, r.departure))
    ),
    items AS (
        SELECT
            f.folio,
            SUM(ii.amount) total_required_amount
        FROM folios f
        LEFT JOIN `tabPOS Invoice Item` ii
            ON ii.folio_window = f.folio_window
        GROUP BY f.folio
    )
    SELECT
        f.room,
        f.folio_window,
        f.restaurant_table,
        f.folio,
        f.reservation,
        f.arrival,
        f.departure,
        f.guest,
        i.total_required_amount,
        SUM(p.amount) total_paid_amount
    FROM folios f
    JOIN items i
        ON i.folio = f.folio
    LEFT JOIN `tabSales Invoice Payment` p
        ON p.folio_window = f.folio_window
    GROUP BY f.folio, f.room, f.folio_window, f.restaurant_table,
             f.reservation, f.arrival, f.departure, f.guest,
             i.total_required_amount;
END $$

-------------------
DROP PROCEDURE IF EXISTS folio_find $$
CREATE OR REPLACE PROCEDURE folio_find(
    IN p_folio varchar(140),
    IN p_pos_profile varchar(140)
)
BEGIN
    WITH items AS (
      SELECT
        ii.folio_window,
        JSON_ARRAYAGG(
          JSON_OBJECT(
              'invoice_name', i.name,
              'invoice_submitted', i.docstatus,
              'invoice_for_date', i.for_date,
              'invoice_item_for_date', ii.for_date,
              'invoice_item_name', ii.name,
              'item_code', ii.item_code,
              'item_name', ii.item_name,
              'rate', ii.rate,
              'qty', ii.qty,
              'amount', ii.amount
          )
        ) AS items,
        SUM(ii.amount) total_required_amount
      FROM `tabFolio Window` fw
      LEFT JOIN `tabPOS Invoice Item` ii ON fw.name = ii.folio_window
      LEFT JOIN `tabPOS Invoice` i ON ii.parent = i.name
      WHERE fw.folio = COALESCE(p_folio, fw.folio) and i.pos_profile = p_pos_profile
      GROUP BY ii.folio_window
    ), payments AS (
      SELECT
        p.folio_window,
        JSON_ARRAYAGG(
          JSON_OBJECT(
              'invoice_name', i.name,
              'invoice_submitted', i.docstatus,
              'invoice_for_date', i.for_date,
              'mode_of_payment', p.mode_of_payment,
              'amount', p.amount
          )
        ) payments,
        SUM(p.amount) total_paid_amount
      FROM `tabFolio Window` fw
      LEFT JOIN `tabSales Invoice Payment` p ON fw.name = p.folio_window
      LEFT JOIN `tabPOS Invoice` i ON p.parent = i.name and i.pos_profile = p_pos_profile
      WHERE p.folio_window IS NOT NULL
        AND fw.folio = COALESCE(p_folio, fw.folio)
      GROUP BY p.folio_window
    ), windows AS (
      SELECT
        fw.folio,
        fw.name folio_window,
  fw.window_label,
        i.total_required_amount,
        p.total_paid_amount,
        i.items,
        p.payments
      FROM  `tabFolio Window` fw
      LEFT JOIN items i ON fw.name = i.folio_window
      LEFT JOIN payments p ON fw.name = p.folio_window
      WHERE fw.folio = COALESCE(p_folio, fw.folio)
    )
    SELECT
      f.name folio,
      f.restaurant_table,
      r.room,
      r.name reservation,
      r.arrival,
      r.departure,
      SUM(fw.total_required_amount) total_required_amount,
      SUM(fw.total_paid_amount) total_paid_amount,
      r.guest,
      JSON_ARRAYAGG(
        JSON_OBJECT(
          'folio_window',fw.folio_window,
          'window_label' , fw.window_label,
          'total_required_amount' , fw.total_required_amount,
          'total_paid_amount' , fw.total_paid_amount,
          'items' , fw.items,
          'payments' , fw.payments
        )
      ) windows
    FROM tabFolio f
    LEFT JOIN tabReservation r ON f.reservation = r.name
    JOIN windows fw ON fw.folio = f.name
    WHERE f.name = COALESCE(p_folio, f.name)
    GROUP BY f.name, f.restaurant_table, r.room, r.name, r.arrival, r.departure, r.guest;
END $$



DELIMITER ;
