
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SALES_FILE = PROJECT_ROOT / "data" / "raw" / "fact_sales.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"

SCENARIO_OUTPUT = OUTPUT_DIR / "sales_scenario_results.csv"
DETAIL_OUTPUT = OUTPUT_DIR / "sales_scenario_monthly_details.csv"

REQUIRED_COLUMNS = {
    "order_date",
    "quantity",
    "unit_price",
    "discount_pct",
    "revenue",
    "cost",
    "profit",
}

# Scenario assumptions
VOLUME_GROWTH = 0.10
VOLUME_DECLINE = -0.10
ADDITIONAL_DISCOUNT_PP = 2.0
UNIT_COST_INCREASE = 0.05


# ============================================================
# 2. LOAD AND VALIDATE DATA
# ============================================================

def load_sales_data():
    """Load historical sales and validate required fields."""

    sales = pd.read_csv(
        SALES_FILE,
        parse_dates=["order_date"],
    )

    missing = REQUIRED_COLUMNS - set(sales.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if sales.empty:
        raise ValueError("The sales dataset is empty.")

    if sales[list(REQUIRED_COLUMNS)].isnull().any().any():
        raise ValueError(
            "Missing values found in required columns."
        )

    if (sales["quantity"] <= 0).any():
        raise ValueError("Quantity must be positive.")

    if (sales["unit_price"] < 0).any():
        raise ValueError("Unit price cannot be negative.")

    if (sales["cost"] < 0).any():
        raise ValueError("Cost cannot be negative.")

    if not sales["discount_pct"].between(0, 100).all():
        raise ValueError("Discount must be between 0 and 100.")

    if sales["order_date"].isnull().any():
        raise ValueError("Invalid order dates found.")

    # Check the source's financial formulas within rounding tolerance.
    expected_revenue = (
        sales["quantity"]
        * sales["unit_price"]
        * (1 - sales["discount_pct"] / 100)
    )

    revenue_difference = (
        sales["revenue"] - expected_revenue
    ).abs()

    if (revenue_difference > 0.01).any():
        raise ValueError(
            "Revenue formula validation failed."
        )

    profit_difference = (
    sales["profit"] - (sales["revenue"] - sales["cost"])
    ).abs()

    if (profit_difference > 0.02).any():
        raise ValueError(
            "Profit formula validation failed: "
            f"maximum difference = {profit_difference.max():.6f}"
        )

    return sales


# ============================================================
# 3. SELECT THE LATEST 12 MONTHS
# ============================================================

def select_analysis_period(sales):
    """Select calendar-year 2025 for a stable, reproducible scenario comparison."""

    start_date = pd.Timestamp("2025-01-01")
    end_date = pd.Timestamp("2025-12-31")

    period_sales = sales.loc[
        sales["order_date"].between(start_date, end_date)
    ].copy()

    if period_sales.empty:
        raise ValueError("No sales found in the analysis period.")

    return period_sales, start_date, end_date


# ============================================================
# 4. CALCULATE A BUSINESS SCENARIO
# ============================================================


def calculate_scenario(
    sales,
    scenario_name,
    volume_change=0.0,
    additional_discount_pp=0.0,
    unit_cost_change=0.0,
):
    """Calculate a deterministic sales what-if scenario."""

    quantity_factor = 1 + volume_change
    cost_factor = 1 + unit_cost_change

    if quantity_factor < 0:
        raise ValueError(
            "Volume change cannot reduce quantity below zero."
        )

    # Keep recorded historical values exact for the baseline.
    is_baseline = (
        volume_change == 0
        and additional_discount_pp == 0
        and unit_cost_change == 0
    )

    if is_baseline:
        scenario_revenue = sales["revenue"].copy()
        scenario_cost = sales["cost"].copy()
        scenario_profit = sales["profit"].copy()
    else:
        scenario_discount = (
            sales["discount_pct"] + additional_discount_pp
        ).clip(lower=0, upper=100)

        scenario_revenue = (
            sales["quantity"]
            * quantity_factor
            * sales["unit_price"]
            * (1 - scenario_discount / 100)
        )

        scenario_cost = (
            sales["cost"]
            * quantity_factor
            * cost_factor
        )

        scenario_profit = scenario_revenue - scenario_cost

    # These calculations apply to every scenario, including baseline.
    total_quantity = sales["quantity"].sum() * quantity_factor
    total_revenue = scenario_revenue.sum()
    total_cost = scenario_cost.sum()
    total_profit = scenario_profit.sum()

    gross_sales = (
        sales["quantity"]
        * quantity_factor
        * sales["unit_price"]
    ).sum()

    effective_discount_pct = (
        (1 - total_revenue / gross_sales) * 100
        if gross_sales > 0
        else 0.0
    )

    profit_margin_pct = (
        total_profit / total_revenue * 100
        if total_revenue != 0
        else 0.0
    )

    return {
        "Scenario": scenario_name,
        "Volume_Change_Pct": volume_change * 100,
        "Additional_Discount_PP": additional_discount_pp,
        "Unit_Cost_Change_Pct": unit_cost_change * 100,
        "Total_Quantity": total_quantity,
        "Total_Revenue": total_revenue,
        "Total_Cost": total_cost,
        "Total_Profit": total_profit,
        "Profit_Margin_Pct": profit_margin_pct,
        "Effective_Discount_Pct": effective_discount_pct,
    }


# ============================================================
# 5. RUN THE SCENARIOS
# ============================================================

def main():
    print("=" * 70)
    print("SALES SCENARIO ANALYSIS")
    print("=" * 70)

    sales = load_sales_data()

    period_sales, start_date, end_date = select_analysis_period(
        sales
    )

    print(f"Source rows: {len(sales):,}")
    print(f"Analysis rows: {len(period_sales):,}")
    print(f"Analysis start: {start_date.date()}")
    print(f"Analysis end:   {end_date.date()}")

    # Baseline is the actual historical period.
    scenarios = [
        {
            "Scenario": "Baseline",
            "volume_change": 0.0,
            "additional_discount_pp": 0.0,
            "unit_cost_change": 0.0,
        },
        {
            "Scenario": "Volume Growth +10%",
            "volume_change": VOLUME_GROWTH,
            "additional_discount_pp": 0.0,
            "unit_cost_change": 0.0,
        },
        {
            "Scenario": "Discount Increase +2pp",
            "volume_change": 0.0,
            "additional_discount_pp": ADDITIONAL_DISCOUNT_PP,
            "unit_cost_change": 0.0,
        },
        {
            "Scenario": "Unit Cost Increase +5%",
            "volume_change": 0.0,
            "additional_discount_pp": 0.0,
            "unit_cost_change": UNIT_COST_INCREASE,
        },
        {
            "Scenario": "Combined Downside",
            "volume_change": VOLUME_DECLINE,
            "additional_discount_pp": ADDITIONAL_DISCOUNT_PP,
            "unit_cost_change": UNIT_COST_INCREASE,
        },
    ]

    results = []

    for config in scenarios:
        result = calculate_scenario(
            sales=period_sales,
            scenario_name=config["Scenario"],
            volume_change=config["volume_change"],
            additional_discount_pp=config[
                "additional_discount_pp"
            ],
            unit_cost_change=config["unit_cost_change"],
        )

        results.append(result)

    results_df = pd.DataFrame(results)

    # Compare each scenario with the historical baseline.
    baseline = results_df.loc[
        results_df["Scenario"] == "Baseline"
    ].iloc[0]

    results_df["Revenue_Change"] = (
        results_df["Total_Revenue"]
        - baseline["Total_Revenue"]
    )

    results_df["Revenue_Change_Pct"] = (
        results_df["Revenue_Change"]
        / baseline["Total_Revenue"]
        * 100
    )

    results_df["Profit_Change"] = (
        results_df["Total_Profit"]
        - baseline["Total_Profit"]
    )

    results_df["Profit_Change_Pct"] = (
        results_df["Profit_Change"]
        / abs(baseline["Total_Profit"])
        * 100
        if baseline["Total_Profit"] != 0
        else np.nan
    )

    # Monthly details for further analysis and visualization.
    monthly_details = (
        period_sales.assign(
            Month=period_sales["order_date"].dt.to_period("M").astype(str)
        )
        .groupby("Month")
        .agg(
            Historical_Quantity=("quantity", "sum"),
            Historical_Revenue=("revenue", "sum"),
            Historical_Cost=("cost", "sum"),
            Historical_Profit=("profit", "sum"),
        )
        .reset_index()
    )

    # Save outputs.
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(SCENARIO_OUTPUT, index=False)
    monthly_details.to_csv(DETAIL_OUTPUT, index=False)

    # Display useful results.
    display_columns = [
        "Scenario",
        "Total_Revenue",
        "Total_Cost",
        "Total_Profit",
        "Profit_Margin_Pct",
        "Revenue_Change_Pct",
        "Profit_Change",
    ]

    print("\nSCENARIO COMPARISON")
    print("-" * 70)

    print(
        results_df[display_columns]
        .round(2)
        .to_string(index=False)
    )

    print("\nOUTPUT FILES")
    print(f"Scenario results: {SCENARIO_OUTPUT}")
    print(f"Monthly details:  {DETAIL_OUTPUT}")

    # Verify the baseline agrees with the historical period.
    if not np.isclose(
        baseline["Total_Revenue"],
        period_sales["revenue"].sum(),
        atol=0.01,
        rtol=0,
    ):
        raise AssertionError(
            "Baseline revenue does not match historical revenue."
        )

    if not np.isclose(
        baseline["Total_Profit"],
        period_sales["profit"].sum(),
        atol=0.01,
        rtol=0,
    ):
        raise AssertionError(
            "Baseline profit does not match historical profit."
        )

    print("\nScenario analysis completed successfully.")
    print("The historical sales dataset was not modified.")


if __name__ == "__main__":
    main()
