-- MariaDB execution evidence: reports/sql_reconciliation.md. Validate single-country invoices.
SELECT Country, COUNT(DISTINCT InvoiceNo) AS CompletedOrders,
 CAST(SUM(LineSalesGBP) AS DECIMAL(20,2)) AS RevenueGBP
FROM sales GROUP BY Country ORDER BY SUM(LineSalesGBP) DESC, Country ASC;
