import unittest

from project_paths import ROOT, project_path


class PortableMetadataPaths(unittest.TestCase):
    def test_relative_and_old_windows_paths_resolve_to_current_checkout(self):
        expected = ROOT/'data/processed/cleaning_example/completed_sales.csv'
        self.assertEqual(project_path('data/processed/cleaning_example/completed_sales.csv', 'data/processed'), expected)
        self.assertEqual(project_path('F:\\Old checkout\\data\\processed\\cleaning_example\\completed_sales.csv', 'data/processed'), expected)

    def test_unexpected_and_traversal_paths_are_rejected(self):
        for value in ['/private/passwords', 'data/processed/../../../outside.csv']:
            with self.assertRaises(ValueError):
                project_path(value, 'data/processed')


if __name__ == '__main__':
    unittest.main()
