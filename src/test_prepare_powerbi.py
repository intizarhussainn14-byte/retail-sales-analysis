import unittest

import pandas as pd

from prepare_powerbi import build_dates, build_products, first_exclusion


class PowerBIPreparationChecks(unittest.TestCase):
    def test_calendar_and_boundary_qualification(self):
        dates = build_dates(pd.Timestamp('2010-12-01 08:26'), pd.Timestamp('2011-12-09 12:50'))
        self.assertEqual(len(dates), 730)
        self.assertEqual(dates.Date.min(), pd.Timestamp('2010-01-01'))
        self.assertEqual(dates.Date.max(), pd.Timestamp('2011-12-31'))
        self.assertEqual(dates.InObservationWindow.sum(), 374)
        self.assertTrue(dates.query("YearMonth == '2010-12'").IsComparableMonth.eq(0).all())
        self.assertTrue(dates.query("YearMonth == '2011-12'").MonthLabel.str.contains('partial').all())
        self.assertTrue(dates.query("YearMonth == '2011-01'").IsComparableMonth.eq(1).all())
        self.assertTrue(dates.Date.is_unique)

    def test_case_sensitive_product_keys_survive_case_insensitive_model(self):
        sales = pd.DataFrame({'StockCode': ['85123a', '85123A', '00100'],
                              'Description': ['Light', 'Light', 'Product']})
        excluded = pd.DataFrame({'StockCode': ['m', 'M'], 'Description': ['Manual', 'Manual']})
        products, collisions = build_products(sales, excluded)
        self.assertEqual(len(products), 5)
        self.assertEqual(len(collisions), 4)
        self.assertTrue(products.ProductLabel.str.casefold().is_unique)
        self.assertEqual(products.StockCode.tolist(), sorted(['85123a', '85123A', '00100', 'm', 'M']))
        self.assertEqual(products.StockCodeUTF8Hex.map(lambda s: bytes.fromhex(s).decode()).tolist(), products.StockCode.tolist())
        again, _ = build_products(sales.iloc[::-1], excluded.iloc[::-1])
        pd.testing.assert_frame_equal(products, again)

    def test_disjoint_exclusion_reason(self):
        self.assertEqual(first_exclusion(False, 'cancellation|nonpositive_quantity|exact_duplicate_extra'), 'cancellation')
        self.assertEqual(first_exclusion(True, pd.NA), 'Included')


if __name__ == '__main__':
    unittest.main()
