
"""Demand planning analysis for the Automated BI Sales Forecasting project.

Uses existing monthly, product, and regional summaries.
Does not modify source sales data or inventory records.
"""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"

MONTHLY_FILE = OUTPUT_DIR / "monthly_summary.csv"
PRODUCT_FILE = OUTPUT_DIR / "product_summary.csv"
REGIONAL_FILE = OUTPUT_DIR / "regional_summary.csv"

MONTHLY_OUTPUT = OUTPUT_DIR / "demand_period_analysis.csv"
PRODUCT_OUTPUT = OUTPUT_DIR / "product_demand_priorities.csv"
REGIONAL_OUTPUT = OUTPUT_DIR / "regional_demand_priorities.csv"
MANAGEMENT_OUTPUT = OUTPUT_DIR / "demand_planning_recommendations.csv"
TREND_SEASONALITY_OUTPUT = (OUTPUT_DIR / "demand_trend_seasonality.csv")


def load_summary(path: Path, required_columns: list[str]) -> pd.DataFrame:
    """Load a summary and validate its required columns."""

    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")

    df = pd.read_csv(path)

    missing = sorted(set(required_columns) - set(df.columns))
    if missing:
        raise ValueError(
            f"{path.name} is missing required columns: {missing}"
        )

    if df.empty:
        raise ValueError(f"{path.name} contains no data.")

    return df


def classify_demand_periods(monthly: pd.DataFrame) -> pd.DataFrame:
    """Classify months using quantity relative to the historical median."""

    df = monthly.copy()
    df["month"] = pd.to_datetime(df["month"], errors="raise")
    df = df.sort_values("month").reset_index(drop=True)

    if df["month"].duplicated().any():
        raise ValueError("Monthly summary contains duplicate months.")

    if df["quantity"].isna().any() or (df["quantity"] < 0).any():
        raise ValueError("Monthly quantity contains missing or negative values.")

    median_quantity = df["quantity"].median()

    df["median_monthly_quantity"] = median_quantity
    df["quantity_vs_median_pct"] = (
        (df["quantity"] - median_quantity)
        .div(median_quantity)
        .mul(100)
        if median_quantity != 0
        else 0.0
    )

    df["demand_period"] = "Typical"

    df.loc[df["quantity"] > median_quantity, "demand_period"] = "High"
    df.loc[df["quantity"] < median_quantity, "demand_period"] = "Low"

    return df[
        [
            "month",
            "quantity",
            "revenue",
            "orders",
            "customers",
            "median_monthly_quantity",
            "quantity_vs_median_pct",
            "demand_period",
        ]
    ]


def analyze_demand_trend_seasonality(
    monthly: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compare demand year over year and examine calendar-month patterns.

    Two years of history support exploratory comparisons, not proof
    of stable or statistically significant seasonality.
    """

    df = monthly.copy()
    df["month"] = pd.to_datetime(df["month"], errors="raise")
    df = df.sort_values("month").reset_index(drop=True)

    if df["month"].duplicated().any():
        raise ValueError("Monthly summary contains duplicate months.")

    if df["quantity"].isna().any() or (df["quantity"] < 0).any():
        raise ValueError("Monthly quantity contains missing or negative values.")

    # Ensure each observation represents the first day of a month.
    df["month"] = df["month"].dt.to_period("M").dt.to_timestamp()

    # Three-month moving average smooths short-term fluctuations.
    df["moving_average_3m"] = (
        df["quantity"].rolling(window=3, min_periods=3).mean()
    )

    df["year"] = df["month"].dt.year
    df["calendar_month"] = df["month"].dt.month
    df["calendar_month_name"] = df["month"].dt.strftime("%b")

    # Compare each month with the same calendar month one year earlier.
    df["quantity_previous_year"] = (
        df.groupby("calendar_month")["quantity"].shift(1)
    )

    df["year_over_year_change"] = (
        df["quantity"] - df["quantity_previous_year"]
    )

    df["year_over_year_change_pct"] = (
        df["year_over_year_change"]
        .div(df["quantity_previous_year"].where(
            df["quantity_previous_year"] != 0
        ))
        .mul(100)
    )

    # Compare the two-year average for each calendar month with
    # the overall monthly average across the available history.
    calendar_month_average = (
        df.groupby("calendar_month")["quantity"].mean()
    )

    overall_monthly_average = df["quantity"].mean()

    df["calendar_month_average"] = (
        df["calendar_month"].map(calendar_month_average)
    )

    df["calendar_month_vs_overall_avg_pct"] = (
        (
            df["calendar_month_average"]
            - overall_monthly_average
        )
        / overall_monthly_average
        * 100
        if overall_monthly_average != 0
        else 0.0
    )

    df["calendar_pattern"] = "Near overall average"

    df.loc[
        df["calendar_month_vs_overall_avg_pct"] > 5,
        "calendar_pattern",
    ] = "Relatively high"

    df.loc[
        df["calendar_month_vs_overall_avg_pct"] < -5,
        "calendar_pattern",
    ] = "Relatively low"

    df["analysis_caveat"] = (
        "Exploratory: only two observations per calendar month; "
        "recurring seasonality is not established."
    )

    return df[
        [
            "month",
            "quantity",
            "moving_average_3m",
            "quantity_previous_year",
            "year_over_year_change",
            "year_over_year_change_pct",
            "calendar_month_name",
            "calendar_month_average",
            "calendar_month_vs_overall_avg_pct",
            "calendar_pattern",
            "analysis_caveat",
        ]
    ]

def rank_products(products: pd.DataFrame) -> pd.DataFrame:
    """Rank products by quantity, revenue, and profit."""

    df = products.copy()

    for column in ["quantity", "revenue", "profit"]:
        if df[column].isna().any():
            raise ValueError(f"Product summary has missing values in {column}.")
        if (df[column] < 0).any():
            raise ValueError(f"Product summary has negative values in {column}.")

    df["quantity_rank"] = df["quantity"].rank(
        method="min", ascending=False
    ).astype(int)

    df["revenue_rank"] = df["revenue"].rank(
        method="min", ascending=False
    ).astype(int)

    df["profit_rank"] = df["profit"].rank(
        method="min", ascending=False
    ).astype(int)

    df["demand_priority"] = "Standard"
    df.loc[df["quantity_rank"] <= 15, "demand_priority"] = "High"
    df.loc[df["quantity_rank"] > len(df) - 15, "demand_priority"] = "Low"

    return df.sort_values(
        ["quantity_rank", "revenue_rank"]
    ).reset_index(drop=True)


def rank_regions(regions: pd.DataFrame) -> pd.DataFrame:
    """Rank regions by quantity, revenue, and profit."""

    df = regions.copy()

    for column in ["quantity", "revenue", "profit"]:
        if df[column].isna().any():
            raise ValueError(f"Regional summary has missing values in {column}.")
        if (df[column] < 0).any():
            raise ValueError(f"Regional summary has negative values in {column}.")

    df["quantity_rank"] = df["quantity"].rank(
        method="min", ascending=False
    ).astype(int)

    df["revenue_rank"] = df["revenue"].rank(
        method="min", ascending=False
    ).astype(int)

    df["profit_rank"] = df["profit"].rank(
        method="min", ascending=False
    ).astype(int)

    median_quantity = df["quantity"].median()
    df["demand_priority"] = "Typical"

    df.loc[df["quantity"] > median_quantity, "demand_priority"] = "High"
    df.loc[df["quantity"] < median_quantity, "demand_priority"] = "Low"

    return df.sort_values(
        ["quantity_rank", "revenue_rank"]
    ).reset_index(drop=True)


def create_recommendations(
    periods: pd.DataFrame,
    products: pd.DataFrame,
    regions: pd.DataFrame,
) -> pd.DataFrame:
    """Create evidence-based recommendations from summary statistics."""

    recommendations = []

    high_periods = periods.loc[periods["demand_period"] == "High"]
    low_periods = periods.loc[periods["demand_period"] == "Low"]

    if not high_periods.empty:
        months = ", ".join(
            high_periods["month"].dt.strftime("%Y-%m").tolist()
        )
        recommendations.append({
            "area": "Demand timing",
            "priority": "Review",
            "finding": f"Above-median quantity occurred in: {months}.",
            "recommended_action": (
                "Review these periods for staffing, purchasing, and "
                "capacity planning; validate the pattern with more history."
            ),
            "evidence": "Monthly quantity compared with the historical median",
        })

    if not low_periods.empty:
        months = ", ".join(
            low_periods["month"].dt.strftime("%Y-%m").tolist()
        )
        recommendations.append({
            "area": "Demand timing",
            "priority": "Review",
            "finding": f"Below-median quantity occurred in: {months}.",
            "recommended_action": (
                "Review these periods for lower workload and possible "
                "marketing or sales opportunities."
            ),
            "evidence": "Monthly quantity compared with the historical median",
        })

    high_products = products.nsmallest(10, "quantity_rank")

    recommendations.append({
        "area": "Product planning",
        "priority": "Review",
        "finding": (
            "Highest-quantity products: "
            + ", ".join(high_products["product_id"].astype(str).tolist())
            + "."
        ),
        "recommended_action": (
            "Review supplier capacity and replenishment plans for these "
            "products. Confirm actual stock and lead times before setting "
            "inventory targets."
        ),
        "evidence": "Top 10 products ranked by historical quantity",
    })

    high_regions = regions.nsmallest(3, "quantity_rank")

    recommendations.append({
        "area": "Regional planning",
        "priority": "Review",
        "finding": (
            "Highest-quantity regions: "
            + ", ".join(high_regions["region_id"].astype(str).tolist())
            + "."
        ),
        "recommended_action": (
            "Review regional fulfillment capacity and demand coverage."
        ),
        "evidence": "Top 3 regions ranked by historical quantity",
    })

    recommendations.append({
        "area": "Inventory data",
        "priority": "Data needed",
        "finding": (
            "The current summary files do not establish stock on hand, "
            "supplier lead time, or stockout history."
        ),
        "recommended_action": (
            "Add inventory and lead-time data before estimating reorder "
            "points, safety stock, or stockout risk."
        ),
        "evidence": "Available input schemas",
    })

    return pd.DataFrame(recommendations)


def main() -> None:
    """Run demand-planning analysis and save its output files."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    monthly = load_summary(
        MONTHLY_FILE,
        ["month", "quantity", "revenue", "orders", "customers"],
    )
    products = load_summary(
        PRODUCT_FILE,
        ["product_id", "quantity", "revenue", "profit"],
    )
    regions = load_summary(
        REGIONAL_FILE,
        ["region_id", "quantity", "revenue", "profit"],
    )

    periods = classify_demand_periods(monthly)
    trend_seasonality = analyze_demand_trend_seasonality(monthly)

    product_priorities = rank_products(products)
    regional_priorities = rank_regions(regions)

    recommendations = create_recommendations(
        periods, product_priorities, regional_priorities
    )

    periods.to_csv(MONTHLY_OUTPUT, index=False)
    trend_seasonality.to_csv(TREND_SEASONALITY_OUTPUT, index=False)

    product_priorities.to_csv(PRODUCT_OUTPUT, index=False)
    regional_priorities.to_csv(REGIONAL_OUTPUT, index=False)
    recommendations.to_csv(MANAGEMENT_OUTPUT, index=False)

    print("\n=== DEMAND PLANNING COMPLETED ===")
    print(f"Monthly periods: {len(periods)}")
    print(f"Products analyzed: {len(product_priorities)}")
    print(f"Regions analyzed: {len(regional_priorities)}")
    print(f"Recommendations: {len(recommendations)}")

    print("\n=== DEMAND PERIOD COUNTS ===")
    print(periods["demand_period"].value_counts().to_string())

    print("\n=== TOP 5 PRODUCTS BY QUANTITY ===")
    print(
        product_priorities[
            ["product_id", "quantity", "revenue", "profit", "demand_priority"]
        ].head(5).to_string(index=False)
    )

    print("\n=== REGIONAL PRIORITIES ===")
    print(
        regional_priorities[
            ["region_id", "quantity", "revenue", "profit", "demand_priority"]
        ].to_string(index=False)
    )

    print("\n=== OUTPUT FILES ===")
    for path in [
        MONTHLY_OUTPUT,
        TREND_SEASONALITY_OUTPUT,
        PRODUCT_OUTPUT,
        REGIONAL_OUTPUT,
        MANAGEMENT_OUTPUT,
    ]:
        print(f"SAVED | {path}")


if __name__ == "__main__":
    main()
