CREATE OR REPLACE VIEW daily_sales AS
WITH si_tax_calc AS (
    SELECT
        si.name,
        si.net_total AS total_net,
        si.total_taxes_and_charges total_tax,
        (si.grand_total - si.net_total) total_tax_calc,
        si.rounding_adjustment rounding_adjustment,
        (((si.grand_total - si.net_total) - si.rounding_adjustment )- si.total_taxes_and_charges) tax_difference,
        ((((si.grand_total - si.net_total) - si.rounding_adjustment )- si.total_taxes_and_charges) < 2) is_tax_correct,
        si.grand_total AS total_gross,
        SUM(pi.grand_total) pi_total,
        SUM(pi.grand_total) - si.grand_total pi_total_difference,
        (SUM(pi.grand_total) - si.grand_total) < 2 is_pi_total_correct,
        GROUP_CONCAT(pi.name) AS pi_names,
        GROUP_CONCAT(pi.for_date) AS pi_dates,
        GROUP_CONCAT(pi.customer) AS pi_customers,
        si.customer,
        MIN(pi.for_date) AS for_date
    FROM `tabSales Invoice` si
    JOIN `tabPOS Invoice` pi on pi.consolidated_invoice = si.name
    WHERE si.docstatus = 1
    GROUP BY si.name
),

tax_breakdown AS (
    SELECT
        stc.parent AS invoice_name,
        SUM(CASE WHEN stc.account_head LIKE '%Service Charge%' THEN stc.tax_amount ELSE 0 END) AS service_charge_tax,
        SUM(CASE WHEN stc.account_head LIKE '%Value Add Tax%' OR stc.account_head LIKE '%VAT%' THEN stc.tax_amount ELSE 0 END) AS vat_tax
    FROM `tabSales Taxes and Charges` stc
    WHERE stc.parenttype = 'Sales Invoice'
    GROUP BY stc.parent
),

invoice_with_taxes AS (
    SELECT
        sic.*,
        tb.service_charge_tax,
        tb.vat_tax
    FROM si_tax_calc sic
    LEFT JOIN tax_breakdown tb ON sic.name = tb.invoice_name
),

daily_summary AS (
    SELECT
        iw.for_date,
  SUM(iw.total_net) AS daily_total_net,
        SUM(iw.total_gross) AS daily_total_gross,
        SUM(iw.service_charge_tax) AS daily_service_charge_tax,
        SUM(iw.vat_tax) AS daily_vat_tax,
        JSON_ARRAYAGG(
            JSON_OBJECT(
                'invoice_name', iw.name,
                'total_net', iw.total_net,
                'total_gross', iw.total_gross,
                'total_tax', iw.total_tax,
                'rounding_adjustment', iw.rounding_adjustment,
                'tax_difference', iw.tax_difference,
                'is_tax_correct', iw.is_tax_correct,
                'pi_total', iw.pi_total,
                'pi_total_difference', iw.pi_total_difference,
                'is_pi_total_correct', iw.is_pi_total_correct,
                'pi_names', iw.pi_names,
                'pi_dates', iw.pi_dates,
                'pi_customers', iw.pi_customers,
                'customer', iw.customer,
                'service_charge_tax', iw.service_charge_tax,
                'vat_tax', iw.vat_tax
            )
        ) AS sales_invoices,
        JSON_ARRAYAGG(
            JSON_OBJECT(
                'pi_names', iw.pi_names,
                'pi_total', iw.pi_total
            )
        ) AS pos_invoice_summary
    FROM invoice_with_taxes iw
    GROUP BY iw.for_date
),

-- New CTE to calculate Month-to-Date and Year-to-Date totals
daily_summary_with_mtd_ytd AS (
    SELECT
        SUM(ds.daily_total_net) OVER (PARTITION BY YEAR(ds.for_date), MONTH(ds.for_date) ORDER BY ds.for_date) AS mtd_total_net,
        SUM(ds.daily_total_gross) OVER (PARTITION BY YEAR(ds.for_date), MONTH(ds.for_date) ORDER BY ds.for_date) AS mtd_total_gross,
        SUM(ds.daily_service_charge_tax) OVER (PARTITION BY YEAR(ds.for_date), MONTH(ds.for_date) ORDER BY ds.for_date) AS mtd_service_charge_tax,
        SUM(ds.daily_vat_tax) OVER (PARTITION BY YEAR(ds.for_date), MONTH(ds.for_date) ORDER BY ds.for_date) AS mtd_vat_tax,
        SUM(ds.daily_total_net) OVER (PARTITION BY YEAR(ds.for_date) ORDER BY ds.for_date) AS ytd_total_net,
        SUM(ds.daily_total_gross) OVER (PARTITION BY YEAR(ds.for_date) ORDER BY ds.for_date) AS ytd_total_gross,
        SUM(ds.daily_service_charge_tax) OVER (PARTITION BY YEAR(ds.for_date) ORDER BY ds.for_date) AS ytd_service_charge_tax,
        SUM(ds.daily_vat_tax) OVER (PARTITION BY YEAR(ds.for_date) ORDER BY ds.for_date) AS ytd_vat_tax,
        ds.*
    FROM daily_summary ds
)

SELECT *
FROM daily_summary_with_mtd_ytd
ORDER BY for_date;
