-- MariaDB execution evidence: reports/sql_reconciliation.md. Only customer metrics omit anonymous IDs.
SELECT CustomerID, COUNT(DISTINCT InvoiceNo) AS CompletedOrders,
 SUM(Quantity) AS UnitsSold, CAST(SUM(LineSalesGBP) AS DECIMAL(20,2)) AS RevenueGBP,
 CASE WHEN COUNT(DISTINCT InvoiceNo)>=2 THEN 1 ELSE 0 END AS RepeatCustomer
FROM sales WHERE CustomerID IS NOT NULL
GROUP BY CustomerID ORDER BY CustomerID;
