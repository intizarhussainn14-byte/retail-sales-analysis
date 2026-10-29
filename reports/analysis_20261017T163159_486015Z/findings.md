# Completed-sales analysis

Observed revenue: GBP 10247219.32; distinct completed orders: 19,773; units sold: 5,561,387; AOV: GBP 518.24; known unique customers: 4,334.

Among 4,334 known customers, 2,829 (65.27%) placed at least two distinct completed orders in this observation window. This is not lifetime retention or a cohort repeat rate.

The highest-revenue product code is 22423 (REGENCY CAKESTAND 3 TIER), GBP 174156.54. United Kingdom has the highest country revenue, GBP 8724443.67, across 17,901 orders.

The highest-revenue interior calendar month is 2011-11, GBP 1452115.98.

Raw coverage: 2010-12-01 08:26:00 to 2011-12-09 12:50:00. December 2010 starts on day 1: it is not visibly truncated by calendar day, but first-day and source completeness are unverified. December 2011 ends on day 9 and is partial. Interior months are treated as calendar-covered, not independently verified complete.

Monthly tables show observed changes for transparency. ComparableMoMPct is suppressed whenever either month is a boundary month; do not interpret partial-versus-full changes as growth or decline.

Definitions: revenue sums line-rounded integer pence; AOV = revenue / distinct eligible InvoiceNo, rounded half-up to two decimals. Units sum Quantity. Product ranks group by StockCode, with code ascending as the tie-break. Product descriptions use the smallest observed text label and can vary for one code. Countries use distinct invoice counts. Repeat purchasing uses known IDs only and at least two distinct invoices, not multiple lines of one invoice.

Completed-sales revenue excludes cancellations and negative adjustments and is not net revenue. Anonymous sales are retained in overall metrics; customer metrics omit missing IDs. No customer identities are inferred. No categories, costs, profit or return matching are invented.

Limitations: analytical exact-duplicate removal and stock-code exclusions affect totals. Missing IDs limit customer analysis. The window censors purchases before/after coverage; invoices are eligible merchandise orders rather than all source transactions. Large transactions are retained and may influence rankings. These observations do not establish why patterns occurred.

Recommendation: use interior-month comparisons in the dashboard, expose boundary labels and metric definitions, and investigate unusual high-value orders before drawing business conclusions. Promotions, seasonality or customer mix are possible explanations only; they were not tested here.

PASS: cleaning totals, identifiers/eligibility, money consistency, monthly/country revenue and orders, known customer order reconciliation.

SQL status: UNEXECUTED: XAMPP MariaDB 10.4.32 client found; localhost:3306 connection refused; no active standard-port listener/service found.

Tables and SQL import files are alongside this report. SQL reconciliation has not been performed.