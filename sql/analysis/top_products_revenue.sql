-- MariaDB execution evidence: reports/sql_reconciliation.md. Rank by exact code, not description.
WITH products AS (
 SELECT StockCode, SUM(Quantity) AS UnitsSold, MIN(Description) AS Description,
 SUM(LineSalesGBP) AS RevenueGBP FROM sales GROUP BY StockCode
)
SELECT ROW_NUMBER() OVER (ORDER BY RevenueGBP DESC, StockCode) AS `Rank`,
 StockCode, UnitsSold, Description, CAST(RevenueGBP AS DECIMAL(20,2)) AS RevenueGBP
FROM products ORDER BY RevenueGBP DESC, StockCode LIMIT 10;
