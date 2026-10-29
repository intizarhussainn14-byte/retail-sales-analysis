# SQL execution and reconciliation

**PASS — all seven SQL result tables match the validated Python analysis.**

Engine: **10.4.32-MariaDB**, local port 3306. Database: **retail_sales_analysis**.

## Execution history and preservation

The initial connection failed with Windows error 10061 because the server was stopped. The user started XAMPP MySQL. A local connection then succeeded without a password. A read-only information_schema check returned database_exists = 0 before CREATE. Only the new dedicated database and its tables were created/loaded; no pre-existing database was changed. No account, password or global server setting was changed.

The schema uses binary-collated VARCHAR identifiers, BIGINT quantities/pence and DECIMAL monetary values. The UTF-8 TSV was loaded with blank customer IDs converted to NULL. The import returned no warning output. Validation found 522,540 rows, 1,024,721,932 pence, 131,387 missing customer IDs, zero invalid quantity/price/cancellation/rounding rows, and no ambiguous invoice attribution. The imported source hash matches the Python analysis metadata.

## Actual SQL results

| Metric | SQL result | Python comparison |
| --- | ---: | --- |
| Completed-sales revenue (GBP) | 10247219.32 | Match |
| Completed orders | 19773 | Match |
| Units sold | 5561387 | Match |
| Average order value (GBP) | 518.24 | Match |
| Known customers | 4334 | Match |
| Repeat customers | 2829 | Match |
| Repeat-customer percentage | 65.27% | Match |

| Table | SQL rows compared | Status |
| --- | ---: | --- |
| kpis | 1 | PASS |
| monthly | 13 | PASS |
| countries | 38 | PASS |
| top_products_revenue | 10 | PASS |
| top_products_quantity | 10 | PASS |
| customer_purchases | 4334 | PASS |
| repeat_purchasing | 1 | PASS |

## Discrepancy investigation

**No value discrepancies were found.** Every returned equivalent field was compared, including all 4,334 customer rows, product identities/ranks, all countries, all monthly labels and both observed/qualified MoM values.

One expected representation difference was observed: SQL exports NULL for unavailable monthly comparisons, while Python CSV stores a blank. The comparator normalizes this to the same missing value. It aligns semantic row keys rather than treating file row order as a data difference, and compares exact Decimal values rather than strings with different decimal scales. Actual penny differences, identifier changes and different ranked products still fail. Two regression tests exercise these safeguards; the complete ten-test Python suite also passed.

Binary collation preserved case-distinct product codes. DECIMAL amounts and per-line integer pence reconciled without a rounding tolerance. Distinct invoice counts avoid treating product lines as separate orders. Customer-specific queries omit NULL IDs; overall sales retain anonymous lines. These definitions reproduce Python rather than re-cleaning data in SQL.

December 2010 remains a boundary with completeness unverified; December 2011 is partial through day 9. Qualified MoM comparisons involving either boundary remain NULL, matching Python. Completed-sales revenue excludes cancellations/negative adjustments and is **not net revenue**.

Some grouped queries took longer on this local instance. They completed without changing global database settings; no performance claim or causal business explanation is inferred.

## Evidence and reproduction

- [Machine-readable comparison evidence](sql_20261017T171530_730533Z_reconciliation.json) includes engine/version, validation values and result/query hashes.
- Python reference: `reports/analysis_20261017T165141_531793Z`.
- Local actual SQL TSVs and query snapshots: `reports/sql_results/sql_20261017T171530_730533Z`. These line/customer-level exports are ignored by Git; the public summary is retained.
- [Execution/import instructions](../sql/EXECUTION_CHECKLIST.md): the database now exists, so do not repeat CREATE/LOAD. Use the read-only runner for subsequent queries.
- [Beginner query guide](../sql/QUERY_GUIDE.md) explains aggregation, distinct counts, CTEs, window functions and comparisons.

```powershell
.\.venv\Scripts\python.exe src/run_sql_analysis.py
```

SQL was tested on MariaDB 10.4.32. MySQL 8 compatibility is intended but has not been separately engine-tested. Current Excel/Power BI completion status is tracked in README.md; SQL reconciliation by itself does not validate visualization artifacts. Nothing was staged, committed or pushed.
