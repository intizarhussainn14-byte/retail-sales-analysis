"""Analyze a validated cleaning run; integer pence are authoritative."""
import argparse
import csv
import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

from inspect_data import ROOT, sha256
from project_paths import relative_path


def amount(pence):
    return format(Decimal(int(pence)) / 100, '.2f')


def ratio(a, b, places='0.01'):
    return None if not b else format((Decimal(int(a)) / Decimal(int(b))).quantize(Decimal(places), rounding=ROUND_HALF_UP), 'f')


def analyze(d, start, end):
    d = d.copy()
    d['Month'] = d.InvoiceDate.dt.strftime('%Y-%m')
    conflicts = {c: int(d.groupby('InvoiceNo')[c].nunique(dropna=False).gt(1).sum())
                 for c in ['CustomerID', 'Country', 'Month']}
    if any(conflicts.values()):
        raise ValueError(f'Order attribution needs review: {conflicts}')
    revenue, orders = int(d.LineSalesPence.sum()), d.InvoiceNo.nunique()
    known = d[d.CustomerID.notna()]
    customers = known.groupby('CustomerID', sort=True).agg(
        CompletedOrders=('InvoiceNo', 'nunique'), UnitsSold=('Quantity', 'sum'), RevenuePence=('LineSalesPence', 'sum')).reset_index()
    customers['RevenueGBP'] = customers.pop('RevenuePence').map(amount)
    customers['RepeatCustomer'] = customers.CompletedOrders.ge(2).astype(int)
    repeat = int(customers.RepeatCustomer.sum())
    kpi = pd.DataFrame([{'RevenueGBP': amount(revenue), 'CompletedOrders': orders,
                         'UnitsSold': int(d.Quantity.sum()), 'AverageOrderValueGBP': ratio(revenue, orders * 100),
                         'KnownUniqueCustomers': len(customers)}])
    repeat_summary = pd.DataFrame([{'KnownCustomers': len(customers), 'RepeatCustomers': repeat,
                                   'OneOrderCustomers': len(customers) - repeat,
                                   'RepeatCustomerPct': ratio(repeat * 100, len(customers)),
                                   'KnownCustomerOrders': known.InvoiceNo.nunique(),
                                   'KnownCustomerRevenueGBP': amount(known.LineSalesPence.sum())}])
    months = pd.period_range(start.to_period('M'), end.to_period('M'), freq='M').astype(str)
    monthly = d.groupby('Month').agg(RevenuePence=('LineSalesPence', 'sum'), CompletedOrders=('InvoiceNo', 'nunique')).reindex(months, fill_value=0)
    monthly.index.name = 'Month'
    monthly = monthly.reset_index()
    statuses = []
    for month in months:
        if month == str(start.to_period('M')):
            statuses.append('partial_start' if start.day > 1 else 'boundary_start_day_1_unverified')
        elif month == str(end.to_period('M')):
            statuses.append('partial_end' if end.day < end.days_in_month else 'boundary_end_last_day_unverified')
        else:
            statuses.append('interior_calendar_month')
    monthly['CoverageStatus'] = statuses
    monthly['RevenueGBP'] = monthly.RevenuePence.map(amount)
    prev = monthly.RevenuePence.shift()
    monthly['ObservedMoMChangeGBP'] = [None if pd.isna(p) else amount(int(c)-int(p)) for c, p in zip(monthly.RevenuePence, prev)]
    monthly['ObservedMoMPct'] = [None if pd.isna(p) else ratio((int(c)-int(p))*100, int(p)) for c, p in zip(monthly.RevenuePence, prev)]
    monthly['ComparableMoMPct'] = [v if i > 0 and statuses[i] == statuses[i-1] == 'interior_calendar_month' else None for i, v in enumerate(monthly.ObservedMoMPct)]
    monthly = monthly.drop(columns='RevenuePence')
    products = d.groupby('StockCode', sort=True).agg(RevenuePence=('LineSalesPence', 'sum'), UnitsSold=('Quantity', 'sum')).reset_index()
    # Deterministic label: binary/Unicode smallest observed description, not an invented category.
    labels = d.dropna(subset=['Description']).groupby('StockCode').Description.min()
    products['Description'] = products.StockCode.map(labels)
    top_rev = products.sort_values(['RevenuePence', 'StockCode'], ascending=[False, True]).head(10).copy()
    top_qty = products.sort_values(['UnitsSold', 'StockCode'], ascending=[False, True]).head(10).copy()
    for table in [top_rev, top_qty]:
        table['RevenueGBP'] = table.pop('RevenuePence').map(amount)
        table.insert(0, 'Rank', range(1, len(table)+1))
    countries = d.groupby('Country', dropna=False).agg(RevenuePence=('LineSalesPence', 'sum'), CompletedOrders=('InvoiceNo', 'nunique')).reset_index()
    countries = countries.sort_values(['RevenuePence', 'Country'], ascending=[False, True])
    countries['RevenueGBP'] = countries.pop('RevenuePence').map(amount)
    tables = {'kpis': kpi, 'monthly': monthly, 'top_products_revenue': top_rev,
              'top_products_quantity': top_qty, 'countries': countries,
              'customer_purchases': customers, 'repeat_purchasing': repeat_summary}
    assert sum(Decimal(v) for v in monthly.RevenueGBP) == Decimal(amount(revenue))
    assert sum(Decimal(v) for v in countries.RevenueGBP) == Decimal(amount(revenue))
    assert int(countries.CompletedOrders.sum()) == orders
    assert int(monthly.CompletedOrders.sum()) == orders
    assert int(customers.CompletedOrders.sum()) == known.InvoiceNo.nunique()
    assert repeat + int(repeat_summary.OneOrderCustomers.iloc[0]) == len(customers)
    return tables, conflicts


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, default=ROOT/'data/processed/cleaning_20261017T162742_974298Z/completed_sales.csv')
    p.add_argument('--inspection', type=Path, default=ROOT/'reports/inspection_20261017T162126_340038Z/inspection.json')
    args = p.parse_args()
    source = args.input.resolve()
    summary_path = ROOT/'reports'/source.parent.name/'cleaning_summary.json'
    validated = json.loads(summary_path.read_text())
    if 'output_sha256' in validated:
        assert sha256(source) == validated['output_sha256']['completed_sales.csv'], 'Cleaned output hash changed'
    inspection = json.loads(args.inspection.read_text())
    assert inspection['sha256'] == validated['source_sha256']
    coverage = inspection['sheets']['Online Retail']['date_range']
    start, end = pd.Timestamp(coverage['min']), pd.Timestamp(coverage['max'])
    d = pd.read_csv(source, dtype={c: 'string' for c in ['InvoiceNo', 'StockCode', 'CustomerID', 'Description', 'Country', 'UnitPrice', 'LineSalesGBP']}, parse_dates=['InvoiceDate'])
    d['Quantity'] = pd.to_numeric(d.Quantity)
    assert d.Quantity.mod(1).eq(0).all()
    d['Quantity'] = d.Quantity.astype('int64')
    assert len(d) == validated['completed_sales_rows']
    assert amount(d.LineSalesPence.sum()) == validated['completed_sales_GBP']
    assert d.SourceRow.is_unique and d.Quantity.gt(0).all()
    assert d.UnitPrice.map(Decimal).gt(0).all()
    assert not d.InvoiceNo.str.upper().str.startswith('C').any()
    assert d.CustomerMetricsEligible.equals(d.CustomerID.notna())
    assert not d.Flag_exact_duplicate_extra.any()
    assert d.LineSalesGBP.tolist() == d.LineSalesPence.map(amount).tolist()
    tables, conflicts = analyze(d, start, end)
    out = ROOT/'reports'/datetime.now(timezone.utc).strftime('analysis_%Y%m%dT%H%M%S_%fZ')
    out.mkdir(exist_ok=False)
    for name, table in tables.items():
        table.to_csv(out/f'{name}.csv', index=False)
    export = d[['SourceRow', 'InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate', 'UnitPrice', 'CustomerID', 'Country', 'LineSalesPence', 'LineSalesGBP']]
    # Tab separated, no quoting; escape no data: fail if source contains unsafe import characters.
    assert not export.astype('string').apply(lambda c: c.str.contains(r'[\t\r\n\\]', na=False)).any().any()
    export.to_csv(out/'sql_import.tsv', sep='\t', index=False, quoting=csv.QUOTE_NONE, lineterminator='\n')
    load = f"""-- UNEXECUTED. First create a NEW database using sql/01_schema.sql.
-- Only load into the empty table in that newly created database. Do not use --force.
LOAD DATA LOCAL INFILE '{(out/'sql_import.tsv').as_posix()}'
INTO TABLE sales CHARACTER SET utf8mb4
FIELDS TERMINATED BY '\\t' ESCAPED BY '' LINES TERMINATED BY '\\n' IGNORE 1 LINES
(SourceRow, InvoiceNo, StockCode, @description, Quantity, InvoiceDate, UnitPrice,
 @customer, @country, LineSalesPence, LineSalesGBP)
SET Description=NULLIF(@description,''), CustomerID=NULLIF(@customer,''), Country=NULLIF(@country,'');
SHOW WARNINGS;
INSERT INTO analysis_metadata VALUES (1, '{start}', '{end}', '{sha256(source)}');
"""
    (out/'02_load.sql').write_text(load, encoding='utf-8')
    metadata = {'input': relative_path(source), 'input_sha256': sha256(source), 'cleaning_summary': relative_path(summary_path),
                'coverage_start': str(start), 'coverage_end': str(end), 'invoice_conflicts': conflicts,
                'sql_status': 'UNEXECUTED: this Python script does not connect to or execute SQL on any database.',
                'validation': 'PASS: cleaning totals, identifiers/eligibility, money consistency, monthly/country revenue and orders, known customer order reconciliation.'}
    (out/'analysis_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    k = tables['kpis'].iloc[0]
    r = tables['repeat_purchasing'].iloc[0]
    top = tables['top_products_revenue'].iloc[0]
    country = tables['countries'].iloc[0]
    full = tables['monthly'].query("CoverageStatus == 'interior_calendar_month'").sort_values('RevenueGBP', key=lambda s:s.map(Decimal), ascending=False).iloc[0]
    lines = ['# Completed-sales analysis', '',
             f"Observed revenue: GBP {k.RevenueGBP}; distinct completed orders: {k.CompletedOrders:,}; units sold: {k.UnitsSold:,}; AOV: GBP {k.AverageOrderValueGBP}; known unique customers: {k.KnownUniqueCustomers:,}.", '',
             f"Among {r.KnownCustomers:,} known customers, {r.RepeatCustomers:,} ({r.RepeatCustomerPct}%) placed at least two distinct completed orders in this observation window. This is not lifetime retention or a cohort repeat rate.", '',
             f"The highest-revenue product code is {top.StockCode} ({top.Description}), GBP {top.RevenueGBP}. {country.Country} has the highest country revenue, GBP {country.RevenueGBP}, across {country.CompletedOrders:,} orders.", '',
             f"The highest-revenue interior calendar month is {full.Month}, GBP {full.RevenueGBP}.", '',
             f"Raw coverage: {start} to {end}. December 2010 starts on day 1: it is not visibly truncated by calendar day, but first-day and source completeness are unverified. December 2011 ends on day 9 and is partial. Interior months are treated as calendar-covered, not independently verified complete.", '',
             'Monthly tables show observed changes for transparency. ComparableMoMPct is suppressed whenever either month is a boundary month; do not interpret partial-versus-full changes as growth or decline.', '',
             'Definitions: revenue sums line-rounded integer pence; AOV = revenue / distinct eligible InvoiceNo, rounded half-up to two decimals. Units sum Quantity. Product ranks group by StockCode, with code ascending as the tie-break. Product descriptions use the smallest observed text label and can vary for one code. Countries use distinct invoice counts. Repeat purchasing uses known IDs only and at least two distinct invoices, not multiple lines of one invoice.', '',
             'Completed-sales revenue excludes cancellations and negative adjustments and is not net revenue. Anonymous sales are retained in overall metrics; customer metrics omit missing IDs. No customer identities are inferred. No categories, costs, profit or return matching are invented.', '',
             'Limitations: analytical exact-duplicate removal and stock-code exclusions affect totals. Missing IDs limit customer analysis. The window censors purchases before/after coverage; invoices are eligible merchandise orders rather than all source transactions. Large transactions are retained and may influence rankings. These observations do not establish why patterns occurred.', '',
             'Recommendation: use interior-month comparisons in the dashboard, expose boundary labels and metric definitions, and investigate unusual high-value orders before drawing business conclusions. Promotions, seasonality or customer mix are possible explanations only; they were not tested here.', '',
             metadata['validation'], '', 'SQL status: ' + metadata['sql_status'], '',
             'Tables and SQL import files are alongside this report. SQL reconciliation has not been performed.']
    (out/'findings.md').write_text('\n'.join(lines), encoding='utf-8')
    print(out)
    print(tables['kpis'].to_string(index=False))
    print(tables['repeat_purchasing'].to_string(index=False))
    print(tables['monthly'].to_string(index=False))


if __name__ == '__main__':
    main()
