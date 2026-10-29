-- MariaDB execution evidence: reports/sql_reconciliation.md. Raw coverage determines labels.
WITH RECURSIVE months AS (
 SELECT CAST(DATE_FORMAT(CoverageStart,'%Y-%m-01') AS DATE) AS MonthStart
 FROM analysis_metadata WHERE Id=1
 UNION ALL
 SELECT DATE_ADD(MonthStart, INTERVAL 1 MONTH) FROM months
 WHERE DATE_ADD(MonthStart, INTERVAL 1 MONTH) <=
 (SELECT CAST(DATE_FORMAT(CoverageEnd,'%Y-%m-01') AS DATE) FROM analysis_metadata WHERE Id=1)
), totals AS (
 SELECT DATE_FORMAT(InvoiceDate,'%Y-%m') AS Month, SUM(LineSalesGBP) AS RevenueGBP,
 COUNT(DISTINCT InvoiceNo) AS CompletedOrders FROM sales GROUP BY DATE_FORMAT(InvoiceDate,'%Y-%m')
), labeled AS (
 SELECT DATE_FORMAT(m.MonthStart,'%Y-%m') AS Month,
 COALESCE(t.CompletedOrders,0) AS CompletedOrders,
 CASE WHEN DATE_FORMAT(m.MonthStart,'%Y-%m')=DATE_FORMAT(a.CoverageStart,'%Y-%m')
 THEN CASE WHEN DAY(a.CoverageStart)>1 THEN 'partial_start' ELSE 'boundary_start_day_1_unverified' END
 WHEN DATE_FORMAT(m.MonthStart,'%Y-%m')=DATE_FORMAT(a.CoverageEnd,'%Y-%m')
 THEN CASE WHEN DAY(a.CoverageEnd)<DAY(LAST_DAY(a.CoverageEnd)) THEN 'partial_end' ELSE 'boundary_end_last_day_unverified' END
 ELSE 'interior_calendar_month' END AS CoverageStatus,
 CAST(COALESCE(t.RevenueGBP,0) AS DECIMAL(20,2)) AS RevenueGBP
 FROM months m CROSS JOIN analysis_metadata a
 LEFT JOIN totals t ON t.Month=DATE_FORMAT(m.MonthStart,'%Y-%m') WHERE a.Id=1
), previous AS (
 SELECT labeled.*, LAG(RevenueGBP) OVER (ORDER BY Month) AS PreviousRevenue,
 LAG(CoverageStatus) OVER (ORDER BY Month) AS PreviousStatus FROM labeled
)
SELECT Month, CompletedOrders, CoverageStatus, RevenueGBP,
 RevenueGBP-PreviousRevenue AS ObservedMoMChangeGBP,
 ROUND(100*(RevenueGBP-PreviousRevenue)/NULLIF(PreviousRevenue,0),2) AS ObservedMoMPct,
 CASE WHEN CoverageStatus='interior_calendar_month' AND PreviousStatus='interior_calendar_month'
 THEN ROUND(100*(RevenueGBP-PreviousRevenue)/NULLIF(PreviousRevenue,0),2) END AS ComparableMoMPct
FROM previous ORDER BY Month;
