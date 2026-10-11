
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# 1. PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"

SALES_FILE = RAW_DIR / "fact_sales.csv"

FORECAST_COMPARISON_FILE = (
    OUTPUT_DIR / "forecast_model_comparison.csv"
)
FORECAST_PREDICTIONS_FILE = (
    OUTPUT_DIR / "forecast_model_predictions.csv"
)
ANOMALIES_FILE = OUTPUT_DIR / "daily_sales_anomalies.csv"
RFM_FILE = OUTPUT_DIR / "customer_rfm_segments.csv"
RFM_SUMMARY_FILE = OUTPUT_DIR / "customer_rfm_summary.csv"
SCENARIO_FILE = OUTPUT_DIR / "sales_scenario_results.csv"
MONTHLY_DETAILS_FILE = (
    OUTPUT_DIR / "sales_scenario_monthly_details.csv"
)
BUSINESS_KPI_FILE = OUTPUT_DIR / "business_kpi_summary.csv"
BUSINESS_INSIGHTS_FILE = OUTPUT_DIR / "business_insights.csv"

# ============================================================
# 2. VALIDATION HELPERS
# ============================================================

passed = 0
failed = 0


def check(condition, description):
    """Print a validation result and update the totals."""
    global passed, failed

    if condition:
        passed += 1
        print(f"PASS | {description}")
    else:
        failed += 1
        print(f"FAIL | {description}")


def check_columns(df, required_columns, description):
    """Check whether a DataFrame contains required columns."""
    missing = set(required_columns) - set(df.columns)

    check(
        not missing,
        (
            f"{description}: required columns present"
            if not missing
            else f"{description}: missing columns {sorted(missing)}"
        ),
    )


def read_output(path, description):
    """Read an existing output CSV or record a validation failure."""
    if not path.is_file():
        check(False, f"{description}: file exists")
        return None

    check(True, f"{description}: file exists")

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        check(False, f"{description}: CSV readable ({exc})")
        return None

    check(not df.empty, f"{description}: file is not empty")
    return df


# ============================================================
# 3. CHECK REQUIRED OUTPUT FILES AND COLUMNS
# ============================================================

def main():
    global passed, failed

    print("=" * 72)
    print("ANALYTICS OUTPUT VALIDATION")
    print("=" * 72)

    forecast_comparison = read_output(
        FORECAST_COMPARISON_FILE,
        "Forecast comparison",
    )
    forecast_predictions = read_output(
        FORECAST_PREDICTIONS_FILE,
        "Forecast predictions",
    )
    anomalies = read_output(
        ANOMALIES_FILE,
        "Daily anomaly output",
    )
    rfm = read_output(
        RFM_FILE,
        "Customer RFM output",
    )
    rfm_summary = read_output(
        RFM_SUMMARY_FILE,
        "RFM summary",
    )
    scenarios = read_output(
        SCENARIO_FILE,
        "Scenario results",
    )
    monthly_details = read_output(
        MONTHLY_DETAILS_FILE,
        "Monthly scenario details",
    )

    # --------------------------------------------------------
    # Forecast output structure and metrics
    # --------------------------------------------------------

    if forecast_comparison is not None:
        check_columns(
            forecast_comparison,
            ["model", "MAE", "RMSE", "MAPE"],
            "Forecast comparison",
        )

        metric_columns = ["MAE", "RMSE", "MAPE"]

        if set(metric_columns).issubset(forecast_comparison.columns):
            metrics = forecast_comparison[metric_columns].apply(
                pd.to_numeric,
                errors="coerce",
            )

            check(
                np.isfinite(metrics.to_numpy()).all()
                and (metrics >= 0).all().all(),
                "Forecast error metrics are finite and non-negative",
            )

    if forecast_predictions is not None:
        check_columns(
        forecast_predictions,
        ["month", "model", "actual_revenue", "forecast_revenue"],
        "Forecast predictions",
        )

        if "forecast_revenue" in forecast_predictions.columns:
            predictions = pd.to_numeric(
            forecast_predictions["forecast_revenue"],
            errors="coerce",
        )

        check(
            predictions.notna().all()
            and np.isfinite(predictions.to_numpy()).all(),
            "Forecast predictions contain finite numeric values",
        )

    # --------------------------------------------------------
    # Anomaly output
    # --------------------------------------------------------

    if anomalies is not None:
        check_columns(
            anomalies,
            ["date", "daily_revenue", "anomaly_type"],
            "Daily anomaly output",
        )

        if "date" in anomalies.columns:
            dates = pd.to_datetime(anomalies["date"], errors="coerce")

            check(
                dates.notna().all(),
                "Anomaly dates are valid",
            )

            if dates.notna().all():
                check(
                    dates.is_unique,
                    "Anomaly output has one row per date",
                )

                source_dates = pd.to_datetime(
                    pd.read_csv(
                        SALES_FILE,
                        usecols=["order_date"],
                    )["order_date"],
                    errors="coerce",
                ).dropna().dt.normalize().drop_duplicates()

                anomaly_dates = dates.dt.normalize().drop_duplicates()

                check(
                    dates.notna().all()
                    and source_dates.min() == anomaly_dates.min()
                    and source_dates.max() == anomaly_dates.max()
                    and set(source_dates) == set(anomaly_dates),
                    "Anomaly output covers every date in the source sales data",
                )

        if "daily_revenue" in anomalies.columns:
            daily_revenue = pd.to_numeric(
                anomalies["daily_revenue"],
                errors="coerce",
            )

            check(
                daily_revenue.notna().all()
                and np.isfinite(daily_revenue.to_numpy()).all(),
                "Daily anomaly revenue values are finite",
            )

    # --------------------------------------------------------
    # Customer RFM output and segment reconciliation
    # --------------------------------------------------------

    if rfm is not None:
        check_columns(
            rfm,
            [
                "customer_id",
                "Recency",
                "Frequency",
                "Monetary",
                "R_Score",
                "F_Score",
                "M_Score",
                "Customer_Segment",
            ],
            "Customer RFM output",
        )

        if "customer_id" in rfm.columns:
            check(
                rfm["customer_id"].notna().all()
                and rfm["customer_id"].is_unique,
                "RFM output has unique, non-missing customer IDs",
            )

            check(
                len(rfm) == 1500,
                "RFM output contains the expected 1,500 customers",
            )

        score_columns = ["R_Score", "F_Score", "M_Score"]

        if set(score_columns).issubset(rfm.columns):
            scores = rfm[score_columns].apply(
                pd.to_numeric,
                errors="coerce",
            )

            check(
                scores.notna().all().all()
                and scores.apply(
                    lambda col: col.between(1, 5).all()
                ).all(),
                "RFM scores are valid integers between 1 and 5",
            )

        if "Customer_Segment" in rfm.columns:
            check(
                rfm["Customer_Segment"].notna().all(),
                "Every customer has a segment",
            )

    if rfm_summary is not None:
        check_columns(
            rfm_summary,
            [
                "Customer_Segment",
                "Customer_Count",
                "Total_Revenue",
            ],
            "RFM summary",
        )

        if (
            rfm is not None
            and "Customer_Segment" in rfm.columns
            and {"Customer_Segment", "Customer_Count"}.issubset(
                rfm_summary.columns
            )
        ):
            detail_counts = (
                rfm.groupby("Customer_Segment")["customer_id"]
                .nunique()
                .sort_index()
            )

            summary_counts = (
                rfm_summary.set_index("Customer_Segment")[
                    "Customer_Count"
                ]
                .sort_index()
            )

            counts_match = (
                detail_counts.index.equals(summary_counts.index)
                and np.array_equal(
                    detail_counts.to_numpy(),
                    pd.to_numeric(
                        summary_counts,
                        errors="coerce",
                    ).to_numpy(),
                )
            )

            check(
                counts_match,
                "RFM summary customer counts reconcile with customer-level data",
            )

    # --------------------------------------------------------
    # Scenario output and historical baseline
    # --------------------------------------------------------

    if scenarios is not None:
        check_columns(
            scenarios,
            [
                "Scenario",
                "Total_Revenue",
                "Total_Cost",
                "Total_Profit",
                "Profit_Margin_Pct",
            ],
            "Scenario results",
        )

        if "Scenario" in scenarios.columns:
            expected_scenarios = {
                "Baseline",
                "Volume Growth +10%",
                "Discount Increase +2pp",
                "Unit Cost Increase +5%",
                "Combined Downside",
            }

            actual_scenarios = set(scenarios["Scenario"])

            check(
                expected_scenarios.issubset(actual_scenarios),
                "All five expected business scenarios are present",
            )

        financial_columns = [
            "Total_Revenue",
            "Total_Cost",
            "Total_Profit",
        ]

        if set(financial_columns).issubset(scenarios.columns):
            financial_values = scenarios[financial_columns].apply(
                pd.to_numeric,
                errors="coerce",
            )

            check(
                financial_values.notna().all().all()
                and np.isfinite(financial_values.to_numpy()).all(),
                "Scenario financial totals are finite numeric values",
            )

        if (
            SALES_FILE.is_file()
            and "Scenario" in scenarios.columns
            and set(financial_columns).issubset(scenarios.columns)
        ):
            source = pd.read_csv(
                SALES_FILE,
                usecols=["order_date", "revenue", "cost", "profit"],
                parse_dates=["order_date"],
            )

            source_2025 = source.loc[
                source["order_date"].between(
                    "2025-01-01",
                    "2025-12-31",
                )
            ]

            baseline_rows = scenarios.loc[
                scenarios["Scenario"] == "Baseline"
            ]

            if len(baseline_rows) == 1:
                baseline = baseline_rows.iloc[0]

                revenue_match = np.isclose(
                    float(baseline["Total_Revenue"]),
                    source_2025["revenue"].sum(),
                    atol=0.02,
                    rtol=0,
                )

                profit_match = np.isclose(
                    float(baseline["Total_Profit"]),
                    source_2025["profit"].sum(),
                    atol=0.02,
                    rtol=0,
                )

                check(
                    revenue_match,
                    "Scenario baseline revenue matches source data for 2025",
                )

                check(
                    profit_match,
                    "Scenario baseline profit matches source data for 2025",
                )
            else:
                check(
                    False,
                    "Exactly one baseline scenario exists",
                )

    # --------------------------------------------------------
    # Monthly historical details
    # --------------------------------------------------------

    if monthly_details is not None:
        check_columns(
            monthly_details,
            [
                "Month",
                "Historical_Quantity",
                "Historical_Revenue",
                "Historical_Cost",
                "Historical_Profit",
            ],
            "Monthly scenario details",
        )

        if "Month" in monthly_details.columns:
            check(
                monthly_details["Month"].nunique() == 12,
                "Monthly details contain 12 distinct months",
            )
    
    
    # --------------------------------------------------------
    # Business KPI summary and insights
    # --------------------------------------------------------

    business_kpis = read_output(
        BUSINESS_KPI_FILE,
        "Business KPI summary",
    )

    business_insights = read_output(
        BUSINESS_INSIGHTS_FILE,
        "Business insights",
    )

    if business_kpis is not None:
        check_columns(
            business_kpis,
            [
                "Metric",
                "Current_Month",
                "Previous_Month",
                "Current_Value",
                "Previous_Value",
                "Change_Pct",
            ],
            "Business KPI summary",
        )

        if "Metric" in business_kpis.columns:
            required_metrics = {
                "Revenue",
                "Profit",
                "Profit_Margin_Pct",
                "Average_Order_Value",
            }

            check(
                required_metrics.issubset(set(business_kpis["Metric"])),
                "Business KPI summary contains required metrics",
            )

            check(
                business_kpis["Metric"].is_unique,
                "Business KPI summary contains unique metric names",
            )

        numeric_columns = [
            "Current_Value",
            "Previous_Value",
            "Change_Pct",
        ]

        if set(numeric_columns).issubset(business_kpis.columns):
            numeric_values = business_kpis[numeric_columns].apply(
                pd.to_numeric,
                errors="coerce",
            )

            check(
                numeric_values[["Current_Value", "Previous_Value"]]
                .notna()
                .all()
                .all(),
                "Business KPI values are numeric",
            )

            check(
                np.isfinite(
                    numeric_values[
                        ["Current_Value", "Previous_Value"]
                    ].to_numpy(dtype=float)
                ).all(),
                "Business KPI values are finite",
            )

    if business_insights is not None:
        check_columns(
            business_insights,
            [
                "Current_Month",
                "Previous_Month",
                "Category",
                "Priority",
                "Insight",
            ],
            "Business insights",
        )

        check(
            not business_insights.empty,
            "Business insights contain at least one insight",
        )

        required_text_columns = [
            "Current_Month",
            "Previous_Month",
            "Category",
            "Priority",
            "Insight",
        ]

        if (
            not business_insights.empty
            and set(required_text_columns).issubset(
                business_insights.columns
            )
        ):
            check(
                business_insights[required_text_columns]
                .notna()
                .all()
                .all(),
                "Business insight fields are populated",
            )

            check(
                business_insights["Priority"].isin(
                    ["High", "Medium", "Low"]
                ).all(),
                "Business insight priorities are valid",
            )

            check(
                business_insights["Insight"]
                .astype(str)
                .str.strip()
                .ne("")
                .all(),
                "Business insight messages are not empty",
            )

    # --------------------------------------------------------
    # Final report
    # --------------------------------------------------------

    print("\n" + "=" * 72)
    print("VALIDATION SUMMARY")
    print("=" * 72)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total checks: {passed + failed}")

    if failed:
        print("\nSome checks failed. Review each FAIL message above.")
        raise SystemExit(1)

    print("\nAll analytics output validation checks passed.")


if __name__ == "__main__":
    main()
