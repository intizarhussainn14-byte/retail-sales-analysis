"""Package validated data for Power BI Desktop; does not create a PBIX file."""
import argparse
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd

from analyze_sales import amount, ratio
from inspect_data import ROOT, sha256
from project_paths import project_path, relative_path
from powerbi_assets import write_assets

DEFAULT_ANALYSIS = ROOT / 'reports/analysis_20261017T163159_486015Z'
IDS = {c: 'string' for c in ['InvoiceNo', 'StockCode', 'CustomerID', 'Country', 'Description']}


def build_dates(start, end):
    dates = pd.DataFrame({'Date': pd.date_range(f'{start.year}-01-01', f'{end.year}-12-31')})
    dates['Year'] = dates.Date.dt.year
    dates['MonthNumber'] = dates.Date.dt.month
    dates['MonthStart'] = dates.Date.dt.to_period('M').dt.to_timestamp()
    dates['YearMonth'] = dates.Date.dt.strftime('%Y-%m')
    dates['YearMonthSort'] = dates.Year * 100 + dates.MonthNumber
    first, last = start.to_period('M'), end.to_period('M')
    def status(date):
        month = date.to_period('M')
        if month < first or month > last:
            return 'Outside observation window'
        if month == first:
            return 'Partial start month' if start.day > 1 else 'Boundary start: day 1; completeness unverified'
        if month == last:
            return 'Partial end month' if end.day < end.days_in_month else 'Boundary end: last day; completeness unverified'
        return 'Interior calendar month'
    dates['CoverageStatus'] = dates.Date.map(status)
    dates['MonthLabel'] = dates.YearMonth + dates.CoverageStatus.map({
        'Partial start month': ' (partial)', 'Partial end month': ' (partial)',
        'Boundary start: day 1; completeness unverified': ' (boundary)',
        'Boundary end: last day; completeness unverified': ' (boundary)'}).fillna('')
    dates['IsComparableMonth'] = dates.CoverageStatus.eq('Interior calendar month').astype(int)
    dates['InObservationWindow'] = dates.Date.between(start.normalize(), end.normalize()).astype(int)
    return dates


def first_exclusion(included, reasons):
    return 'Included' if included else str(reasons).split('|')[0]


def build_products(sales, excluded):
    source = pd.concat([sales[['StockCode', 'Description']], excluded[['StockCode', 'Description']]])
    keys = source.StockCode.dropna().drop_duplicates()
    collisions = keys[keys.str.casefold().duplicated(keep=False)]
    labels = sales.dropna(subset=['Description']).groupby('StockCode').Description.min()
    fallback = source.dropna(subset=['Description']).groupby('StockCode').Description.min()
    products = pd.DataFrame({'StockCode': sorted(keys)})
    products.insert(0, 'ProductKey', range(1, len(products)+1))
    products['Description'] = products.StockCode.map(labels).fillna(products.StockCode.map(fallback))
    products['StockCodeUTF8Hex'] = products.StockCode.map(lambda s: s.encode('utf-8').hex())
    collision_set = set(collisions)
    suffix = products.apply(lambda r: f' [key {r.ProductKey}]' if r.StockCode in collision_set else '', axis=1)
    products['ProductLabel'] = products.StockCode + suffix + ' | ' + products.Description.fillna('(description missing)')
    assert products.ProductKey.is_unique and products.ProductLabel.str.casefold().is_unique
    return products, collisions


def m_type(dtype, column):
    if column in ['SaleDate', 'Date', 'MonthStart']:
        return 'type date'
    if column == 'InvoiceDate':
        return 'type datetime'
    if column.endswith('GBP'):
        return 'Currency.Type'
    if column == 'UnitPrice':
        return 'type number'
    if pd.api.types.is_integer_dtype(dtype):
        return 'Int64.Type'
    return 'type text'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis', type=Path, default=DEFAULT_ANALYSIS)
    args = parser.parse_args()
    analysis = args.analysis.resolve()
    meta = json.loads((analysis/'analysis_metadata.json').read_text())
    sales_path = project_path(meta['input'], 'data/processed')
    audit_path = sales_path.parent/'audit.csv'
    cleaning_path = project_path(meta['cleaning_summary'], 'reports')
    cleaning = json.loads(cleaning_path.read_text())
    if 'output_sha256' in cleaning:
        assert sha256(audit_path) == cleaning['output_sha256']['audit.csv'], 'Audit output hash changed'
    if sha256(sales_path) != meta['input_sha256']:
        raise ValueError('Sales input no longer matches the validated Python analysis')
    sales = pd.read_csv(sales_path, dtype=IDS, parse_dates=['InvoiceDate'])
    audit = pd.read_csv(audit_path, dtype=IDS, parse_dates=['InvoiceDate'])
    excluded = audit.loc[~audit.IncludedCompletedSales].copy()
    flags = [c for c in sales if c.startswith('Flag_')]
    quality_columns = ['SourceRow', 'InvoiceDate', 'Country', 'StockCode', 'CustomerID',
                       'LineSalesPence', 'IncludedCompletedSales', 'ExclusionReasons'] + flags
    quality = pd.concat([sales[quality_columns], excluded[quality_columns]], ignore_index=True).sort_values('SourceRow')
    quality['SaleDate'] = quality.InvoiceDate.dt.normalize()
    quality['IsIncluded'] = quality.pop('IncludedCompletedSales').astype('int64')
    quality['ExclusionRule'] = [first_exclusion(bool(i), r) for i, r in zip(quality.IsIncluded, quality.ExclusionReasons)]
    quality = quality.drop(columns='ExclusionReasons')
    for col in flags:
        quality[col] = quality[col].astype('int64')
    assert len(sales) == cleaning['completed_sales_rows']
    assert len(quality) == cleaning['input_rows'] and quality.SourceRow.is_unique
    assert int(quality.IsIncluded.eq(0).sum()) == cleaning['excluded_rows']
    for col in flags:
        assert int(quality[col].sum()) == cleaning['flag_counts'][col], col
    sales['SaleDate'] = sales.InvoiceDate.dt.normalize()
    sales['CustomerMetricsEligible'] = sales.CustomerMetricsEligible.astype('int64')
    fact = sales[['SourceRow', 'InvoiceNo', 'StockCode', 'Quantity', 'InvoiceDate', 'SaleDate',
                  'UnitPrice', 'CustomerID', 'Country', 'LineSalesPence', 'LineSalesGBP', 'CustomerMetricsEligible']].copy()
    assert fact.Quantity.gt(0).all() and not fact.InvoiceNo.str.upper().str.startswith('C').any()
    assert fact.CustomerMetricsEligible.eq(fact.CustomerID.notna().astype(int)).all()
    assert amount(fact.LineSalesPence.sum()) == cleaning['completed_sales_GBP']
    assert quality.SourceRow.min() == 2 and quality.SourceRow.max() == len(quality)+1
    assert quality.InvoiceDate.notna().all() and quality.Country.notna().all() and quality.StockCode.notna().all()
    for col in ['InvoiceNo', 'Country', 'CustomerID']:
        assert not fact[col].dropna().ne(fact[col].dropna().str.strip()).any()
    # Power BI text comparison is case-insensitive. M/m occur in excluded audit rows.
    # Use a numeric technical relationship key while preserving source code strings in CSV.
    products, case_collision_codes = build_products(sales, excluded)
    key_map = products.set_index('StockCode').ProductKey
    fact['ProductKey'] = fact.StockCode.map(key_map).astype('int64')
    quality['ProductKey'] = quality.StockCode.map(key_map).astype('int64')
    countries = pd.DataFrame({'Country': sorted(quality.Country.unique())})
    start, end = pd.Timestamp(meta['coverage_start']), pd.Timestamp(meta['coverage_end'])
    dates = build_dates(start, end)
    assert dates.Date.is_unique and dates.Date.equals(pd.Series(pd.date_range(dates.Date.min(), dates.Date.max())))
    assert quality.SaleDate.isin(dates.Date).all()
    assert quality.Country.isin(countries.Country).all() and quality.StockCode.isin(products.StockCode).all()
    kpi = pd.read_csv(analysis/'kpis.csv', dtype='string').iloc[0]
    assert fact.InvoiceNo.nunique() == int(kpi.CompletedOrders)
    assert fact.Quantity.sum() == int(kpi.UnitsSold)
    assert fact.CustomerID.nunique() == int(kpi.KnownUniqueCustomers)
    assert ratio(fact.LineSalesPence.sum(), fact.InvoiceNo.nunique()*100) == kpi.AverageOrderValueGBP
    steps = pd.DataFrame(cleaning['stages']).rename(columns={
        'rule': 'ExclusionRule', 'before': 'BeforeRows', 'excluded': 'ExcludedRows', 'after': 'AfterRows',
        'excluded_signed_GBP': 'ExcludedSignedGBP', 'excluded_absolute_GBP': 'ExcludedAbsoluteGBP',
        'excluded_unvalued_rows': 'UnvaluedRows'})
    steps.insert(0, 'Step', range(1, len(steps)+1))
    for row in steps.itertuples():
        subset = quality[quality.ExclusionRule.eq(row.ExclusionRule)]
        assert len(subset) == row.ExcludedRows
        assert Decimal(amount(subset.LineSalesPence.sum())) == Decimal(row.ExcludedSignedGBP)
    run = datetime.now(timezone.utc).strftime('powerbi_%Y%m%dT%H%M%S_%fZ')
    out = ROOT/'dashboard'/run
    data_dir, query_dir = out/'data', out/'power_query'
    data_dir.mkdir(parents=True, exist_ok=False)
    query_dir.mkdir()
    tables = {'FactSales': fact, 'QualityRows': quality, 'DimDate': dates,
              'DimProduct': products, 'DimCountry': countries, 'CleaningSteps': steps}
    for name, table in tables.items():
        # Date-only fields must export as dates, avoiding datetime-to-date locale ambiguity.
        exported = table.copy()
        for col in ['Date', 'SaleDate', 'MonthStart']:
            if col in exported:
                exported[col] = exported[col].dt.strftime('%Y-%m-%d')
        exported.to_csv(data_dir/f'{name}.csv', index=False, encoding='utf-8', lineterminator='\n')
        types = ',\n        '.join('{"'+c+'", '+m_type(table[c].dtype, c)+'}' for c in table)
        query = 'let\n    Source = fnLoadCsv("'+name+'.csv", {\n        '+types+'\n    })\nin\n    Source\n'
        (query_dir/f'{name}.pq').write_text(query, encoding='utf-8')
    (query_dir/'pDataFolder.pq').write_text('"'+data_dir.as_posix()+'"\n', encoding='utf-8')
    (query_dir/'fnLoadCsv.pq').write_text('''(FileName as text, Types as list) as table =>
let
    Raw = Csv.Document(File.Contents(pDataFolder & "/" & FileName),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]),
    Typed = Table.TransformColumnTypes(Headers, Types, "en-GB"),
    NullCustomer = if Table.HasColumns(Typed, "CustomerID") then
        Table.TransformColumns(Typed, {{"CustomerID", each if _ = "" then null else _, type nullable text}})
        else Typed
in
    NullCustomer
''', encoding='utf-8')
    scenarios = [('All', start.normalize(), end.normalize(), None),
                 ('United Kingdom', start.normalize(), end.normalize(), 'United Kingdom'),
                 ('January 2011', pd.Timestamp('2011-01-01'), pd.Timestamp('2011-01-31'), None),
                 ('January 2011 France', pd.Timestamp('2011-01-01'), pd.Timestamp('2011-01-31'), 'France'),
                 ('November 2011 Germany', pd.Timestamp('2011-11-01'), pd.Timestamp('2011-11-30'), 'Germany'),
                 ('Partial December 2011', pd.Timestamp('2011-12-01'), pd.Timestamp('2011-12-09'), None)]
    expected, rankings = [], []
    for name, low, high, country in scenarios:
        s = fact[fact.SaleDate.between(low, high)]
        q = quality[quality.SaleDate.between(low, high)]
        if country:
            s, q = s[s.Country.eq(country)], q[q.Country.eq(country)]
        customer_orders = s.dropna(subset=['CustomerID']).groupby('CustomerID').InvoiceNo.nunique()
        expected.append({'Scenario': name, 'DateFrom': low.date().isoformat(), 'DateTo': high.date().isoformat(),
                         'Country': country or '(All)', 'RevenueGBP': amount(s.LineSalesPence.sum()),
                         'Orders': s.InvoiceNo.nunique(), 'Units': int(s.Quantity.sum()),
                         'AOV_GBP': ratio(s.LineSalesPence.sum(), s.InvoiceNo.nunique()*100),
                         'KnownCustomers': s.CustomerID.nunique(), 'RepeatCustomers': int(customer_orders.ge(2).sum()),
                         'RepeatCustomerPct': ratio(customer_orders.ge(2).sum()*100, len(customer_orders)),
                         'RetainedMissingCustomerRows': int(s.CustomerID.isna().sum()),
                         'RawRows': len(q), 'ExcludedRows': int(q.IsIncluded.eq(0).sum()),
                         'RawMissingCustomerRows': int(q.Flag_missing_CustomerID.sum())})
        agg = s.groupby('StockCode').agg(RevenuePence=('LineSalesPence', 'sum'), Units=('Quantity', 'sum')).reset_index()
        for metric, column in [('Revenue', 'RevenuePence'), ('Quantity', 'Units')]:
            top = agg.sort_values([column, 'StockCode'], ascending=[False, True]).head(10)
            for rank, r in enumerate(top.itertuples(), 1):
                rankings.append({'Scenario': name, 'Metric': metric, 'Rank': rank, 'StockCode': r.StockCode,
                                 'RevenueGBP': amount(r.RevenuePence), 'Units': int(r.Units)})
    pd.DataFrame(expected).to_csv(out/'expected_filter_totals.csv', index=False)
    pd.DataFrame(rankings).to_csv(out/'expected_filtered_top10.csv', index=False)
    products[products.StockCode.isin(case_collision_codes)].to_csv(out/'case_sensitive_product_codes.csv', index=False)
    write_assets(out, tables, scenarios)
    # Validate serialised imports rather than just in-memory data.
    roundtrip = pd.read_csv(data_dir/'FactSales.csv', dtype=IDS)
    assert len(roundtrip) == len(fact) and roundtrip.LineSalesPence.sum() == fact.LineSalesPence.sum()
    assert roundtrip.CustomerID.isna().sum() == fact.CustomerID.isna().sum()
    assert roundtrip.InvoiceNo.equals(fact.InvoiceNo.reset_index(drop=True))
    manifest = {'status': 'DATA AND BUILD INSTRUCTIONS ONLY; NO PBIX CREATED; M AND DAX NOT EXECUTED IN POWER BI',
                'analysis_folder': relative_path(analysis), 'sales_sha256': sha256(sales_path), 'audit_sha256': sha256(audit_path),
                'raw_sha256_from_cleaning': cleaning['source_sha256'], 'coverage_start': str(start), 'coverage_end': str(end),
                'case_collision_codes': len(case_collision_codes),
                'tables': {name: {'rows': len(table), 'columns': list(table.columns),
                                  'sha256': sha256(data_dir/f'{name}.csv')} for name, table in tables.items()},
                'checks': ['Validated analysis source hash and headline totals', 'All raw rows reconstructed exactly once by SourceRow',
                           'All quality flag counts and disjoint exclusion rule amounts match cleaning summary',
                           'Numeric ProductKey and collision-safe ProductLabel preserve case-distinct stock codes; hex records exact source bytes',
                           'Date table continuous, full calendar years, all facts covered',
                           'CSV round-trip preserves revenue pence, identifiers and missing customers',
                           'Six filter scenarios and both top-ten metrics computed from line-level data']}
    (out/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    (out/'START_HERE.md').write_text('''# Power BI Desktop import package

No native PBIX was created. These are validated data exports and unexecuted M queries.
Follow [the Desktop build guide](../POWER_BI_DESKTOP.md) and use the M queries in `power_query/`.
The shared `pDataFolder` points to this package's `data/` directory. Use all six CSV files as specified.
The `expected_filter_totals.csv` and `expected_filtered_top10.csv` files are reconciliation references,
not preaggregated fact tables. DAX measure definitions are in `../measures.dax`.

This package also includes `model_spec.json` (implementation specification, NOT
a native PBIP model), `REPORT_LAYOUT.md` (three-page manual construction plan),
`retail_theme.json`, a frozen `measures.dax` snapshot, and `validate_measures.dax`
for DAX Query view after creating the measures. Use the snapshot for this run.
Run `src/validate_powerbi.py dashboard/POWERBI_RUN` for additional Python-side
reconciliation against completed SQL/Excel evidence; this does not execute DAX.

Refresh All rereads this package; it does not rerun Python. To package a new validated run:
`.\\.venv\\Scripts\\python.exe src/prepare_powerbi.py --analysis reports/analysis_TIMESTAMP`
then update the pDataFolder query in Desktop and reconcile before saving the PBIX.
''', encoding='utf-8')
    print(out)
    print(pd.DataFrame(expected).to_string(index=False))
    print(json.dumps({n: len(t) for n, t in tables.items()}, indent=2))


if __name__ == '__main__':
    main()
