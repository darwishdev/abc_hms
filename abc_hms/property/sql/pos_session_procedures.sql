
DELIMITER $$
DROP procedure IF EXISTS pos_session_find$$
CREATE PROCEDURE pos_session_find (
    IN session_id VARCHAR(255)
)
BEGIN
    WITH items AS (
        SELECT
            item_name,
            pos_session,
            item_code,
            qty,
            price_list_rate,
            rate,
            (price_list_rate - rate) AS discount_amount,
            amount,
            parent,
            (amount - (qty * (price_list_rate - rate))) AS total_discount_amount
        FROM
            `tabPOS Invoice Item`
        WHERE
            pos_session = session_id
    )
    SELECT
        i.item_name,
        i.item_code,
        SUM(i.qty) AS total_qty,
        AVG(i.price_list_rate) AS avg_price_list_rate,
        AVG(i.rate) AS avg_rate,
        SUM(i.amount) AS total_amount,
        COUNT(DISTINCT i.parent) AS distinct_invoices,
        SUM(i.total_discount_amount) AS total_discount_amount
    FROM
        items i
    GROUP BY
        i.item_name, i.item_code, i.pos_session;

    SELECT
        mode_of_payment,
        SUM(base_amount) AS total_base_amount,
        pos_session
    FROM
        `tabSales Invoice Payment`
    WHERE
        pos_session = session_id
    GROUP BY
        mode_of_payment, pos_session;

END$$

DELIMITER;
