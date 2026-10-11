
from pathlib import Path
import pandas as pd


# ============================================================
# 1. PROJECT PATHS AND CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SALES_FILE = PROJECT_ROOT / "data" / "raw" / "fact_sales.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"

KPI_OUTPUT = OUTPUT_DIR / "business_kpi_summary.csv"
INSIGHTS_OUTPUT = OUTPUT_DIR / "business_insights.csv"

REQUIRED_COLUMNS = [
    "order_id",
    "order_date",
    "customer_id",
    "product_id",
    "region_id",
    "quantity",
    "revenue",
    "cost",
    "profit",
]

THRESHOLDS = {
    "revenue_change_pct": 10.0,
    "profit_change_pct": 10.0,
    "low_profit_margin_pct": 20.0,
    "aov_decline_pct": -10.0,
}


# ============================================================
# 2. LOAD AND VALIDATE SALES DATA
# ============================================================

def load_sales_data():
    """Load sales data and perform basic validation."""

    if not SALES_FILE.exists():
        raise FileNotFoundError(f"Sales data not found: {SALES_FILE}")

    sales = pd.read_csv(SALES_FILE, parse_dates=["order_date"])

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in sales.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if sales[REQUIRED_COLUMNS].isna().any().any():
        raise ValueError(
            "Missing values found in required sales columns."
        )

    if sales["order_date"].isna().any():
        raise ValueError("Invalid dates found in order_date.")

    if (sales["quantity"] <= 0).any():
        raise ValueError("Quantity must be greater than zero.")

    if (sales[["revenue", "cost"]] < 0).any().any():
        raise ValueError("Revenue and cost cannot be negative.")

    return sales


# ============================================================
# 3. SELECT THE TWO MOST RECENT COMPLETE MONTHS
# ============================================================

def select_comparison_periods(sales):
    """Return the latest and previous complete calendar months."""

    latest_date = sales["order_date"].max()

    latest_month = latest_date.to_period("M")
    month_end = latest_month.end_time.normalize()

    # If the dataset ends before month-end, exclude that
    # potentially incomplete month from the comparison.
    if latest_date.normalize() < month_end:
        current_month = latest_month - 1
    else:
        current_month = latest_month

    previous_month = current_month - 1

    return current_month, previous_month


# ============================================================
# 4. CALCULATE BUSINESS KPIs
# ============================================================

def calculate_kpis(sales):
    """Calculate the main business performance indicators."""

    revenue = sales["revenue"].sum()
    profit = sales["profit"].sum()
    orders = sales["order_id"].nunique()

    profit_margin = (
        profit / revenue * 100
        if revenue != 0
        else 0.0
    )

    average_order_value = (
        revenue / orders
        if orders != 0
        else 0.0
    )

    return {
        "Revenue": revenue,
        "Profit": profit,
        "Profit_Margin_Pct": profit_margin,
        "Orders": orders,
        "Average_Order_Value": average_order_value,
        "Quantity_Sold": sales["quantity"].sum(),
        "Unique_Customers": sales["customer_id"].nunique(),
        "Unique_Products": sales["product_id"].nunique(),
        "Unique_Regions": sales["region_id"].nunique(),
    }


# ============================================================
# 5. GENERATE BUSINESS INSIGHTS
# ============================================================

def generate_insights(current_kpis, previous_kpis):
    """Generate rule-based business insights from KPI comparisons."""

    insights = []

    # Revenue change
    previous_revenue = previous_kpis["Revenue"]
    current_revenue = current_kpis["Revenue"]

    revenue_change_pct = (
        (current_revenue - previous_revenue)
        / previous_revenue * 100
        if previous_revenue != 0
        else None
    )

    if revenue_change_pct is not None:
        if revenue_change_pct >= THRESHOLDS["revenue_change_pct"]:
            insights.append({
                "Category": "Revenue",
                "Priority": "High",
                "Insight": (
                    f"Revenue increased by {revenue_change_pct:.2f}% "
                    "compared with the previous month."
                ),
            })

        elif revenue_change_pct <= -THRESHOLDS["revenue_change_pct"]:
            insights.append({
                "Category": "Revenue",
                "Priority": "High",
                "Insight": (
                    f"Revenue declined by {abs(revenue_change_pct):.2f}% "
                    "compared with the previous month."
                ),
            })

    # Profit change
    previous_profit = previous_kpis["Profit"]
    current_profit = current_kpis["Profit"]

    profit_change_pct = (
        (current_profit - previous_profit)
        / previous_profit * 100
        if previous_profit != 0
        else None
    )

    if profit_change_pct is not None:
        if profit_change_pct >= THRESHOLDS["profit_change_pct"]:
            insights.append({
                "Category": "Profit",
                "Priority": "High",
                "Insight": (
                    f"Profit increased by {profit_change_pct:.2f}% "
                    "compared with the previous month."
                ),
            })

        elif profit_change_pct <= -THRESHOLDS["profit_change_pct"]:
            insights.append({
                "Category": "Profit",
                "Priority": "High",
                "Insight": (
                    f"Profit declined by {abs(profit_change_pct):.2f}% "
                    "compared with the previous month."
                ),
            })

    # Profit margin
    current_margin = current_kpis["Profit_Margin_Pct"]

    if current_margin < THRESHOLDS["low_profit_margin_pct"]:
        insights.append({
            "Category": "Profit Margin",
            "Priority": "High",
            "Insight": (
                f"Profit margin is {current_margin:.2f}%, below the "
                f"{THRESHOLDS['low_profit_margin_pct']:.2f}% threshold."
            ),
        })

    # Average order value (AOV)
    previous_aov = previous_kpis["Average_Order_Value"]
    current_aov = current_kpis["Average_Order_Value"]

    aov_change_pct = (
        (current_aov - previous_aov) / previous_aov * 100
        if previous_aov != 0
        else None
    )

    if (
        aov_change_pct is not None
        and aov_change_pct <= THRESHOLDS["aov_decline_pct"]
    ):
        insights.append({
            "Category": "Average Order Value",
            "Priority": "Medium",
            "Insight": (
                f"Average order value declined by "
                f"{abs(aov_change_pct):.2f}% compared with the previous month."
            ),
        })

    # No alerts triggered
    if not insights:
        insights.append({
            "Category": "General",
            "Priority": "Low",
            "Insight": (
                "No business alerts were triggered by the configured thresholds."
            ),
        })

    return insights


# ============================================================
# 6. MAIN ENTRY POINT
# ============================================================

def main():
    """Run KPI calculations and generate business insights."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load source data
    sales = load_sales_data()

    # Identify comparison periods
    current_month, previous_month = select_comparison_periods(sales)

    current_sales = sales[
        sales["order_date"].dt.to_period("M") == current_month
    ]

    previous_sales = sales[
        sales["order_date"].dt.to_period("M") == previous_month
    ]

    if current_sales.empty or previous_sales.empty:
        raise ValueError(
            "The current or previous comparison month has no sales records."
        )

    # Calculate KPIs
    current_kpis = calculate_kpis(current_sales)
    previous_kpis = calculate_kpis(previous_sales)

    # Build KPI summary
    kpi_rows = []

    for metric in current_kpis:
        current_value = current_kpis[metric]
        previous_value = previous_kpis[metric]

        change_pct = (
            (current_value - previous_value) / previous_value * 100
            if previous_value != 0
            else None
        )

        kpi_rows.append({
            "Metric": metric,
            "Current_Month": str(current_month),
            "Previous_Month": str(previous_month),
            "Current_Value": current_value,
            "Previous_Value": previous_value,
            "Change_Pct": change_pct,
        })

    kpi_df = pd.DataFrame(kpi_rows)
    kpi_df.to_csv(KPI_OUTPUT, index=False)

    # Generate insights AFTER the KPI dictionaries exist
    insights = generate_insights(current_kpis, previous_kpis)

    # Build and save insights output
    insights_df = pd.DataFrame(insights)

    insights_df.insert(0, "Current_Month", str(current_month))
    insights_df.insert(1, "Previous_Month", str(previous_month))

    insights_df.to_csv(INSIGHTS_OUTPUT, index=False)

    # Display results
    print("=" * 60)
    print("BUSINESS INSIGHTS ENGINE")
    print("=" * 60)

    print(f"Source rows: {len(sales):,}")
    print(f"Current month: {current_month}")
    print(f"Previous month: {previous_month}")

    print("\nCURRENT MONTH KPIs")

    for metric, value in current_kpis.items():
        print(f"{metric:25}: {value:,.2f}")

    print("\nBUSINESS INSIGHTS")

    for insight in insights:
        print(
            f"[{insight['Priority']}] "
            f"{insight['Category']}: {insight['Insight']}"
        )

    print(f"\nKPI summary saved to: {KPI_OUTPUT}")
    print(f"Business insights saved to: {INSIGHTS_OUTPUT}")
    print("\nBusiness insights engine completed successfully.")


if __name__ == "__main__":
    main()
