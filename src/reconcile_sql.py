"""Compare exported mysql --batch --raw TSV query results to Python tables."""
import argparse
from decimal import Decimal
from pathlib import Path

import pandas as pd

KEYS = {'kpis': [], 'monthly': ['Month'], 'countries': ['Country'],
        'top_products_revenue': ['Rank'], 'top_products_quantity': ['Rank'],
        'customer_purchases': ['CustomerID'], 'repeat_purchasing': []}


def compare_tables(name, py, sql):
    """Compare by semantic row keys, preserving string IDs and exact decimals."""
    assert py.columns.tolist() == sql.columns.tolist(), f'{name}: columns differ'
    assert py.shape == sql.shape, f'{name}: row counts differ'
    sql = sql.replace('NULL', '')  # mysql --batch renders SQL NULL as this token
    keys = KEYS[name]
    if keys:
        assert not py.duplicated(keys).any(), f'{name}: duplicate Python keys'
        assert not sql.duplicated(keys).any(), f'{name}: duplicate SQL keys'
        py = py.sort_values(keys).reset_index(drop=True)
        sql = sql.sort_values(keys).reset_index(drop=True)
    for col in py:
        for i, (a, b) in enumerate(zip(py[col], sql[col])):
            if col.endswith(('GBP', 'Pct')) or col in ['Rank', 'UnitsSold', 'CompletedOrders', 'KnownUniqueCustomers', 'KnownCustomers', 'RepeatCustomers', 'OneOrderCustomers', 'KnownCustomerOrders', 'RepeatCustomer']:
                same = a == b if not a or not b else Decimal(a) == Decimal(b)
            else:
                same = a == b
            assert same, f'{name}, row {i}, {col}: Python {a!r}, SQL {b!r}'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--python-report', type=Path, required=True)
    p.add_argument('--sql-results', type=Path, required=True)
    args = p.parse_args()
    names = ['kpis', 'monthly', 'countries', 'top_products_revenue',
             'top_products_quantity', 'customer_purchases', 'repeat_purchasing']
    for name in names:
        py = pd.read_csv(args.python_report/f'{name}.csv', dtype='string', keep_default_na=False)
        sql = pd.read_csv(args.sql_results/f'{name}.tsv', sep='\t', dtype='string', keep_default_na=False)
        compare_tables(name, py, sql)
        print(f'PASS: {name} ({len(py)} rows)')


if __name__ == '__main__':
    main()
