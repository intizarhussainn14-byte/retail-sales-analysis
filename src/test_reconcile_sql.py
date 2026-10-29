import unittest

import pandas as pd

from reconcile_sql import compare_tables


class SQLComparisonChecks(unittest.TestCase):
    def test_order_and_decimal_representation_do_not_create_false_discrepancy(self):
        py = pd.DataFrame([['001', '2', '10.20'], ['1', '1', '0.01']],
                          columns=['CustomerID', 'CompletedOrders', 'RevenueGBP'], dtype='string')
        sql = pd.DataFrame([['1', '1', '0.0100'], ['001', '2', '10.2000']], columns=py.columns, dtype='string')
        compare_tables('customer_purchases', py, sql)
        sql.loc[0, 'CustomerID'] = '0001'
        with self.assertRaises(AssertionError):
            compare_tables('customer_purchases', py, sql)

    def test_nulls_normalize_but_real_penny_discrepancies_fail(self):
        py = pd.DataFrame([['2010-12', '775638.36', '']],
                          columns=['Month', 'RevenueGBP', 'ComparableMoMPct'], dtype='string')
        sql = pd.DataFrame([['2010-12', '775638.3600', 'NULL']], columns=py.columns, dtype='string')
        compare_tables('monthly', py, sql)
        sql.loc[0, 'RevenueGBP'] = '775638.37'
        with self.assertRaises(AssertionError):
            compare_tables('monthly', py, sql)


if __name__ == '__main__':
    unittest.main()
