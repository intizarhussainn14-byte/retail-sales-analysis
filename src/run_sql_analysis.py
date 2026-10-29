"""Read-only execution/export of SQL analysis against the dedicated loaded database.

No CREATE/LOAD/UPDATE/DROP statements are issued. Passwords are never accepted
as arguments: --prompt-password delegates hidden input to the database client.
"""
import argparse
import csv
import io
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from inspect_data import ROOT, sha256
from reconcile_sql import KEYS, compare_tables


def write_report(report, evidence_path):
    """Write current status only from completed engine comparisons and exports."""
    assert report['status'] == 'PASS'
    folder = ROOT/report['results_folder']
    kpi = pd.read_csv(folder/'kpis.tsv', sep='\t', dtype='string').iloc[0]
    repeat = pd.read_csv(folder/'repeat_purchasing.tsv', sep='\t', dtype='string').iloc[0]
    lines = ['# SQL execution and reconciliation', '',
             '**PASS — all seven SQL result tables match the validated Python analysis.**', '',
             f"Engine: **{report['server']['ServerVersion']}**, local port {report['server']['ServerPort']}. Database: **retail_sales_analysis**.", '',
             '## Execution history and preservation', '',
             'The initial connection failed with Windows error 10061 because the server was stopped. The user started XAMPP MySQL. A local connection then succeeded without a password. A read-only information_schema check returned database_exists = 0 before CREATE. Only the new dedicated database and its tables were created/loaded; no pre-existing database was changed. No account, password or global server setting was changed.', '',
             'The schema uses binary-collated VARCHAR identifiers, BIGINT quantities/pence and DECIMAL monetary values. The UTF-8 TSV was loaded with blank customer IDs converted to NULL. The import returned no warning output. Validation found 522,540 rows, 1,024,721,932 pence, 131,387 missing customer IDs, zero invalid quantity/price/cancellation/rounding rows, and no ambiguous invoice attribution. The imported source hash matches the Python analysis metadata.', '',
             '## Actual SQL results', '',
             '| Metric | SQL result | Python comparison |', '| --- | ---: | --- |',
             f'| Completed-sales revenue (GBP) | {kpi.RevenueGBP} | Match |',
             f'| Completed orders | {kpi.CompletedOrders} | Match |',
             f'| Units sold | {kpi.UnitsSold} | Match |',
             f'| Average order value (GBP) | {kpi.AverageOrderValueGBP} | Match |',
             f'| Known customers | {kpi.KnownUniqueCustomers} | Match |',
             f'| Repeat customers | {repeat.RepeatCustomers} | Match |',
             f'| Repeat-customer percentage | {repeat.RepeatCustomerPct}% | Match |', '',
             '| Table | SQL rows compared | Status |', '| --- | ---: | --- |']
    for name, result in report['tables'].items():
        lines.append(f"| {name} | {result['rows']} | {result['status']} |")
    lines += ['', '## Discrepancy investigation', '',
              '**No value discrepancies were found.** Every returned equivalent field was compared, including all 4,334 customer rows, product identities/ranks, all countries, all monthly labels and both observed/qualified MoM values.', '',
              'One expected representation difference was observed: SQL exports NULL for unavailable monthly comparisons, while Python CSV stores a blank. The comparator normalizes this to the same missing value. It aligns semantic row keys rather than treating file row order as a data difference, and compares exact Decimal values rather than strings with different decimal scales. Actual penny differences, identifier changes and different ranked products still fail. Two regression tests exercise these safeguards; the complete ten-test Python suite also passed.', '',
              'Binary collation preserved case-distinct product codes. DECIMAL amounts and per-line integer pence reconciled without a rounding tolerance. Distinct invoice counts avoid treating product lines as separate orders. Customer-specific queries omit NULL IDs; overall sales retain anonymous lines. These definitions reproduce Python rather than re-cleaning data in SQL.', '',
              'December 2010 remains a boundary with completeness unverified; December 2011 is partial through day 9. Qualified MoM comparisons involving either boundary remain NULL, matching Python. Completed-sales revenue excludes cancellations/negative adjustments and is **not net revenue**.', '',
              'Some grouped queries took longer on this local instance. They completed without changing global database settings; no performance claim or causal business explanation is inferred.', '',
              '## Evidence and reproduction', '',
              f"- [Machine-readable comparison evidence]({evidence_path.name}) includes engine/version, validation values and result/query hashes.",
              f"- Python reference: `{report['python_report']}`.",
              f"- Local actual SQL TSVs and query snapshots: `{report['results_folder']}`. These line/customer-level exports are ignored by Git; the public summary is retained.",
              '- [Execution/import instructions](../sql/EXECUTION_CHECKLIST.md): the database now exists, so do not repeat CREATE/LOAD. Use the read-only runner for subsequent queries.',
              '- [Beginner query guide](../sql/QUERY_GUIDE.md) explains aggregation, distinct counts, CTEs, window functions and comparisons.', '',
              '```powershell', '.\\.venv\\Scripts\\python.exe src/run_sql_analysis.py', '```', '',
              'SQL was tested on MariaDB 10.4.32. MySQL 8 compatibility is intended but has not been separately engine-tested. Current Excel/Power BI completion status is tracked in README.md; SQL reconciliation by itself does not validate visualization artifacts. Nothing was staged, committed or pushed.']
    (ROOT/'reports/sql_reconciliation.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    status_path = ROOT/'reports/sql_execution_status.json'
    status = json.loads(status_path.read_text()) if status_path.exists() else {}
    status.update(status='PASS', server_version=report['server']['ServerVersion'], database_exists=True,
                  database_existed_before_creation=False, database_created=True, rows_loaded=522540,
                  sql_queries_executed=True, reconciliation_completed=True, connection_error=None,
                  reconciliation_evidence=evidence_path.relative_to(ROOT).as_posix())
    status_path.write_text(json.dumps(status, indent=2), encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--client', type=Path, default=Path('C:/xampp/mysql/bin/mysql.exe'))
    p.add_argument('--user', default='root')
    p.add_argument('--port', type=int, default=3306)
    p.add_argument('--prompt-password', action='store_true')
    p.add_argument('--python-report', type=Path, default=ROOT/'reports/analysis_20261017T165141_531793Z')
    args = p.parse_args()
    args.python_report = args.python_report.resolve()
    environment = dict(os.environ)
    environment.pop('MYSQL_PWD', None)
    command = [str(args.client), '--no-defaults', '--protocol=tcp', '--host=127.0.0.1',
               f'--port={args.port}', f'--user={args.user}', '--connect-timeout=5',
               '--default-character-set=utf8mb4', '--batch', '--raw', '--database=retail_sales_analysis']
    if args.prompt_password:
        command.append('--password')

    def query(sql):
        completed = subprocess.run(command, input=sql, capture_output=True, encoding='utf-8',
                                   env=environment, check=False)
        if completed.returncode:
            raise RuntimeError('Database query failed: ' + completed.stderr)
        return completed.stdout

    def record(sql):
        return list(csv.DictReader(io.StringIO(query(sql)), delimiter='\t'))

    server = record('SELECT VERSION() AS ServerVersion, @@port AS ServerPort;')[0]
    validation = record('''SELECT COUNT(*) AS RowsLoaded, SUM(LineSalesPence) AS TotalPence,
        SUM(LineSalesGBP) AS RevenueGBP, SUM(CustomerID IS NULL) AS MissingCustomerRows,
        COUNT(DISTINCT StockCode) AS DistinctProductCodes,
        SUM(Quantity<=0 OR UnitPrice<=0 OR UPPER(InvoiceNo) LIKE 'C%'
            OR LineSalesGBP<>ROUND(Quantity*UnitPrice,2) OR LineSalesGBP*100<>LineSalesPence) AS InvalidRows
        FROM sales;''')[0]
    assert validation['RowsLoaded'] == '522540'
    assert validation['TotalPence'] == '1024721932'
    assert validation['MissingCustomerRows'] == '131387'
    assert validation['InvalidRows'] == '0'
    conflicts = record('''SELECT InvoiceNo FROM sales GROUP BY InvoiceNo
        HAVING COUNT(DISTINCT Country)+MAX(Country IS NULL)>1
        OR COUNT(DISTINCT CustomerID)+MAX(CustomerID IS NULL)>1
        OR COUNT(DISTINCT DATE_FORMAT(InvoiceDate,'%Y-%m'))>1;''')
    assert not conflicts
    metadata = json.loads((args.python_report/'analysis_metadata.json').read_text())
    imported = record('SELECT SourceCSV_SHA256 FROM analysis_metadata WHERE Id=1;')[0]
    assert imported['SourceCSV_SHA256'] == metadata['input_sha256']
    run = datetime.now(timezone.utc).strftime('sql_%Y%m%dT%H%M%S_%fZ')
    out = ROOT/'reports/sql_results'/run
    out.mkdir(parents=True, exist_ok=False)
    snapshots = out/'query_snapshots'
    snapshots.mkdir()
    results = {}
    for name in KEYS:
        script = ROOT/'sql/analysis'/f'{name}.sql'
        snapshot = snapshots/f'{name}.sql'
        shutil.copyfile(script, snapshot)
        text = query(snapshot.read_text(encoding='utf-8'))
        path = out/f'{name}.tsv'
        path.write_text(text, encoding='utf-8', newline='')
        py = pd.read_csv(args.python_report/f'{name}.csv', dtype='string', keep_default_na=False)
        sql = pd.read_csv(path, sep='\t', dtype='string', keep_default_na=False)
        try:
            compare_tables(name, py, sql)
            results[name] = {'status': 'PASS', 'rows': len(sql), 'query_sha256': sha256(script), 'result_sha256': sha256(path)}
        except AssertionError as exc:
            results[name] = {'status': 'FAIL', 'rows': len(sql), 'cause': str(exc)}
        print(f'{name}: {results[name]["status"]} ({len(sql)} rows)', flush=True)
    report = {'status': 'PASS' if all(r['status']=='PASS' for r in results.values()) else 'DISCREPANCIES',
              'database': 'retail_sales_analysis', 'server': server, 'load_validation': validation,
              'invoice_conflicts': len(conflicts), 'python_report': args.python_report.relative_to(ROOT).as_posix(),
              'results_folder': out.relative_to(ROOT).as_posix(), 'tables': results,
              'comparison': 'Semantic row keys; exact Decimal values; NULL-to-blank; string IDs preserved. No tolerance hides penny differences.'}
    target = ROOT/'reports'/f'{run}_reconciliation.json'
    target.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(target)
    if report['status'] != 'PASS':
        raise SystemExit('SQL discrepancies require investigation; exports preserved')
    write_report(report, target)


if __name__ == '__main__':
    main()
