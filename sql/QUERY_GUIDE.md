# Understand the SQL analysis

Every query reads the same completed-sales merchandise lines used by Python. A row is a product line, not a whole order. Revenue is GBP and excludes cancellations/negative adjustments; it is not net revenue.

## Headline metrics (`analysis/kpis.sql`)

`SUM(LineSalesGBP)` adds the already line-rounded DECIMAL amounts. `COUNT(DISTINCT InvoiceNo)` counts orders once even if an invoice has many products. `SUM(Quantity)` counts units. Average order value divides total sales by distinct orders, then rounds to two decimals. `COUNT(DISTINCT CustomerID)` automatically omits SQL NULL, while missing-customer sales remain in the other measures.

Verified SQL headline values: **GBP 10,247,219.32**, **19,773 orders**, **5,561,387 units**, **GBP 518.24 AOV**, **4,334 known customers**. The `kpis` comparison passed against the validated Python table.

## Monthly trend (`analysis/monthly.sql`)

The recursive `months` CTE constructs consecutive months using raw coverage metadata. CTEs are named intermediate results within one query. Eligible lines are grouped by year-month; an empty month can still appear with zero sales. `LAG` retrieves the preceding month. Subtracting its revenue gives the observed change; division gives the percentage change.

Coverage labels keep December 2010 as an unverified start boundary and December 2011 as partial through day 9. `ComparableMoMPct` is NULL when either month is a boundary, preventing an unqualified comparison of a partial period with a full one. SQL NULL exports as `NULL`; Python's CSV uses a blank for the same missing comparison. All 13 monthly rows passed comparison, including these labels and missing values.

## Product leaders (`analysis/top_products_*.sql`)

`GROUP BY StockCode` combines lines for one exact product code. Revenue and units are summed before ranking. `ROW_NUMBER` records the position after sorting, and `LIMIT 10` returns ten products. Product code ascending breaks equal-value ties consistently with Python. Description is a deterministic observed label, not a category or catalog assertion.

`utf8mb4_bin` keeps case-distinct StockCodes separate. A case-insensitive grouping could incorrectly combine codes such as `85123A` and `85123a`, changing product rankings even if total revenue stayed the same.

## Country performance (`analysis/countries.sql`)

Grouping by Country produces one row per market, summing revenue and counting distinct invoices. Anonymous customer rows remain. Before comparing country-order totals with the overall count, the validation query checks that a single invoice is not attributed to multiple countries.

## Known customer purchases (`analysis/customer_purchases.sql`)

`WHERE CustomerID IS NOT NULL` limits this customer-specific query only. Grouping by CustomerID produces each known customer's invoice count, units and revenue. A CASE expression marks at least two distinct invoices as repeat purchasing. Repeated product lines on one invoice do not create a repeat purchase.

## Repeat summary (`analysis/repeat_purchasing.sql`)

An intermediate customer grouping is summarized into known, repeat and one-order customer counts, percentage repeat purchasing, and known-customer order/revenue totals. The denominator is known customers with eligible sales in this time window, not all transactions or anonymous rows. It is not lifetime retention.

## How comparisons work

The comparator aligns semantic row keys (Month, Country, CustomerID or Rank), so harmless export-order differences do not create false failures. Text IDs retain leading zeros and case. Money and percentages are compared as exact Decimal values, allowing only equivalent textual scales, e.g. `10.20` and `10.2000`; an actual one-penny difference fails. SQL NULL normalizes to blank. Product ranks must still identify the same products, so alignment does not hide different rankings.

Two small regression tests verify the comparator; they are separate from the actual engine comparisons. See [the reconciliation report](../reports/sql_reconciliation.md) for full execution evidence and any discrepancies. No causal explanation, profit, categories or return matching is introduced by these queries.
