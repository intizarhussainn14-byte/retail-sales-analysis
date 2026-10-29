# MySQL / MariaDB execution guide

Current status: **EXECUTED AND RECONCILED on MariaDB 10.4.32**. All seven SQL outputs match Python. The new `retail_sales_analysis` database was created only after an absence check; pre-existing databases were preserved. It now contains 522,540 cleaned rows. **Do not repeat CREATE/LOAD on it.** Use [EXECUTION_CHECKLIST.md](EXECUTION_CHECKLIST.md) for read-only reruns and safe setup elsewhere. See [the reconciliation report](../reports/sql_reconciliation.md).

The initial localhost:3306 connection was refused. After the user started XAMPP MySQL, the local connection succeeded without a password, and creation, import, validation and analysis completed. No passwords or global settings were changed or stored. SQL query snapshots, actual TSV outputs and hashes were retained; there were no value discrepancies. SQL NULL values for unavailable monthly changes match blank CSV cells after normalization.

The queries use CTE/window functions intended for MySQL 8.0+ or MariaDB 10.2+. **Actual execution was tested on MariaDB 10.4.32 only**, not MySQL 8. Query files are under `sql/analysis/`, one result set per file. `utf8mb4_bin` keeps identifier case distinctions and deterministic product-label ordering. SQL VARCHAR comparisons ignore trailing spaces on some versions; the inspected identifiers have none. The setup instructions below apply only to a fresh server where the target database is absent; otherwise use `src/run_sql_analysis.py` without recreating or loading tables.

1. Start your local server yourself when ready. Use a permitted local account. Enter any password only at the client's interactive prompt (`--password` without a value); do not put it in a script, command argument, environment file or Git. Do not enable network-wide access for this exercise.
2. Run `sql/00_preflight.sql` first and confirm database_exists = 0. If `retail_sales_analysis` exists, stop and preserve it. The schema deliberately has no `IF NOT EXISTS`, DROP or TRUNCATE. Do not run with `--force`: an existing-name error must stop the batch before USE. Run from the project directory, replacing `YOUR_LOCAL_USER`:

```powershell
$schemaSql = Get-Content -LiteralPath 'sql/01_schema.sql' -Raw
& 'C:/xampp/mysql/bin/mysql.exe' --default-character-set=utf8mb4 --local-infile=1 --user=YOUR_LOCAL_USER --password --execute=$schemaSql
if ($LASTEXITCODE -ne 0) { throw 'Schema creation failed; stop and review' }
```

3. Confirm it created a new, empty database. The analysis run folder under `reports/analysis_<timestamp>/` contains a generated `02_load.sql` with the exact absolute import path and raw coverage dates. Inspect it, then execute it against **only the new database** (replace the example database name and report folder below):

```powershell
& 'C:/xampp/mysql/bin/mysql.exe' --default-character-set=utf8mb4 --local-infile=1 --user=YOUR_LOCAL_USER --password --database=retail_sales_analysis --execute="source reports/analysis_TIMESTAMP/02_load.sql"
```

The server must permit LOCAL INFILE; if disabled, consult your local server administrator/configuration rather than changing unrelated databases. Only use the trusted generated TSV with LOCAL enabled. TSV is UTF-8, LF-terminated, header included, unquoted, no escape decoding. The Python exporter checks for embedded tab/newline/backslash characters. Blank customer/description/country fields become SQL NULL. UnitPrice uses DECIMAL(20,6), line revenue DECIMAL(20,2); pence stay BIGINT. Do not import the full cleaned CSV with this column mapping.

4. Immediately inspect LOAD warnings and row counts. Expected: 522,540 rows; GBP 10,247,219.32; 131,387 missing customers for the currently validated cleaning run. Run `sql/validation.sql`: InvalidRows must be zero and the invoice-conflict result empty. Do not re-run LOAD on a populated table; SourceRow primary keys protect against a second import, but inspect errors and use a fresh database for another run.
5. Run each `sql/analysis/*.sql` query. Revenue comes from the already line-rounded decimal amount, not FLOAT recomputation. A completed order is a distinct InvoiceNo with eligible merchandise. Repeat customers have two or more distinct completed invoices and known IDs. Boundary-month observed changes are shown, but qualified comparisons are suppressed. December 2010 begins on day 1 (completeness unverified); December 2011 is partial through day 9.
6. Export each result using `--batch --raw`, preserving headers, to `kpis.tsv`, `monthly.tsv`, `countries.tsv`, `top_products_revenue.tsv`, `top_products_quantity.tsv`, `customer_purchases.tsv`, and `repeat_purchasing.tsv`. In PowerShell, use a UTF-8 writer to avoid version-specific redirect encoding. Example for one query:

```powershell
$sqlRows = & 'C:/xampp/mysql/bin/mysql.exe' --default-character-set=utf8mb4 --batch --raw --user=YOUR_LOCAL_USER --password --database=retail_sales_analysis --execute="source sql/analysis/kpis.sql"
if ($LASTEXITCODE -ne 0) { throw 'SQL query failed' }
$resultPath = Join-Path (Get-Location) 'reports/sql_results/kpis.tsv'
[IO.File]::WriteAllLines($resultPath, [string[]]$sqlRows, [Text.UTF8Encoding]::new($false))
```

Create `reports/sql_results/` first. Repeat for all seven tables, then compare every table, identifier, value and row order:

```powershell
.\.venv\Scripts\python.exe src/reconcile_sql.py --python-report reports/analysis_TIMESTAMP --sql-results reports/sql_results
```

The actual comparison has succeeded for all seven result tables. For later runs, call results reconciled only after their own comparison passes. The comparator aligns semantic row keys, compares money/percentages as exact decimals, preserves text identifiers and normalizes SQL NULL to blank. The original executed query snapshots are retained with the actual local exports; source comments may now point to the current report rather than their original unexecuted authoring status.
