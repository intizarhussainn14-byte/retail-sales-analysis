-- MariaDB execution evidence: reports/sql_reconciliation.md. Completed sales are not net revenue.
SELECT CAST(SUM(LineSalesGBP) AS DECIMAL(20,2)) AS RevenueGBP,
 COUNT(DISTINCT InvoiceNo) AS CompletedOrders, SUM(Quantity) AS UnitsSold,
 ROUND(SUM(LineSalesGBP)/NULLIF(COUNT(DISTINCT InvoiceNo),0),2) AS AverageOrderValueGBP,
 COUNT(DISTINCT CustomerID) AS KnownUniqueCustomers
FROM sales;
