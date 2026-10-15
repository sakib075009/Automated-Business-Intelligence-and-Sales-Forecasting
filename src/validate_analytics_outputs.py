
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
DEMAND_PERIODS_FILE = OUTPUT_DIR / "demand_period_analysis.csv"
PRODUCT_DEMAND_FILE = OUTPUT_DIR / "product_demand_priorities.csv"
REGIONAL_DEMAND_FILE = OUTPUT_DIR / "regional_demand_priorities.csv"
DEMAND_RECOMMENDATIONS_FILE = OUTPUT_DIR / "demand_planning_recommendations.csv"
AI_ALERTS_FILE = OUTPUT_DIR / "ai_risk_alerts.csv"
AI_RECOMMENDATIONS_FILE = OUTPUT_DIR / "ai_business_recommendations.csv"
AI_SUMMARY_FILE = OUTPUT_DIR / "ai_executive_summary.md"

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
    # Demand planning outputs
    # --------------------------------------------------------

    demand_periods = read_output(
        DEMAND_PERIODS_FILE,
        "Demand period analysis",
    )

    product_demand = read_output(
        PRODUCT_DEMAND_FILE,
        "Product demand priorities",
    )

    regional_demand = read_output(
        REGIONAL_DEMAND_FILE,
        "Regional demand priorities",
    )

    demand_recommendations = read_output(
        DEMAND_RECOMMENDATIONS_FILE,
        "Demand planning recommendations",
    )

    if demand_periods is not None:
        check_columns(
            demand_periods,
            ["month", "quantity", "demand_period"],
            "Demand period analysis",
        )

        if {"month", "quantity", "demand_period"}.issubset(
            demand_periods.columns
        ):
            months = pd.to_datetime(
                demand_periods["month"],
                errors="coerce",
            )
            quantities = pd.to_numeric(
                demand_periods["quantity"],
                errors="coerce",
            )

            check(
                months.notna().all(),
                "Demand periods contain valid dates",
            )

            check(
                months.is_unique,
                "Demand periods contain unique months",
            )

            check(
                quantities.notna().all()
                and np.isfinite(quantities.to_numpy()).all()
                and (quantities >= 0).all(),
                "Demand quantities are finite and non-negative",
            )

            check(
                demand_periods["demand_period"].isin(
                    ["High", "Low", "Typical"]
                ).all(),
                "Demand period classifications are valid",
            )

    if product_demand is not None:
        check_columns(
            product_demand,
            [
                "product_id",
                "quantity",
                "revenue",
                "profit",
                "quantity_rank",
                "demand_priority",
            ],
            "Product demand priorities",
        )

        required = {
            "product_id",
            "quantity",
            "revenue",
            "profit",
            "quantity_rank",
            "demand_priority",
        }

        if required.issubset(product_demand.columns):
            check(
                product_demand["product_id"].notna().all()
                and product_demand["product_id"].is_unique,
                "Product demand output has unique product IDs",
            )

            product_quantities = pd.to_numeric(
                product_demand["quantity"],
                errors="coerce",
            )

            product_ranks = pd.to_numeric(
                product_demand["quantity_rank"],
                errors="coerce",
            )

            check(
                product_quantities.notna().all()
                and np.isfinite(product_quantities.to_numpy()).all()
                and (product_quantities >= 0).all(),
                "Product quantities are finite and non-negative",
            )

            check(
                product_ranks.notna().all()
                and np.isfinite(product_ranks.to_numpy()).all()
                and (product_ranks >= 1).all()
                and (product_ranks <= len(product_demand)).all()
                and (product_ranks == product_ranks.astype(int)).all(),
                "Product quantity ranks are valid positive integers",
            )

            check(
                product_demand["demand_priority"].isin(
                    ["High", "Standard", "Low"]
                ).all(),
                "Product demand priorities are valid",
            )

    if regional_demand is not None:
        check_columns(
            regional_demand,
            [
                "region_id",
                "quantity",
                "revenue",
                "profit",
                "quantity_rank",
                "demand_priority",
            ],
            "Regional demand priorities",
        )

        required = {
            "region_id",
            "quantity",
            "revenue",
            "profit",
            "quantity_rank",
            "demand_priority",
        }

        if required.issubset(regional_demand.columns):
            check(
                regional_demand["region_id"].notna().all()
                and regional_demand["region_id"].is_unique,
                "Regional demand output has unique region IDs",
            )

            region_quantities = pd.to_numeric(
                regional_demand["quantity"],
                errors="coerce",
            )

            check(
                region_quantities.notna().all()
                and np.isfinite(region_quantities.to_numpy()).all()
                and (region_quantities >= 0).all(),
                "Regional quantities are finite and non-negative",
            )

            check(
                regional_demand["demand_priority"].isin(
                    ["High", "Low", "Typical"]
                ).all(),
                "Regional demand priorities are valid",
            )

    if demand_recommendations is not None:
        check_columns(
            demand_recommendations,
            [
                "area",
                "priority",
                "finding",
                "recommended_action",
                "evidence",
            ],
            "Demand planning recommendations",
        )

        required_text_columns = [
            "area",
            "priority",
            "finding",
            "recommended_action",
            "evidence",
        ]

        if set(required_text_columns).issubset(
            demand_recommendations.columns
        ):
            text_values = (
                demand_recommendations[required_text_columns]
                .astype("string")
                .apply(lambda column: column.str.strip())
            )

            check(
                text_values.notna().all().all()
                and text_values.ne("").all().all(),
                "Demand planning recommendation fields are populated",
            )

            check(
                demand_recommendations["priority"].isin(
                    ["Review", "Data needed"]
                ).all(),
                "Demand planning recommendation priorities are valid",
            )

    # --------------------------------------------------------
    # AI Analytics MVP validation
    # AI_ANALYTICS_MVP_VALIDATION
    # --------------------------------------------------------

    ai_alerts = None
    if AI_ALERTS_FILE.is_file():
        check(True, "AI risk alerts: file exists")
        try:
            ai_alerts = pd.read_csv(AI_ALERTS_FILE)
            check(True, "AI risk alerts: CSV readable")
            check(
                {"severity", "category", "date", "message", "metric_value"}
                .issubset(ai_alerts.columns),
                "AI risk alerts: required columns present",
            )
            if {"severity", "category", "message"}.issubset(ai_alerts.columns):
                check(
                    ai_alerts["severity"].isin(
                        ["High", "Medium", "Low"]
                    ).all(),
                    "AI risk alert severities are valid",
                )
                check(
                    ai_alerts[["category", "message"]]
                    .notna().all().all()
                    and ai_alerts[["category", "message"]]
                    .astype(str).apply(
                        lambda col: col.str.strip().ne("")
                    ).all().all(),
                    "AI risk alert descriptions are populated",
                )
        except Exception as exc:
            check(False, f"AI risk alerts: CSV validation failed ({exc})")
    else:
        check(False, "AI risk alerts: file exists")

    if AI_RECOMMENDATIONS_FILE.is_file():
        check(True, "AI recommendations: file exists")
        try:
            ai_recommendations = pd.read_csv(AI_RECOMMENDATIONS_FILE)
            check(True, "AI recommendations: CSV readable")
            check(
                not ai_recommendations.empty,
                "AI recommendations contain at least one recommendation",
            )
            required = [
                "priority", "category", "finding",
                "recommended_action", "evidence",
            ]
            check(
                set(required).issubset(ai_recommendations.columns),
                "AI recommendations: required columns present",
            )
            if set(required).issubset(ai_recommendations.columns):
                text_values = ai_recommendations[required].astype("string")
                check(
                    text_values.notna().all().all()
                    and text_values.apply(
                        lambda col: col.str.strip().ne("")
                    ).all().all(),
                    "AI recommendation fields are populated",
                )
        except Exception as exc:
            check(
                False,
                f"AI recommendations: CSV validation failed ({exc})",
            )
    else:
        check(False, "AI recommendations: file exists")

    check(
        AI_SUMMARY_FILE.is_file(),
        "AI executive summary: file exists",
    )
    if AI_SUMMARY_FILE.is_file():
        try:
            summary_text = AI_SUMMARY_FILE.read_text(encoding="utf-8")
            check(
                bool(summary_text.strip()),
                "AI executive summary: file is not empty",
            )
            check(
                "# AI-Assisted Business Analytics Summary" in summary_text,
                "AI executive summary contains the expected heading",
            )
        except Exception as exc:
            check(
                False,
                f"AI executive summary: file could not be read ({exc})",
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
