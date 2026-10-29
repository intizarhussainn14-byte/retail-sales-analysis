-- Executed on MariaDB 10.4.32; see reports/sql_reconciliation.md.
-- Compare these figures with analysis_metadata.json, cleaning summary and kpis.csv.
SELECT COUNT(*) AS RowsLoaded, SUM(LineSalesPence) AS TotalPence,
 SUM(LineSalesGBP) AS RevenueGBP, SUM(CustomerID IS NULL) AS MissingCustomerRows
FROM sales;
-- Must be zero. UnitPrice is not rounded before line multiplication.
SELECT COUNT(*) AS InvalidRows FROM sales
WHERE Quantity<=0 OR UnitPrice<=0 OR UPPER(InvoiceNo) LIKE 'C%'
 OR LineSalesGBP<>ROUND(Quantity*UnitPrice,2) OR LineSalesGBP*100<>LineSalesPence;
-- Must return no rows: order assignment must be unambiguous.
SELECT InvoiceNo FROM sales GROUP BY InvoiceNo
HAVING COUNT(DISTINCT Country)+MAX(Country IS NULL)>1
 OR COUNT(DISTINCT CustomerID)+MAX(CustomerID IS NULL)>1
 OR COUNT(DISTINCT DATE_FORMAT(InvoiceDate,'%Y-%m'))>1;
