# Resume SQL execution safely

The initial connection was refused with error 10061; the user then started XAMPP MySQL on port 3306. MariaDB 10.4.32 accepted the local connection without a password. A read-only check confirmed the target absent, and `retail_sales_analysis` was created and loaded. **Do not repeat the CREATE/LOAD steps below on the now-populated database.** See [the reconciliation report](../reports/sql_reconciliation.md) for the final analysis status. No password was used or recorded.

For subsequent read-only query execution and comparison, use:

```powershell
.\.venv\Scripts\python.exe src/run_sql_analysis.py
```

This script does not create, import, change or delete any database/table. It exports all seven query results into a new ignored local `reports/sql_results/sql_<timestamp>/` folder and writes a reconciliation JSON alongside the public aggregate reports. Use `--user YOUR_LOCAL_USER --port 3306 --prompt-password` only when your account needs the client's hidden password prompt; never supply a password value to any argument. The default matches the current local XAMPP root connection. For a different validated analysis, use `--python-report reports/ANALYSIS_RUN`; matching imported data is required, and the reference totals are specific to the current UCI cleaning policy.

## Fresh-server setup reference

The steps below are retained for reproducing on another server where the target database does not exist. They are not instructions to overwrite the current database.

## 1. Start the existing server

Open **XAMPP Control Panel** from the Windows Start menu and click **Start** next to **MySQL** (XAMPP labels MariaDB as MySQL). Wait for **Running**. Apache is not required. Do not reinstall, initialize or reset the server, change data directories, or delete database files. If startup fails, read XAMPP's displayed error and report the error and port, without credentials.

Once Running, tell the assistant the local port. If no-password local access works, the assistant can continue without handling a password. If your account requires authentication, run the commands below in your own PowerShell terminal; the client reads passwords directly at its hidden prompt. **Never paste a password into this chat, a command argument, an environment variable, a script, or a log.**

## 2. Read-only connection and database-existence check

Run from this project directory. Replace the port only if XAMPP shows another one. A username is not a password:

```powershell
$sqlClient = 'C:/xampp/mysql/bin/mysql.exe'
$sqlUser = Read-Host 'Local database username'
$sqlPort = 3306
$preflightSql = Get-Content -LiteralPath 'sql/00_preflight.sql' -Raw
& $sqlClient --no-defaults --protocol=tcp --host=127.0.0.1 --port=$sqlPort --user=$sqlUser --password --default-character-set=utf8mb4 --execute=$preflightSql
if ($LASTEXITCODE -ne 0) { throw 'Connection/authentication failed; stop' }
```

If error 1045 occurs, authentication failed: use an existing authorized local account and its password at the hidden prompt. Do not reset credentials or put a password in code. If error 10061 remains, the server/port is still unavailable. Stop on either error.

If **database_exists = 1**, stop and preserve `retail_sales_analysis`. Do not run CREATE/LOAD, DROP, TRUNCATE, REPLACE, or import into its tables. The assistant can inspect its schema read-only first and decide whether existing results can be validated safely; do not assume it belongs to this project. If it is zero, continue.

## 3. Create only the dedicated new database

```powershell
$schemaSql = Get-Content -LiteralPath 'sql/01_schema.sql' -Raw
& $sqlClient --no-defaults --protocol=tcp --host=127.0.0.1 --port=$sqlPort --user=$sqlUser --password --default-character-set=utf8mb4 --execute=$schemaSql
if ($LASTEXITCODE -ne 0) { throw 'Schema creation failed; stop before loading' }
```

CREATE has no IF NOT EXISTS. A race creating that database between preflight and CREATE must fail; do not use --force. No existing database is dropped or altered. Identifier fields use binary-collated VARCHAR (so case-distinct codes remain distinct), unit price DECIMAL(20,6), line GBP DECIMAL(20,2), and pence BIGINT. Missing customer IDs are SQL NULL, not zero or a shared invented ID.

## 4. Import the validated dataset

This attempt uses the reproduced Python run `reports/analysis_20261017T165141_531793Z/`. Its generated loader points to its narrow UTF-8 `sql_import.tsv`, produced from the validated cleaned sales, not raw Excel. Regenerate analysis after moving the project so the local LOAD path is correct. Review that path before executing.

```powershell
$loadSql = Get-Content -LiteralPath 'reports/analysis_20261017T165141_531793Z/02_load.sql' -Raw
& $sqlClient --no-defaults --protocol=tcp --host=127.0.0.1 --port=$sqlPort --user=$sqlUser --password --local-infile=1 --default-character-set=utf8mb4 --database=retail_sales_analysis --execute=$loadSql
if ($LASTEXITCODE -ne 0) { throw 'Import failed; stop and inspect, do not rerun blindly' }
$validationSql = Get-Content -LiteralPath 'sql/validation.sql' -Raw
& $sqlClient --no-defaults --protocol=tcp --host=127.0.0.1 --port=$sqlPort --user=$sqlUser --password --default-character-set=utf8mb4 --database=retail_sales_analysis --execute=$validationSql
if ($LASTEXITCODE -ne 0) { throw 'Validation query failed' }
```

Review all LOAD warnings. Expected: **522,540 rows**, **1,024,721,932 pence**, **GBP 10,247,219.32**, **131,387 missing-customer rows**, **0 invalid rows**, and no invoice-attribution conflicts. LOCAL INFILE must be permitted by the server; if disabled, report that error rather than changing global server settings or other databases. Never rerun an import into a populated table to force totals to match.

## 5. Execute all seven queries and export actual results

This loop prompts through the database client for each query if required. It stores only query output, not passwords. No transcript or verbose authentication logging is needed. If desired, execute through an already authenticated database GUI and export equivalent tab-delimited UTF-8 results with headers instead.

```powershell
$resultFolder = Join-Path (Get-Location) ('reports/sql_results/' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $resultFolder -ErrorAction Stop | Out-Null
$queryNames = 'kpis','monthly','countries','top_products_revenue','top_products_quantity','customer_purchases','repeat_purchasing'
foreach ($queryName in $queryNames) {
    $querySql = Get-Content -LiteralPath ('sql/analysis/' + $queryName + '.sql') -Raw
    $resultRows = & $sqlClient --no-defaults --protocol=tcp --host=127.0.0.1 --port=$sqlPort --user=$sqlUser --password --default-character-set=utf8mb4 --batch --raw --database=retail_sales_analysis --execute=$querySql
    if ($LASTEXITCODE -ne 0) { throw ('Query failed: ' + $queryName) }
    [IO.File]::WriteAllLines((Join-Path $resultFolder ($queryName + '.tsv')), [string[]]$resultRows, [Text.UTF8Encoding]::new($false))
}
.\.venv\Scripts\python.exe src/reconcile_sql.py --python-report reports/analysis_20261017T165141_531793Z --sql-results $resultFolder
if ($LASTEXITCODE -ne 0) { throw 'Reconciliation failed; investigate before accepting results' }
```

The comparator aligns rows by month/country/customer/rank; harmless export ordering and equivalent decimal text (e.g. 10.20 versus 10.2000) do not fail. SQL NULL normalizes to blank. Identifier spelling/case/leading zeros and actual penny/percentage differences still fail. Top-ten ranks must match the same product; rank values are not discarded to conceal a different ordering. SQL NULL is exported as `NULL`; these source outputs contain no legitimate text field with that literal value.

## What each query answers

| Query | Plain-language explanation |
| --- | --- |
| kpis | Adds eligible line sales, counts distinct invoices, sums units and divides sales by orders |
| monthly | Groups by calendar month, adds missing calendar months if needed, then uses the previous month's value; flags/suppresses boundary comparisons |
| top_products_revenue | Groups all lines for each exact product code, sorts total GBP descending and code ascending for ties |
| top_products_quantity | Uses the same grouping but ranks total units |
| countries | Adds sales and counts distinct orders per country; anonymous sales remain |
| customer_purchases | Groups only known IDs, counts each invoice once and marks two-or-more-order customers |
| repeat_purchasing | Summarizes those known customers and calculates the repeat-customer percentage |

**Revenue is completed-sales revenue in GBP, not net revenue.** No cancellations/negative adjustments are put back into the sales table. SQL should reproduce the Python view, not change its cleaning policy. See the [current reconciliation report](../reports/sql_reconciliation.md) for what has actually run.
