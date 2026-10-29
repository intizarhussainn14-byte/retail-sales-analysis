import unittest

import pandas as pd

from analyze_sales import analyze


class AnalysisChecks(unittest.TestCase):
    def test_orders_customer_denominator_and_boundaries(self):
        d = pd.DataFrame({
            'InvoiceNo': ['01', '01', '02', '03', '04'],
            'StockCode': ['A', 'B', 'A', 'B', 'A'],
            'Description': ['Alpha', 'Beta', 'Alpha', 'Beta', 'Alpha'],
            'CustomerID': ['001', '001', '001', None, '002'],
            'Country': ['UK']*5, 'Quantity': [1, 2, 1, 1, 1],
            'InvoiceDate': pd.to_datetime(['2011-01-02', '2011-01-02', '2011-02-01', '2011-03-01', '2011-04-09']),
            'LineSalesPence': [100, 200, 300, 400, 500]})
        tables, _ = analyze(d, pd.Timestamp('2011-01-02'), pd.Timestamp('2011-04-09'))
        k = tables['kpis'].iloc[0]
        self.assertEqual(k.CompletedOrders, 4)
        self.assertEqual(k.RevenueGBP, '15.00')
        self.assertEqual(k.AverageOrderValueGBP, '3.75')
        self.assertEqual(k.KnownUniqueCustomers, 2)
        self.assertEqual(tables['repeat_purchasing'].iloc[0].RepeatCustomerPct, '50.00')
        m = tables['monthly']
        self.assertEqual(m.CoverageStatus.iloc[0], 'partial_start')
        self.assertEqual(m.CoverageStatus.iloc[-1], 'partial_end')
        self.assertIsNone(m.ComparableMoMPct.iloc[1])
        self.assertEqual(m.ComparableMoMPct.iloc[2], '33.33')
        self.assertIsNone(m.ComparableMoMPct.iloc[3])
        d.loc[1, 'Country'] = 'France'
        with self.assertRaises(ValueError):
            analyze(d, pd.Timestamp('2011-01-02'), pd.Timestamp('2011-04-09'))


if __name__ == '__main__':
    unittest.main()
