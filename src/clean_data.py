"""Reproducible, audited completed-sales view; never edits the source workbook."""
import argparse
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

import pandas as pd

from inspect_data import ROOT, sha256

COLS = ['InvoiceNo', 'StockCode', 'Description', 'Quantity', 'InvoiceDate',
        'UnitPrice', 'CustomerID', 'Country']
# Explicit reviewed codes only. Alphabetic suffixes on normal product codes are valid.
NONPRODUCT = {'POST', 'DOT', 'M', 'D', 'C2', 'BANK CHARGES', 'AMAZONFEE',
              'B', 'CRUK', 'S', 'm', 'gift_0001_10', 'gift_0001_20',
              'gift_0001_30', 'gift_0001_40', 'gift_0001_50'}
REVIEWED_PRODUCTS = {'PADS', 'DCGS0003', 'DCGS0004', 'DCGS0069', 'DCGS0070',
                     'DCGS0076', 'DCGSSBOY', 'DCGSSGIRL'}


def money_cents(quantity, price):
    try:
        q, p = Decimal(str(quantity)), Decimal(str(price))
        if not q.is_finite() or not p.is_finite():
            return pd.NA
        return int((q * p).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) * 100)
    except (InvalidOperation, ValueError, TypeError):
        return pd.NA


def gbp(cents):
    return '' if pd.isna(cents) else format(Decimal(int(cents)) / 100, '.2f')


def transform(raw):
    d = raw[COLS].copy()
    for col in ['InvoiceNo', 'StockCode', 'CustomerID']:
        d[col] = d[col].astype('string')
    duplicate = d.duplicated(subset=COLS, keep='first')
    group = d.duplicated(subset=COLS, keep=False)
    d.insert(0, 'SourceRow', range(2, len(d) + 2))
    flags = {}
    for col in COLS:
        missing = d[col].isna() | d[col].astype('string').str.strip().eq('').fillna(False)
        flags['missing_' + col] = missing
    for col in ['Quantity', 'UnitPrice', 'InvoiceDate']:
        d['Original_' + col] = d[col]
        if col == 'InvoiceDate':
            parsed = pd.to_datetime(d[col], errors='coerce', format='mixed')
        else:
            parsed = pd.to_numeric(d[col], errors='coerce')
            parsed = parsed.where(parsed.abs() != float('inf'))
        flags['conversion_failure_' + col] = ~flags['missing_' + col] & parsed.isna()
        d[col] = parsed
    flags['fractional_quantity'] = d.Quantity.notna() & d.Quantity.mod(1).ne(0)
    flags['cancellation'] = d.InvoiceNo.str.strip().str.upper().str.startswith('C', na=False)
    flags['negative_quantity'] = d.Quantity.lt(0)
    flags['zero_quantity'] = d.Quantity.eq(0)
    flags['nonpositive_price'] = d.UnitPrice.le(0)
    flags['exact_duplicate_extra'] = duplicate
    flags['exact_duplicate_group'] = group
    flags['nonproduct_code'] = d.StockCode.isin(NONPRODUCT)
    flags['unreviewed_stock_code'] = ~(d.StockCode.str.fullmatch(r'[0-9]{5}[A-Za-z]*', na=False) | d.StockCode.isin(NONPRODUCT | REVIEWED_PRODUCTS))
    f = pd.DataFrame(flags, index=d.index).fillna(False).astype(bool)
    d['LineSalesPence'] = pd.array([money_cents(q, p) for q, p in
                                  zip(d.Original_Quantity, d.Original_UnitPrice)], dtype='Int64')
    d['LineSalesGBP'] = d.LineSalesPence.map(gbp)
    d['CustomerMetricsEligible'] = ~f.missing_CustomerID
    invalid = f[[c for c in f if c.startswith('conversion_failure_')]].any(axis=1)
    invalid |= f[['missing_InvoiceNo', 'missing_StockCode', 'missing_Quantity',
                  'missing_UnitPrice', 'missing_InvoiceDate', 'fractional_quantity']].any(axis=1)
    rules = [('invalid_required_fields', invalid), ('cancellation', f.cancellation),
             ('nonpositive_quantity', d.Quantity.le(0)), ('nonpositive_price', f.nonpositive_price),
             ('nonproduct_or_unreviewed_code', f.nonproduct_code | f.unreviewed_stock_code),
             ('exact_duplicate_extra', f.exact_duplicate_extra)]
    keep = pd.Series(True, index=d.index)
    stages = []
    for name, mask in rules:
        removed = keep & mask
        before = int(keep.sum())
        cents = int(d.loc[removed, 'LineSalesPence'].sum())
        keep &= ~mask
        stages.append({'rule': name, 'before': before, 'excluded': int(removed.sum()),
                       'after': int(keep.sum()), 'excluded_signed_GBP': gbp(cents),
                       'excluded_absolute_GBP': gbp(int(d.loc[removed, 'LineSalesPence'].abs().sum())),
                       'excluded_unvalued_rows': int(d.loc[removed, 'LineSalesPence'].isna().sum())})
    d['IncludedCompletedSales'] = keep
    d['AuditReasons'] = f.apply(lambda row: '|'.join(row.index[row]), axis=1)
    d['ExclusionReasons'] = pd.DataFrame({name: mask for name, mask in rules}).apply(
        lambda row: '|'.join(row.index[row]), axis=1)
    d = pd.concat([d, f.add_prefix('Flag_')], axis=1)
    return d, stages


def validate(d, raw):
    sales = d[d.IncludedCompletedSales]
    assert len(d) == len(raw) and d.SourceRow.is_unique
    assert sales.Quantity.gt(0).all() and sales.UnitPrice.gt(0).all()
    assert not sales.Flag_cancellation.any()
    assert not sales.Flag_nonproduct_code.any() and not sales.Flag_unreviewed_stock_code.any()
    assert not sales.Flag_exact_duplicate_extra.any()
    assert sales[['InvoiceNo', 'StockCode', 'InvoiceDate']].notna().all().all()
    assert d.CustomerID.isna().equals(raw.CustomerID.isna())
    assert sales.CustomerMetricsEligible.equals(sales.CustomerID.notna())
    assert not d.loc[~d.IncludedCompletedSales, 'ExclusionReasons'].eq('').any()
    assert d.LineSalesPence.sum() == (sales.LineSalesPence.sum() + d.loc[~d.IncludedCompletedSales, 'LineSalesPence'].sum())
    assert sales.InvoiceNo.duplicated().any(), 'Multi-line invoices must survive'
    return ['PASS: row provenance, eligibility, missing customer preservation, duplicate policy,',
            'identifier/date completeness, multi-line invoices and integer-pence reconciliation.']


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, default=ROOT / 'data/raw/Online Retail.xlsx')
    args = p.parse_args()
    source = args.input.resolve()
    before = sha256(source)
    raw = pd.read_excel(source, sheet_name='Online Retail', engine='openpyxl',
                        dtype={c: 'string' for c in ['InvoiceNo', 'StockCode', 'CustomerID']})
    d, stages = transform(raw)
    checks = validate(d, raw)
    assert sha256(source) == before, 'Raw workbook changed'
    run = datetime.now(timezone.utc).strftime('cleaning_%Y%m%dT%H%M%S_%fZ')
    out, report = ROOT / 'data/processed' / run, ROOT / 'reports' / run
    out.mkdir(parents=True, exist_ok=False)
    report.mkdir(parents=True, exist_ok=False)
    sales = d[d.IncludedCompletedSales]
    audit = d[d.AuditReasons.ne('')]
    sales.to_csv(out / 'completed_sales.csv', index=False)
    audit.to_csv(out / 'audit.csv', index=False)
    # CSV has no type metadata: explicitly force text IDs and blank IDs to missing on import.
    back = pd.read_csv(out / 'completed_sales.csv', dtype={c: 'string' for c in ['InvoiceNo', 'StockCode', 'CustomerID']})
    assert len(back) == len(sales) and back.CustomerID.isna().sum() == sales.CustomerID.isna().sum()
    assert back.InvoiceNo.tolist() == sales.InvoiceNo.tolist()
    unusual = raw[~raw.StockCode.str.fullmatch(r'[0-9]{5}', na=False)]
    profile = unusual.groupby(['StockCode', 'Description'], dropna=False).agg(
        Rows=('StockCode', 'size'), MinQuantity=('Quantity', 'min'), MaxQuantity=('Quantity', 'max'),
        MinPrice=('UnitPrice', 'min'), MaxPrice=('UnitPrice', 'max')).reset_index()
    profile.to_csv(report / 'stock_code_review.csv', index=False)
    summary = {'source': str(source), 'source_sha256': before, 'raw_unchanged': True,
               'input_rows': len(d), 'completed_sales_rows': len(sales), 'audit_rows': len(audit),
               'excluded_rows': int((~d.IncludedCompletedSales).sum()),
               'output_sha256': {name: sha256(out / name) for name in ['completed_sales.csv', 'audit.csv']},
               'completed_sales_GBP': gbp(int(sales.LineSalesPence.sum())),
               'retained_missing_customer_rows': int(sales.CustomerID.isna().sum()),
               'flag_counts': {c: int(d[c].sum()) for c in d if c.startswith('Flag_')},
               'stages': stages, 'validation': checks + ['PASS: source hash and CSV round-trip identifiers/missing customers.']}
    (report / 'cleaning_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    lines = ['# Cleaning report', '',
             'Completed-sales revenue excludes cancellations and negative adjustments. It is not net revenue.', '',
             'Money: Decimal(str(source value)), Quantity × UnitPrice, round each line to GBP 0.01',
             'using ROUND_HALF_UP, then sum integer pence. No unit-price pre-rounding. Unvalued lines',
             'are counted separately, never treated as zero economic impact.', '',
             'Duplicate policy: remove only extra exact matches across all eight original columns, keeping',
             'the first source row. This is an explicit analytical assumption, not proof of an error.',
             'All duplicate-group members are audited. Repeated InvoiceNo alone is never removed.', '',
             'Missing customer, description or country alone does not exclude an otherwise valid product sale.',
             'CustomerMetricsEligible must be true for customer metrics. Missing customer IDs remain blank.', '',
             'Stock-code policy: observed charge/adjustment codes are excluded via the explicit NONPRODUCT',
             'list in src/clean_data.py. Normal five-digit product codes with alphabetic suffixes remain.',
             'Unexpected formats are quarantined for review rather than silently classified as products.',
             'See stock_code_review.csv and reports/stock_code_policy.md for observed descriptions.', '',
             'Sequential exclusions below are disjoint; flag counts overlap. Signed amounts describe',
             'excluded source line values, not lost revenue or confirmed returns. Removing negative lines',
             'increases the remaining signed total. Absolute amounts show scale without offsetting signs.', '',
             '| Rule | Before | Excluded | After | Excluded signed GBP | Absolute GBP | Unvalued |',
             '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for s in stages:
        lines.append('| ' + ' | '.join(str(v) for v in s.values()) + ' |')
    lines += ['', '```json', json.dumps(summary, indent=2), '```', '',
              'Audit includes flagged retained rows as well as excluded rows; use IncludedCompletedSales',
              'and ExclusionReasons to distinguish them. SourceRow is the original Excel row including header.',
              'Original numeric/date values are retained in audit columns. No categories, costs, profit,',
              'outlier caps or return-to-sale matching were created. December 2011 is partial.', '',
              'CSV import: set InvoiceNo, StockCode and CustomerID to Text in Excel/Power BI or VARCHAR',
              'in MySQL/MariaDB; blank CustomerID means missing. LineSalesPence is the authoritative',
              'integer money field; LineSalesGBP is an exact two-decimal display/export field.']
    (report / 'cleaning_report.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(summary, indent=2))
    print(f'Outputs: {out}\nReport: {report}')


if __name__ == '__main__':
    main()
