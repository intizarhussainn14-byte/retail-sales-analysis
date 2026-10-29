"""Reconcile serialized Power BI inputs with verified outputs, without a DAX engine."""
import argparse
import json
from decimal import Decimal
from pathlib import Path

import pandas as pd

from analyze_sales import analyze, amount, ratio
from inspect_data import ROOT, sha256
from project_paths import project_path, relative_path


def comparable_strings(frame):
    return frame.astype('string').fillna('').reset_index(drop=True)


def validate(package):
    manifest = json.loads((package/'manifest.json').read_text(encoding='utf-8'))
    analysis = project_path(manifest['analysis_folder'], 'reports')
    meta = json.loads((analysis/'analysis_metadata.json').read_text())
    types = {c: 'string' for c in ['InvoiceNo', 'StockCode', 'CustomerID', 'Country',
                                  'Description', 'LineSalesGBP', 'StockCodeUTF8Hex']}
    tables = {}
    for name, entry in manifest['tables'].items():
        source = package/'data'/f'{name}.csv'
        assert sha256(source) == entry['sha256'], f'{name}: hash changed'
        tables[name] = pd.read_csv(source, dtype=types)
        assert len(tables[name]) == entry['rows']
        assert tables[name].columns.tolist() == entry['columns']
    fact, quality, dates, products, countries, steps = [tables[n] for n in
        ['FactSales', 'QualityRows', 'DimDate', 'DimProduct', 'DimCountry', 'CleaningSteps']]
    fact['InvoiceDate'] = pd.to_datetime(fact.InvoiceDate)
    calendar = pd.to_datetime(dates.Date)
    assert calendar.equals(pd.Series(pd.date_range(calendar.min(), calendar.max()))), 'Date gaps'
    assert fact.SourceRow.is_unique and quality.SourceRow.is_unique
    assert fact.Quantity.gt(0).all() and not fact.InvoiceNo.str.upper().str.startswith('C').any()
    assert fact.CustomerMetricsEligible.eq(fact.CustomerID.notna().astype(int)).all()
    # CSV may serialize 1.20 as 1.2; compare money, not trailing-zero spelling.
    assert fact.LineSalesGBP.map(Decimal).tolist() == fact.LineSalesPence.map(lambda p: Decimal(int(p))/100).tolist()
    assert products.ProductKey.is_unique and products.ProductLabel.str.casefold().is_unique
    assert products.StockCodeUTF8Hex.map(lambda s: bytes.fromhex(s).decode('utf-8')).tolist() == products.StockCode.tolist()
    assert countries.Country.str.casefold().is_unique
    for field in ['InvoiceNo', 'CustomerID']:
        values = fact[field].dropna().drop_duplicates()
        assert values.str.casefold().is_unique, f'{field}: engine text-case collision requires review'
    for data in [fact, quality]:
        assert data.SaleDate.isin(dates.Date).all()
        assert data.ProductKey.isin(products.ProductKey).all()
        assert data.Country.isin(countries.Country).all()
        mapped = data.ProductKey.map(products.set_index('ProductKey').StockCode)
        assert mapped.tolist() == data.StockCode.tolist()
    assert set(fact.SourceRow) == set(quality.loc[quality.IsIncluded.eq(1), 'SourceRow'])
    labels = products.set_index('ProductKey').Description
    fact['Description'] = fact.ProductKey.map(labels)
    computed, _ = analyze(fact, pd.Timestamp(meta['coverage_start']), pd.Timestamp(meta['coverage_end']))
    compared = {}
    for name, result in computed.items():
        reference = pd.read_csv(analysis/f'{name}.csv', dtype='string', keep_default_na=False)
        # Match columns; analysis tables already define deterministic ordering.
        pd.testing.assert_frame_equal(comparable_strings(result[reference.columns]),
                                      comparable_strings(reference), check_dtype=False, obj=name)
        compared[name] = {'rows': len(result), 'status': 'PASS', 'sha256': sha256(analysis/f'{name}.csv')}
    cleaning = json.loads(project_path(meta['cleaning_summary'], 'reports').read_text())
    assert len(quality) == cleaning['input_rows']
    assert quality.IsIncluded.eq(0).sum() == cleaning['excluded_rows']
    for col, count in cleaning['flag_counts'].items():
        assert quality[col].sum() == count, col
    for row in steps.itertuples():
        subset = quality[quality.ExclusionRule.eq(row.ExclusionRule)]
        assert len(subset) == row.ExcludedRows
        assert Decimal(amount(subset.LineSalesPence.sum())) == Decimal(str(row.ExcludedSignedGBP))
    scenarios = pd.read_csv(package/'expected_filter_totals.csv', dtype='string')
    ranks = pd.read_csv(package/'expected_filtered_top10.csv', dtype='string')
    for ref in scenarios.itertuples(index=False):
        f = fact[fact.SaleDate.between(ref.DateFrom, ref.DateTo)]
        q = quality[quality.SaleDate.between(ref.DateFrom, ref.DateTo)]
        if ref.Country != '(All)':
            f, q = f[f.Country.eq(ref.Country)], q[q.Country.eq(ref.Country)]
        orders = f.InvoiceNo.nunique()
        customer_orders = f.dropna(subset=['CustomerID']).groupby('CustomerID').InvoiceNo.nunique()
        actual = {'RevenueGBP': amount(f.LineSalesPence.sum()), 'Orders': orders,
                  'Units': f.Quantity.sum(), 'AOV_GBP': ratio(f.LineSalesPence.sum(), orders*100),
                  'KnownCustomers': len(customer_orders), 'RepeatCustomers': customer_orders.ge(2).sum(),
                  'RepeatCustomerPct': ratio(customer_orders.ge(2).sum()*100, len(customer_orders)),
                  'RetainedMissingCustomerRows': f.CustomerID.isna().sum(), 'RawRows': len(q),
                  'ExcludedRows': q.IsIncluded.eq(0).sum(),
                  'RawMissingCustomerRows': q.Flag_missing_CustomerID.sum()}
        for key, value in actual.items():
            assert Decimal(str(value)) == Decimal(getattr(ref, key)), f'{ref.Scenario}: {key}'
        assert len(q) == q.IsIncluded.eq(1).sum() + q.IsIncluded.eq(0).sum()
        grouped = f.groupby('ProductKey').agg(RevenuePence=('LineSalesPence', 'sum'), Units=('Quantity', 'sum')).reset_index()
        for metric, column in [('Revenue', 'RevenuePence'), ('Quantity', 'Units')]:
            top = grouped.sort_values([column, 'ProductKey'], ascending=[False, True]).head(10)
            top['StockCode'] = top.ProductKey.map(products.set_index('ProductKey').StockCode)
            ref_top = ranks[ranks.Scenario.eq(ref.Scenario) & ranks.Metric.eq(metric)]
            assert top.StockCode.tolist() == ref_top.StockCode.tolist(), f'{ref.Scenario}: {metric} membership'
            assert top.RevenuePence.map(amount).tolist() == ref_top.RevenueGBP.tolist()
            assert top.Units.astype('string').tolist() == ref_top.Units.tolist()
    # Protect already completed deliverables and their reference-table hashes.
    sql = json.loads((ROOT/'reports/sql_execution_status.json').read_text())
    excel = json.loads((ROOT/'reports/excel_validation.json').read_text())
    assert sql['status'] == excel['status'] == 'PASS'
    assert sha256(ROOT/excel['workbook']) == excel['workbook_sha256'], 'Verified Excel changed'
    assert manifest['sales_sha256'] == meta['input_sha256']
    source = project_path(meta['input'], 'data/processed')
    assert sha256(source) == manifest['sales_sha256']
    assert sha256(source.parent/'audit.csv') == manifest['audit_sha256']
    assert sha256(ROOT/'data/raw/Online Retail.xlsx') == manifest['raw_sha256_from_cleaning']
    for name, result in compared.items():
        assert result['sha256'] == sql['python_tables'][name]['sha256'] == excel['source_hashes'][name]
    spec = json.loads((package/'model_spec.json').read_text())
    assert len(spec['relationships']) == 6 and spec['disconnected'] == ['CleaningSteps']
    result = {'status': 'PASS: Python-side import and reference reconciliation only',
              'package': relative_path(package), 'analysis_tables': compared,
              'scenarios_checked': len(scenarios), 'top_ten_lists_checked': len(scenarios)*2,
              'import_rows': {n: len(t) for n, t in tables.items()},
              'protected_raw_cleaned_audit_excel_hashes': 'PASS',
              'sql_and_excel_reference_hashes': 'PASS',
              'relationship_integrity': 'PASS: six dimension-to-fact foreign keys; continuous calendar',
              'native_report_created': False, 'm_executed': False, 'dax_executed': False,
              'visuals_and_interactions_checked_in_desktop': False}
    (package/'validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    print(json.dumps(validate(parser.parse_args().package.resolve()), indent=2))
