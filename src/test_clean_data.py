"""Business-rule regression checks using deliberately problematic rows."""
import unittest
from decimal import Decimal

import pandas as pd

from clean_data import COLS, money_cents, transform


class CleaningRules(unittest.TestCase):
    def test_rounding(self):
        self.assertEqual(money_cents(3, '0.335'), 101)
        self.assertEqual(money_cents(-3, '0.335'), -101)
        self.assertEqual(money_cents(2, '0.004'), 1)  # round after multiplication
        self.assertTrue(pd.isna(money_cents(1, 'NaN')))

    def test_classification_and_provenance(self):
        base = ['000123', '85123A', 'PRODUCT', 2, '2011-01-01', 1.25, pd.NA, 'UK']
        rows = [base.copy(), base.copy()]
        changes = [ {'StockCode': '71053'}, {'InvoiceNo': 'C123'}, {'Quantity': -2},
                    {'UnitPrice': 0}, {'StockCode': 'POST'}, {'StockCode': 'PADS'},
                    {'StockCode': 'DCGSSBOY'}, {'StockCode': 'UNKNOWN'},
                    {'Quantity': 'bad'}, {'InvoiceDate': 'bad'}, {'UnitPrice': 'bad'},
                    {'CustomerID': '00042'}, {'Description': pd.NA},
                    {'Quantity': 1.5}, {'Quantity': float('inf')} ]
        for change in changes:
            row = dict(zip(COLS, base))
            row.update(change)
            rows.append([row[c] for c in COLS])
        raw = pd.DataFrame(rows, columns=COLS)
        d, stages = transform(raw)
        sales = d[d.IncludedCompletedSales]
        self.assertEqual(sales.index.tolist(), [0, 2, 7, 8, 13, 14])
        self.assertEqual(sales.InvoiceNo.nunique(), 1)  # many lines per invoice retained
        self.assertEqual(d.loc[0, 'InvoiceNo'], '000123')
        self.assertEqual(d.loc[13, 'CustomerID'], '00042')
        self.assertTrue(pd.isna(d.loc[0, 'CustomerID']))
        self.assertFalse(d.loc[0, 'CustomerMetricsEligible'])
        self.assertTrue(d.loc[0, 'Flag_exact_duplicate_group'])
        self.assertFalse(d.loc[0, 'Flag_exact_duplicate_extra'])
        self.assertTrue(d.loc[1, 'Flag_exact_duplicate_extra'])
        for index, field in [(10, 'Quantity'), (11, 'InvoiceDate'), (12, 'UnitPrice'), (16, 'Quantity')]:
            self.assertTrue(d.loc[index, 'Flag_conversion_failure_' + field])
        self.assertTrue(d.loc[14, 'Flag_missing_Description'])
        self.assertTrue(d.loc[~d.IncludedCompletedSales, 'ExclusionReasons'].ne('').all())
        self.assertEqual(sum(s['excluded'] for s in stages) + len(sales), len(raw))
        self.assertEqual(int(d.LineSalesPence.sum()),
                         int(sales.LineSalesPence.sum()) + int(d.loc[~d.IncludedCompletedSales, 'LineSalesPence'].sum()))


if __name__ == '__main__':
    unittest.main()
