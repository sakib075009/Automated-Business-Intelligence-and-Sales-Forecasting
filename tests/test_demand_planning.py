
import unittest

import pandas as pd

from src.demand_planning_analysis import (
    classify_demand_periods,
    rank_products,
    rank_regions,
)


class TestDemandPlanning(unittest.TestCase):

    def test_monthly_demand_classification(self):
        monthly = pd.DataFrame({
            "month": ["2026-01-01", "2026-02-01", "2026-03-01"],
            "quantity": [10, 20, 30],
            "revenue": [100, 200, 300],
            "orders": [1, 2, 3],
            "customers": [1, 2, 3],
        })

        result = classify_demand_periods(monthly)

        self.assertEqual(
            result["demand_period"].tolist(),
            ["Low", "Typical", "High"],
        )

    def test_duplicate_months_are_rejected(self):
        monthly = pd.DataFrame({
            "month": ["2026-01-01", "2026-01-01"],
            "quantity": [10, 20],
            "revenue": [100, 200],
            "orders": [1, 2],
            "customers": [1, 2],
        })

        with self.assertRaises(ValueError):
            classify_demand_periods(monthly)

    def test_products_rank_by_quantity(self):
        products = pd.DataFrame({
            "product_id": ["P1", "P2", "P3"],
            "quantity": [100, 300, 200],
            "revenue": [1000, 2000, 1500],
            "profit": [100, 200, 150],
        })

        result = rank_products(products)

        self.assertEqual(
            result["product_id"].tolist(),
            ["P2", "P3", "P1"],
        )
        self.assertEqual(
            result["quantity_rank"].tolist(),
            [1, 2, 3],
        )

    def test_regions_rank_by_quantity(self):
        regions = pd.DataFrame({
            "region_id": ["R1", "R2", "R3"],
            "quantity": [500, 100, 300],
            "revenue": [5000, 1000, 3000],
            "profit": [500, 100, 300],
        })

        result = rank_regions(regions)

        self.assertEqual(
            result["region_id"].tolist(),
            ["R1", "R3", "R2"],
        )

    def test_negative_product_quantity_is_rejected(self):
        products = pd.DataFrame({
            "product_id": ["P1", "P2"],
            "quantity": [100, -10],
            "revenue": [1000, 200],
            "profit": [100, 20],
        })

        with self.assertRaises(ValueError):
            rank_products(products)


if __name__ == "__main__":
    unittest.main()
