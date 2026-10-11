
from pathlib import Path

import pandas as pd


# ============================================================
# 1. PROJECT PATHS AND SETTINGS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SALES_FILE = PROJECT_ROOT / "data" / "raw" / "fact_sales.csv"
CUSTOMER_OUTPUT = (
    PROJECT_ROOT / "data" / "outputs" / "customer_rfm_segments.csv"
)
SUMMARY_OUTPUT = (
    PROJECT_ROOT / "data" / "outputs" / "customer_rfm_summary.csv"
)

# Use the final date in the historical sales dataset as the
# analysis date, rather than today's real-world date.
MINIMUM_COLUMNS = {
    "order_id",
    "order_date",
    "customer_id",
    "revenue",
}


# ============================================================
# 2. HELPER FUNCTION: CREATE FIVE SCORES
# ============================================================

def create_quintile_scores(series, higher_is_better=True):
    """
    Assign scores from 1 to 5 using percentile ranks.

    Higher values receive 5 when higher_is_better=True.
    Lower values receive 5 when higher_is_better=False.

    Percentile ranks handle ties without requiring qcut to
    create exactly five distinct bins.
    """
    percentile = series.rank(method="average", pct=True)

    if higher_is_better:
        scores = (percentile * 5).apply(lambda value: min(5, int(value) + 1))
    else:
        scores = ((1 - percentile) * 5).apply(
            lambda value: min(5, max(1, int(value) + 1))
        )

    return scores.astype(int)


# ============================================================
# 3. CUSTOMER SEGMENTATION RULES
# ============================================================

def assign_segment(row):
    """
    Assign an interpretable segment using RFM scores.

    These are practical starter rules, not universal standards.
    """
    r = row["R_Score"]
    f = row["F_Score"]
    m = row["M_Score"]

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"

    if r >= 3 and f >= 4:
        return "Loyal Customers"

    if r >= 4 and f >= 2:
        return "Potential Loyalists"

    if r >= 4 and f == 1:
        return "Recent Customers"

    if r <= 2 and f >= 3 and m >= 3:
        return "At Risk"

    if r <= 2 and f >= 4:
        return "Cannot Lose Them"

    if r == 1 and f <= 2:
        return "Hibernating"

    if r <= 2 and f <= 2:
        return "Needs Attention"

    return "Regular Customers"


# ============================================================
# 4. MAIN RFM ANALYSIS
# ============================================================

def main():
    print("=" * 65)
    print("CUSTOMER RFM SEGMENTATION")
    print("=" * 65)

    # Read the sales dataset.
    sales = pd.read_csv(
        SALES_FILE,
        usecols=lambda column: column in MINIMUM_COLUMNS,
        parse_dates=["order_date"],
    )

    # Validate the required columns.
    missing_columns = MINIMUM_COLUMNS - set(sales.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    if sales.empty:
        raise ValueError("The sales dataset contains no rows.")

    if sales[list(MINIMUM_COLUMNS)].isnull().any().any():
        raise ValueError(
            "Required RFM fields contain missing values. "
            "Resolve these before segmentation."
        )

    if (sales["revenue"] < 0).any():
        raise ValueError(
            "Negative revenue detected. Review the data before segmentation."
        )

    if sales["order_date"].isnull().any():
        raise ValueError("Invalid order dates detected.")

    # Use the last transaction date as the analysis date.
    analysis_date = sales["order_date"].max().normalize()

    # --------------------------------------------------------
    # Calculate customer-level RFM metrics.
    # --------------------------------------------------------

    rfm = (
        sales.groupby("customer_id")
        .agg(
            Last_Purchase_Date=("order_date", "max"),
            Frequency=("order_id", "nunique"),
            Monetary=("revenue", "sum"),
        )
        .reset_index()
    )

    rfm["Recency"] = (
        analysis_date - rfm["Last_Purchase_Date"].dt.normalize()
    ).dt.days

    # --------------------------------------------------------
    # Calculate R, F and M scores.
    # --------------------------------------------------------

    # Lower recency is better: recently active customers
    # receive higher R scores.
    rfm["R_Score"] = create_quintile_scores(
        rfm["Recency"],
        higher_is_better=False,
    )

    # Higher order frequency and revenue are better.
    rfm["F_Score"] = create_quintile_scores(
        rfm["Frequency"],
        higher_is_better=True,
    )

    rfm["M_Score"] = create_quintile_scores(
        rfm["Monetary"],
        higher_is_better=True,
    )

    rfm["RFM_Score"] = (
        rfm["R_Score"].astype(str)
        + rfm["F_Score"].astype(str)
        + rfm["M_Score"].astype(str)
    )

    # Assign customer segments.
    rfm["Customer_Segment"] = rfm.apply(assign_segment, axis=1)

    # --------------------------------------------------------
    # Build the segment summary.
    # --------------------------------------------------------

    summary = (
        rfm.groupby("Customer_Segment")
        .agg(
            Customer_Count=("customer_id", "nunique"),
            Total_Revenue=("Monetary", "sum"),
            Average_Recency_Days=("Recency", "mean"),
            Average_Orders=("Frequency", "mean"),
            Average_Customer_Revenue=("Monetary", "mean"),
        )
        .reset_index()
    )

    summary["Customer_Percentage"] = (
        summary["Customer_Count"] / len(rfm) * 100
    )

    summary["Revenue_Contribution_Percentage"] = (
        summary["Total_Revenue"] / rfm["Monetary"].sum() * 100
    )

    summary = summary.sort_values(
        "Total_Revenue",
        ascending=False,
    )

    # --------------------------------------------------------
    # Save results.
    # --------------------------------------------------------

    CUSTOMER_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    rfm = rfm.sort_values(
        ["Customer_Segment", "Monetary"],
        ascending=[True, False],
    )

    rfm.to_csv(CUSTOMER_OUTPUT, index=False)
    summary.to_csv(SUMMARY_OUTPUT, index=False)

    # --------------------------------------------------------
    # Print a concise report.
    # --------------------------------------------------------

    print(f"Source rows: {len(sales):,}")
    print(f"Unique customers: {rfm['customer_id'].nunique():,}")
    print(f"Analysis date: {analysis_date.date()}")
    print(f"Total revenue: {rfm['Monetary'].sum():,.2f}")
    print("\nCUSTOMER SEGMENT SUMMARY")
    print("-" * 65)

    print(
        summary.round(2).to_string(index=False)
    )

    print("\nOUTPUT FILES")
    print(f"Customer-level results: {CUSTOMER_OUTPUT}")
    print(f"Segment summary:       {SUMMARY_OUTPUT}")

    # Basic output integrity checks.
    if rfm["customer_id"].duplicated().any():
        raise AssertionError(
            "RFM output contains duplicate customer IDs."
        )

    if rfm["R_Score"].between(1, 5).all() is False:
        raise AssertionError("Invalid R scores.")

    if rfm["F_Score"].between(1, 5).all() is False:
        raise AssertionError("Invalid F scores.")

    if rfm["M_Score"].between(1, 5).all() is False:
        raise AssertionError("Invalid M scores.")

    print("\nRFM analysis completed successfully.")


if __name__ == "__main__":
    main()
