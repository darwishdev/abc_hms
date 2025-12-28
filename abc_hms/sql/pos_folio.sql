

DELIMITER ;;
CREATE OR REPLACE PROCEDURE `folio_find`(
    IN p_folio varchar(140),
    IN p_pos_profile varchar(140)
)
BEGIN
    WITH items AS (
      SELECT
        ii.folio_window,
        JSON_ARRAYAGG(
          JSON_OBJECT(
              'invoice_item_name',ii.name,
              'print_class',ii.print_class,
              'invoice_submitted', i.docstatus,
              'invoice_for_date', i.for_date,
              'invoice_item_for_date', ii.for_date,
              'pos_session', ii.pos_session,
              'invoice_remarks',i.remarks,
              'price_list_rate',ii.price_list_rate,
              'consolidated_invoice',i.consolidated_invoice,
              'discount_percentage',ii.discount_percentage,
              'discount_amount', ii.discount_amount,
              'distributed_discount_amount', ii.distributed_discount_amount,
              'item_code', ii.item_code,
              'item_name', ii.item_name,
              'rate', ii.rate,
              'qty', ii.qty,
              'amount', ii.amount
          )
        ) AS items,
        SUM(ii.discount_amount) total_item_discount_amount,
        SUM(ii.distributed_discount_amount) total_distributed_discount_amount,
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
              'payment_name', p.name,
              'consolidated_invoice',i.consolidated_invoice,
              'invoice_for_date', i.for_date,
              'pos_session', p.pos_session,
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
    i.total_item_discount_amount,
  i.total_distributed_discount_amount,
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
      SUM(fw.total_item_discount_amount) total_item_discount_amount,
  SUM(fw.total_distributed_discount_amount) total_distributed_discount_amount,
-- SELECT * FROM `tabPOS Invoice Item`
      SUM(fw.total_required_amount) total_required_amount,
      SUM(fw.total_paid_amount) total_paid_amount,
      r.guest,
      JSON_ARRAYAGG(
        JSON_OBJECT(
          'folio_window',fw.folio_window,
          'window_label' , fw.window_label,
          'total_item_discount_amount',fw.total_item_discount_amount,
          'total_distributed_discount_amount',fw.total_distributed_discount_amount,
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
END ;;
DELIMITER ;

DELIMITER ;;
CREATE OR REPLACE PROCEDURE `folio_find_balance`(
    IN p_folio varchar(140),
    IN p_folio_window varchar(140)
)
BEGIN
      WITH items AS (
          SELECT
              i.folio_window,
              SUM(i.amount) AS amount
          FROM `tabPOS Invoice Item` i
          join `tabFolio Window` w on i.folio_window = w.name and w.folio = p_folio
          WHERE w.name = COALESCE(p_folio_window , w.name)
          GROUP BY i.folio_window
      ), payments AS (
          SELECT
              p.folio_window,
              SUM(p.amount) AS amount
          FROM `tabSales Invoice Payment` p
          join `tabFolio Window` w on p.folio_window = w.name and w.folio = p_folio
          WHERE w.name = COALESCE(p_folio_window , w.name)
          GROUP BY p.folio_window
      )
      SELECT
          fw.name AS folio_window,
          COALESCE(items.amount, 0) AS amount,
          COALESCE(payments.amount, 0) AS paid
      FROM `tabReservation` r
      JOIN `tabFolio` f ON f.reservation = r.name
      JOIN `tabFolio Window` fw ON fw.folio = f.name
      LEFT JOIN items ON fw.name = items.folio_window
      LEFT JOIN payments ON fw.name = payments.folio_window
      WHERE f.name = p_folio
      and fw.name = COALESCE(p_folio_window , fw.name);
END ;;
DELIMITER ;

DELIMITER ;;
CREATE OR REPLACE PROCEDURE folio_list_filtered (
  IN p_pos_profile TEXT,
  IN p_docstatus INT,
  IN p_reservation TEXT,
  IN p_guest TEXT,
  IN p_room TEXT,
  IN p_arrival_from DATE,
  IN p_arrival_to DATE,
  IN p_departure_from DATE,
  IN p_departure_to DATE,
  IN p_include_paymaster bool
) BEGIN
WITH
  folios AS (
    SELECT
      r.room,
      fw.name folio_window,
      f.restaurant_table,
      f.docstatus,
      f.name folio,
      r.name reservation,
      ps.business_date,
      r.arrival,
      rt.pay_master,
      r.departure,
      r.guest
    FROM
      tabFolio f
      JOIN `tabFolio Window` fw ON f.name = fw.folio
      LEFT JOIN tabReservation r ON f.reservation = r.name
      LEFT JOIN `tabProperty Setting` ps ON r.property = ps.name
      LEFT JOIN tabRoom ro ON r.room = ro.name
      LEFT JOIN `tabRoom Type` rt ON ro.room_type = rt.name
    WHERE
      f.pos_profile = COALESCE(p_pos_profile, f.pos_profile)
      AND f.docstatus = COALESCE(p_docstatus, f.docstatus)
      AND (
        r.name IS NULL
        OR r.name = COALESCE(p_reservation, r.name)
      )
      AND (
        p_guest IS NULL
        OR r.guest LIKE CONCAT('%', p_guest, '%')
      )
      AND (
        r.name IS NULL
        OR r.room = COALESCE(p_room, r.room)
      )
      AND (
        r.name IS NULL
        OR r.arrival >= COALESCE(p_arrival_from, r.arrival)
      )
      AND (
        r.name IS NULL
        OR r.arrival <= COALESCE(p_arrival_to, r.arrival)
      )
      AND (
        r.name IS NULL
        OR r.departure >= COALESCE(p_departure_from, r.departure)
      )
      AND (
        r.name IS NULL
        OR r.departure <= COALESCE(p_departure_to, r.departure)
      )
  ),
  items AS (
    SELECT
      f.folio,
      i.customer guest,
      SUM(ii.amount) total_required_amount
    FROM
      folios f
      LEFT JOIN `tabPOS Invoice Item` ii ON ii.folio_window = f.folio_window
      LEFT JOIN `tabPOS Invoice` i ON ii.parent = i.name
      and ii.parenttype = 'POS Invoice'
    GROUP BY
      f.folio
  )
SELECT
  f.room,
  f.restaurant_table,
  f.docstatus,
  f.folio,
  f.reservation,
  f.arrival,
  f.pay_master,
  f.departure,
  (f.arrival = f.business_date) is_arrival,
  (f.departure = f.business_date) is_departure,
  coalesce(f.guest, i.guest) guest,
  i.total_required_amount,
  GROUP_CONCAT(f.folio_window) windows,
  SUM(p.amount) total_paid_amount
FROM
  folios f
  JOIN items i ON i.folio = f.folio
  LEFT JOIN `tabSales Invoice Payment` p ON p.folio_window = f.folio_window
WHERE
  f.pay_master = IF(p_include_paymaster, f.pay_master, 0)
  and (f.arrival is null or f.arrival <= f.business_date)
  and (f.departure is null or f.departure <= f.business_date)
GROUP BY
  f.folio,
  f.pay_master,
  f.room,
  f.restaurant_table,
  f.reservation,
  f.arrival,
  f.departure,
  f.guest,
  i.total_required_amount;

END;;
DELIMITER ;


DELIMITER ;;
CREATE  OR REPLACE PROCEDURE folio_transfer_submitted_items(
  IN p_destination_window varchar(140),
    IN p_source_window varchar(140),
    IN p_item_names TEXT
)
BEGIN
  IF p_destination_window  then
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid p_destination_window is required for transfer';
  END IF;
  IF p_source_window IS NULL AND  p_item_names IS NULL then
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid p_source_window or p_item_names is required for transfer';
  END IF;
  UPDATE `tabPOS Invoice Item` ii
  join `tabPOS Invoice` i on ii.parent = i.name and ii.parenttype = 'POS Invoice' and ii.docstatus = 1
  SET folio_window = p_destination_window
  WHERE ii.folio_window = coalesce(p_source_window , ii.folio_window)
  AND (p_item_names is null or find_in_set(ii.name , p_item_names));
END ;;
DELIMITER ;

DELIMITER ;;
CREATE OR REPLACE PROCEDURE folio_merge_submitted_invoices(
    IN p_source_folio varchar(140),
    IN p_destination_folio varchar(140),
    IN p_destination_window varchar(140)
)
BEGIN
    DELETE FROM `tabPOS Invoice` WHERE folio = p_source_folio AND docstatus = 0;
    UPDATE `tabPOS Invoice` SET old_folio = p_source_folio , folio = p_destination_folio WHERE folio = p_source_folio AND docstatus = 1;
    update `tabPOS Invoice Item` i join `tabFolio Window` fw on i.folio_window = fw.name and fw.folio = p_source_folio set i.folio_window = p_destination_window;
    update `tabSales Invoice Payment` p join `tabFolio Window` fw on p.folio_window =
            fw.name and fw.folio = p_source_folio set p.folio_window = p_destination_window;
    UPDATE `tabFolio` SET folio_status = 'Merged' , merged_with_folio = p_destination_folio, docstatus = 2 WHERE name = p_source_folio;
END;;
DELIMITER ;
