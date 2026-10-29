"""Read-only workbook inspection. Run from any directory; never cleans data."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def inspect(path):
    before = sha256(path)
    result = {'source': str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
              'sha256': before, 'generated_utc': datetime.now(timezone.utc).isoformat(),
              'definitions': {'duplicates': 'All columns equal, counting extra occurrences after the first.',
                              'unique': 'Distinct nonmissing identifiers; no trimming or case normalization.',
                              'cancellation': 'InvoiceNo starts with C, case-insensitive; whitespace is not trimmed.'},
              'sheets': {}}
    with pd.ExcelFile(path, engine='openpyxl') as book:
        result['sheet_names'] = book.sheet_names
        for name in book.sheet_names:
            # Read identifiers as strings; preserve missing values and all rows.
            df = pd.read_excel(book, sheet_name=name,
                               dtype={c: 'string' for c in ['InvoiceNo', 'StockCode', 'CustomerID']})
            s = {'row_count': len(df), 'columns': list(df.columns),
                 'dtypes': {c: str(t) for c, t in df.dtypes.items()},
                 'missing_values': {c: int(n) for c, n in df.isna().sum().items()},
                 'exact_duplicate_extra_rows': int(df.duplicated().sum()),
                 'all_rows_in_duplicate_groups': int(df.duplicated(keep=False).sum())}
            s['unique_nonmissing'] = {c: int(df[c].nunique()) for c in
                                     ['InvoiceNo', 'StockCode', 'CustomerID', 'Country'] if c in df}
            if 'InvoiceDate' in df:
                dates = pd.to_datetime(df['InvoiceDate'], errors='coerce')
                s['date_range'] = {'min': str(dates.min()), 'max': str(dates.max()),
                                   'invalid_nonmissing': int((df['InvoiceDate'].notna() & dates.isna()).sum())}
            for col in ['Quantity', 'UnitPrice']:
                if col in df:
                    nums = pd.to_numeric(df[col], errors='coerce')
                    s[col] = {'negative': int((nums < 0).sum()), 'zero': int((nums == 0).sum()),
                              'min': float(nums.min()), 'max': float(nums.max()),
                              'invalid_nonmissing': int((df[col].notna() & nums.isna()).sum())}
            if 'InvoiceNo' in df:
                cancel = df['InvoiceNo'].str.upper().str.startswith('C', na=False)
                s['cancellations'] = {'rows': int(cancel.sum()),
                                      'unique_invoices': int(df.loc[cancel, 'InvoiceNo'].nunique()),
                                      'examples': df.loc[cancel, 'InvoiceNo'].drop_duplicates().head(5).tolist()}
                qty = pd.to_numeric(df['Quantity'], errors='coerce')
                s['cancellations']['negative_quantity_without_C'] = int(((qty < 0) & ~cancel).sum())
                s['cancellations']['C_with_nonnegative_quantity'] = int((cancel & (qty >= 0)).sum())
            s['identifier_checks'] = {}
            for col in ['InvoiceNo', 'StockCode', 'CustomerID']:
                if col in df:
                    values = df[col].dropna()
                    s['identifier_checks'][col] = {
                        'examples': values.drop_duplicates().head(8).tolist(),
                        'surrounding_whitespace_rows': int(values.ne(values.str.strip()).sum()),
                        'nonnumeric_examples': values[~values.str.fullmatch(r'\d+', na=False)].drop_duplicates().head(12).tolist()}
            result['sheets'][name] = s
    result['source_unchanged'] = before == sha256(path)
    if not result['source_unchanged']:
        raise RuntimeError('Source checksum changed during inspection')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=ROOT / 'data/raw/Online Retail.xlsx')
    args = parser.parse_args()
    result = inspect(args.input.resolve())
    # Each run gets its own output directory so earlier reports are preserved.
    out = ROOT / 'reports' / datetime.now(timezone.utc).strftime('inspection_%Y%m%dT%H%M%S_%fZ')
    out.mkdir(parents=True, exist_ok=False)
    (out / 'inspection.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    lines = ['# Retail workbook inspection', '', f"Source: `{result['source']}`",
             f"SHA-256: `{result['sha256']}`", '',
             'Read-only inspection; no rows removed or values changed.', '',
             f"Sheets: {', '.join(result['sheet_names'])}", '']
    for name, stats in result['sheets'].items():
        lines += [f'## {name}', '', '```json', json.dumps(stats, indent=2), '```', '']
    lines += ['Source checksum verified unchanged.', '',
              'Counts refer to invoice line items, not orders. Unique counts exclude missing values.',
              'Duplicate count means extra identical rows after the first. Dates are timezone-naive source values.',
              'Identifiers are loaded as strings, not measures. No whitespace or case normalization is applied.']
    (out / 'inspection.md').write_text('\n'.join(lines), encoding='utf-8')
    print(out)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
