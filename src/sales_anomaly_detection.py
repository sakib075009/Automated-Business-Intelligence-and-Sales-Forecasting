
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FACT_SALES_FILE = (
    PROJECT_ROOT / "data" / "raw" / "fact_sales.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"

ANOMALY_OUTPUT_FILE = (
    OUTPUT_DIR / "daily_sales_anomalies.csv"
)

WINDOW_DAYS = 28
MINIMUM_HISTORY_DAYS = 14
MAD_THRESHOLD = 3.5


# ============================================================
# LOAD AND PREPARE DAILY REVENUE
# ============================================================

def load_daily_revenue():
    """Aggregate sales into a continuous daily revenue series."""

    df = pd.read_csv(
        FACT_SALES_FILE,
        usecols=["order_date", "revenue"],
    )

    df["order_date"] = pd.to_datetime(
        df["order_date"],
        errors="raise",
    )

    df["revenue"] = pd.to_numeric(
        df["revenue"],
        errors="raise",
    )

    if df["order_date"].isna().any():
        raise ValueError("Missing or invalid sales dates found.")

    if not np.isfinite(df["revenue"].to_numpy()).all():
        raise ValueError("Revenue contains non-finite values.")

    daily = (
        df.groupby("order_date")["revenue"]
        .sum()
        .sort_index()
    )

    if daily.empty:
        raise ValueError("No sales data found.")

    full_dates = pd.date_range(
        start=daily.index.min(),
        end=daily.index.max(),
        freq="D",
    )

    # A missing calendar date represents zero recorded revenue.
    daily = daily.reindex(
        full_dates,
        fill_value=0.0,
    )

    daily.index.name = "date"

    return daily.astype(float)


# ============================================================
# DETECT ANOMALIES
# ============================================================

def detect_anomalies(daily):
    """
    Compare each day with the preceding 28 calendar days.

    The current day's revenue is excluded from its baseline.
    The robust modified Z-score uses the median and MAD.
    """

    result = pd.DataFrame({
        "date": daily.index,
        "daily_revenue": daily.to_numpy(),
    })

    history = result["daily_revenue"].shift(1)

    rolling_median = history.rolling(
        window=WINDOW_DAYS,
        min_periods=MINIMUM_HISTORY_DAYS,
    ).median()

    rolling_mad = history.rolling(
        window=WINDOW_DAYS,
        min_periods=MINIMUM_HISTORY_DAYS,
    ).apply(
        lambda values: np.median(
            np.abs(values - np.median(values))
        ),
        raw=True,
    )

    result["baseline_median"] = rolling_median
    result["baseline_mad"] = rolling_mad

    result["revenue_difference"] = (
        result["daily_revenue"]
        - result["baseline_median"]
    )

    # MAD is converted to a robust standard-deviation estimate.
    # If MAD is zero, a modified Z-score cannot be calculated.
    valid_mad = result["baseline_mad"] > 0

    result["robust_z_score"] = np.nan

    result.loc[valid_mad, "robust_z_score"] = (
        0.67448975
        * result.loc[valid_mad, "revenue_difference"]
        / result.loc[valid_mad, "baseline_mad"]
    )

    result["anomaly_type"] = "Normal"

    result.loc[
        result["robust_z_score"] >= MAD_THRESHOLD,
        "anomaly_type",
    ] = "High Revenue"

    result.loc[
        result["robust_z_score"] <= -MAD_THRESHOLD,
        "anomaly_type",
    ] = "Low Revenue"

    result["baseline_status"] = "Ready"

    result.loc[
        result["baseline_median"].isna(),
        "baseline_status",
    ] = "Insufficient history"

    result.loc[
        result["baseline_median"].notna()
        & result["baseline_mad"].eq(0),
        "baseline_status",
    ] = "Zero MAD; score unavailable"

    # Do not label observations as anomalies when the robust
    # score cannot be calculated reliably.
    result.loc[
        result["robust_z_score"].isna(),
        "anomaly_type",
    ] = "Not Scored"

    result["absolute_revenue_difference"] = (
        result["revenue_difference"].abs()
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("DAILY SALES ANOMALY DETECTION")
    print("=" * 60)

    daily = load_daily_revenue()

    print(f"Daily observations: {len(daily):,}")
    print(f"First date: {daily.index.min():%Y-%m-%d}")
    print(f"Last date: {daily.index.max():%Y-%m-%d}")

    result = detect_anomalies(daily)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        ANOMALY_OUTPUT_FILE,
        index=False,
    )

    anomalies = result[
        result["anomaly_type"].isin(
            ["High Revenue", "Low Revenue"]
        )
    ].copy()

    print("\n=== ANOMALY SUMMARY ===")
    print(
        result["anomaly_type"]
        .value_counts()
        .to_string()
    )

    print("\n=== LARGEST REVENUE ANOMALIES ===")

    if anomalies.empty:
        print("No scored anomalies were detected.")
    else:
        anomalies = anomalies.reindex(
            anomalies["robust_z_score"]
            .abs()
            .sort_values(ascending=False)
            .index
        )

        print(
            anomalies[
                [
                    "date",
                    "daily_revenue",
                    "baseline_median",
                    "revenue_difference",
                    "robust_z_score",
                    "anomaly_type",
                ]
            ]
            .head(15)
            .to_string(
                index=False,
                float_format=lambda value: f"{value:,.2f}",
            )
        )

    print(f"\nSaved: {ANOMALY_OUTPUT_FILE}")
    print("\nAnomaly detection completed successfully.")


if __name__ == "__main__":
    main()
