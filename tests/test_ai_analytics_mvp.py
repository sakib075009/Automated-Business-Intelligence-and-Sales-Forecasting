import csv
import tempfile
import unittest
from pathlib import Path

from src.ai_analytics_mvp import generate_insights, number


class TestAIAnalyticsMVP(unittest.TestCase):

    def write_csv(self, folder, filename, rows):
        path = folder / filename
        with path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def create_inputs(self, folder, revenue_change="-12"):
        self.write_csv(folder, "business_kpi_summary.csv", [{
            "Metric": "Revenue",
            "Current_Month": "2025-12",
            "Previous_Month": "2025-11",
            "Current_Value": "88",
            "Previous_Value": "100",
            "Change_Pct": revenue_change,
        }])

        self.write_csv(folder, "daily_sales_anomalies.csv", [{
            "date": "2025-12-31",
            "daily_revenue": "50",
            "robust_z_score": "-5.5",
            "anomaly_type": "Low Revenue",
        }])

        self.write_csv(folder, "forecast_model_comparison.csv", [
            {"model": "Model A", "MAPE": "8.0"},
            {"model": "Model B", "MAPE": "12.0"},
        ])

        self.write_csv(folder, "customer_rfm_summary.csv", [{
            "Customer_Segment": "Champions",
            "Revenue_Contribution_Percentage": "40",
        }])

        self.write_csv(folder, "sales_scenario_results.csv", [
            {"Scenario": "Baseline", "Total_Profit": "1000"},
            {"Scenario": "Combined Downside", "Total_Profit": "700"},
        ])

        self.write_csv(folder, "demand_planning_recommendations.csv", [{
            "area": "Demand",
            "priority": "Review",
            "finding": "Demand needs review.",
            "recommended_action": "Review stock levels.",
            "evidence": "Test fixture",
        }])

    def test_revenue_decline_generates_high_alert(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / "inputs"
            outputs = root / "outputs"
            inputs.mkdir()
            self.create_inputs(inputs)

            generate_insights(input_dir=inputs, output_dir=outputs)

            with (outputs / "ai_risk_alerts.csv").open(
                encoding="utf-8", newline=""
            ) as file:
                alerts = list(csv.DictReader(file))

            revenue_alerts = [
                row for row in alerts
                if row["category"] == "KPI movement"
            ]
            self.assertEqual(len(revenue_alerts), 1)
            self.assertEqual(revenue_alerts[0]["severity"], "High")
            self.assertIn("declined by 12.00%", revenue_alerts[0]["message"])

    def test_changed_revenue_removes_decline_alert(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / "inputs"
            outputs = root / "outputs"
            inputs.mkdir()
            self.create_inputs(inputs, revenue_change="2")

            generate_insights(input_dir=inputs, output_dir=outputs)

            with (outputs / "ai_risk_alerts.csv").open(
                encoding="utf-8", newline=""
            ) as file:
                alerts = list(csv.DictReader(file))

            revenue_alerts = [
                row for row in alerts
                if row["category"] == "KPI movement"
            ]
            self.assertEqual(revenue_alerts, [])

    def test_forecast_selection_uses_lowest_mape(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / "inputs"
            outputs = root / "outputs"
            inputs.mkdir()
            self.create_inputs(inputs)

            generate_insights(input_dir=inputs, output_dir=outputs)

            summary = (outputs / "ai_executive_summary.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("Model A", summary)
            self.assertIn("8.00% MAPE", summary)

    def test_forecast_selection_ignores_invalid_mape_values(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / "inputs"
            outputs = root / "outputs"
            inputs.mkdir()
            self.create_inputs(inputs)

            self.write_csv(
                inputs,
                "forecast_model_comparison.csv",
                [
                    {"model": "Invalid text model", "MAPE": "invalid"},
                    {"model": "NaN model", "MAPE": "NaN"},
                    {"model": "Infinite model", "MAPE": "inf"},
                    {"model": "Model B", "MAPE": "12.0"},
                    {"model": "Best valid model", "MAPE": "4.5"},
                ],
            )

            generate_insights(input_dir=inputs, output_dir=outputs)

            summary = (
                outputs / "ai_executive_summary.md"
            ).read_text(encoding="utf-8")

            self.assertIn("Best valid model", summary)
            self.assertIn("4.50% MAPE", summary)
            self.assertNotIn("Invalid text model", summary)
            self.assertNotIn("NaN model", summary)
            self.assertNotIn("Infinite model", summary)


    def test_missing_input_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / "inputs"
            outputs = root / "outputs"
            inputs.mkdir()

            with self.assertRaises(FileNotFoundError):
                generate_insights(input_dir=inputs, output_dir=outputs)

    def test_number_converts_valid_numeric_values(self):
        self.assertEqual(number("42"), 42.0)
        self.assertEqual(number("-12.5"), -12.5)
        self.assertEqual(number("0"), 0.0)

    def test_number_returns_default_for_invalid_values(self):
        invalid_values = [
            "invalid",
            "",
            None,
            "NaN",
            "inf",
            "-inf",
        ]

        for value in invalid_values:
            with self.subTest(value=value):
                self.assertIsNone(number(value))

        self.assertEqual(number("invalid", default=99), 99)


    def test_kpi_finding_contains_correct_values(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / "inputs"
            outputs = root / "outputs"
            inputs.mkdir()
            self.create_inputs(inputs, revenue_change="-12")

            generate_insights(input_dir=inputs, output_dir=outputs)

            summary = (
                outputs / "ai_executive_summary.md"
            ).read_text(encoding="utf-8")

            self.assertIn(
                "**Revenue:** current value 88.00; "
                "change -12.00% versus the previous month.",
                summary,
            )
            self.assertIn(
                "Combined downside scenario:** profit changes by "
                "-300.00 compared with baseline.",
                summary,
            )

    def test_invalid_kpi_values_are_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / "inputs"
            outputs = root / "outputs"
            inputs.mkdir()
            self.create_inputs(inputs)

            self.write_csv(
                inputs,
                "business_kpi_summary.csv",
                [
                    {
                        "Metric": "Invalid text",
                        "Current_Month": "2025-12",
                        "Current_Value": "not-a-number",
                        "Change_Pct": "-20",
                    },
                    {
                        "Metric": "Not finite",
                        "Current_Month": "2025-12",
                        "Current_Value": "100",
                        "Change_Pct": "NaN",
                    },
                    {
                        "Metric": "Valid decline",
                        "Current_Month": "2025-12",
                        "Current_Value": "80",
                        "Change_Pct": "-10",
                    },
                ],
            )

            generate_insights(input_dir=inputs, output_dir=outputs)

            summary = (
                outputs / "ai_executive_summary.md"
            ).read_text(encoding="utf-8")

            with (
                outputs / "ai_risk_alerts.csv"
            ).open(encoding="utf-8", newline="") as file:
                alerts = list(csv.DictReader(file))

            self.assertNotIn("Invalid text", summary)
            self.assertNotIn("Not finite", summary)
            self.assertIn("Valid decline", summary)

            kpi_alerts = [
                row for row in alerts
                if row["category"] == "KPI movement"
            ]
            self.assertEqual(len(kpi_alerts), 1)
            self.assertIn(
                "declined by 10.00%",
                kpi_alerts[0]["message"],
            )
    def test_empty_inputs_generate_all_three_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / "inputs"
            outputs = root / "outputs"
            inputs.mkdir()

            headers = {
                "business_kpi_summary.csv": [
                    "Metric", "Current_Month", "Previous_Month",
                    "Current_Value", "Previous_Value", "Change_Pct",
                ],
                "daily_sales_anomalies.csv": [
                    "date", "daily_revenue", "robust_z_score",
                    "anomaly_type",
                ],
                "forecast_model_comparison.csv": ["model", "MAPE"],
                "customer_rfm_summary.csv": [
                    "Customer_Segment", "Revenue_Contribution_Percentage",
                ],
                "sales_scenario_results.csv": ["Scenario", "Total_Profit"],
                "demand_planning_recommendations.csv": [
                    "area", "priority", "finding",
                    "recommended_action", "evidence",
                ],
            }

            for filename, fields in headers.items():
                with (inputs / filename).open(
                    "w", encoding="utf-8", newline=""
                ) as file:
                    writer = csv.writer(file)
                    writer.writerow(fields)

            generate_insights(input_dir=inputs, output_dir=outputs)

            summary_path = outputs / "ai_executive_summary.md"
            alerts_path = outputs / "ai_risk_alerts.csv"
            recommendations_path = (
                outputs / "ai_business_recommendations.csv"
            )

            self.assertTrue(summary_path.is_file())
            self.assertTrue(alerts_path.is_file())
            self.assertTrue(recommendations_path.is_file())

            summary = summary_path.read_text(encoding="utf-8")
            self.assertIn(
                "No usable findings were available.",
                summary,
            )
            self.assertIn("Total alerts generated: **0**", summary)
            self.assertIn("Recommendations generated: **0**", summary)

            with alerts_path.open(
                encoding="utf-8", newline=""
            ) as file:
                alerts = list(csv.DictReader(file))

            with recommendations_path.open(
                encoding="utf-8", newline=""
            ) as file:
                recommendations = list(csv.DictReader(file))

            self.assertEqual(alerts, [])
            self.assertEqual(recommendations, [])


    def test_recommendations_match_source_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / "inputs"
            outputs = root / "outputs"
            inputs.mkdir()
            self.create_inputs(inputs, revenue_change="-12")

            generate_insights(input_dir=inputs, output_dir=outputs)

            with (
                outputs / "ai_business_recommendations.csv"
            ).open(encoding="utf-8", newline="") as file:
                recommendations = list(csv.DictReader(file))

            kpi = next(
                row for row in recommendations
                if row["category"] == "KPI movement"
            )
            self.assertIn("Current value=88.00", kpi["evidence"])
            self.assertIn("change=-12.00%", kpi["evidence"])
            self.assertIn("declined by 12.00%", kpi["finding"])

            forecast = next(
                row for row in recommendations
                if row["category"] == "Forecasting"
            )
            self.assertIn("MAPE=8.00%", forecast["evidence"])
            self.assertIn("Model A", forecast["finding"])

            customer = next(
                row for row in recommendations
                if row["category"] == "Customer concentration"
            )
            self.assertIn("contribution=40.00%", customer["evidence"])
            self.assertIn("Champions", customer["finding"])

            scenario = next(
                row for row in recommendations
                if row["category"] == "Scenario risk"
            )
            self.assertIn("Baseline profit=1000.00", scenario["evidence"])
            self.assertIn("downside profit=700.00", scenario["evidence"])
            self.assertIn("-300.00", scenario["finding"])


    def test_populated_outputs_have_expected_headers_and_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / "inputs"
            outputs = root / "outputs"
            inputs.mkdir()
            self.create_inputs(inputs)

            generate_insights(input_dir=inputs, output_dir=outputs)

            with (
                outputs / "ai_risk_alerts.csv"
            ).open(encoding="utf-8", newline="") as file:
                alert_reader = csv.DictReader(file)
                alerts = list(alert_reader)
                self.assertEqual(
                    alert_reader.fieldnames,
                    ["severity", "category", "date", "message", "metric_value"],
                )

            with (
                outputs / "ai_business_recommendations.csv"
            ).open(encoding="utf-8", newline="") as file:
                recommendation_reader = csv.DictReader(file)
                recommendations = list(recommendation_reader)
                self.assertEqual(
                    recommendation_reader.fieldnames,
                    [
                        "priority", "category", "finding",
                        "recommended_action", "evidence",
                    ],
                )

            summary = (
                outputs / "ai_executive_summary.md"
            ).read_text(encoding="utf-8")

            self.assertIn(
                f"Total alerts generated: **{len(alerts)}**",
                summary,
            )
            self.assertIn(
                f"Recommendations generated: **{len(recommendations)}**",
                summary,
            )
            self.assertTrue(alerts)
            self.assertTrue(recommendations)


    def test_anomaly_and_demand_recommendations_preserve_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            inputs = root / "inputs"
            outputs = root / "outputs"
            inputs.mkdir()
            self.create_inputs(inputs)

            generate_insights(input_dir=inputs, output_dir=outputs)

            with (
                outputs / "ai_business_recommendations.csv"
            ).open(encoding="utf-8", newline="") as file:
                recommendations = list(csv.DictReader(file))

            findings = [
                row["finding"] for row in recommendations
            ]
            evidence = [
                row["evidence"] for row in recommendations
            ]

            self.assertTrue(
                any("anomal" in finding.lower() for finding in findings),
                "Expected an anomaly-related recommendation.",
            )
            self.assertTrue(
                any("Test fixture" in item for item in evidence),
                "Expected source demand-planning evidence to be preserved.",
            )

if __name__ == "__main__":
    unittest.main()
