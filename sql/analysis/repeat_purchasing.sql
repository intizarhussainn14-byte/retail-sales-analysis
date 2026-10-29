-- MariaDB execution evidence: reports/sql_reconciliation.md. Repeat rate is window-based, not lifetime.
WITH customers AS (
 SELECT CustomerID, COUNT(DISTINCT InvoiceNo) AS Orders, SUM(LineSalesGBP) AS Revenue
 FROM sales WHERE CustomerID IS NOT NULL GROUP BY CustomerID
)
SELECT COUNT(*) AS KnownCustomers, SUM(Orders>=2) AS RepeatCustomers,
 SUM(Orders=1) AS OneOrderCustomers,
 ROUND(100.0*SUM(Orders>=2)/NULLIF(COUNT(*),0),2) AS RepeatCustomerPct,
 SUM(Orders) AS KnownCustomerOrders,
 CAST(SUM(Revenue) AS DECIMAL(20,2)) AS KnownCustomerRevenueGBP
FROM customers;
