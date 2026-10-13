
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PREDICTIONS_FILE = (
    PROJECT_ROOT
    / "data"
    / "outputs"
    / "forecast_model_predictions.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "dashboard" / "figures"

ACTUAL_FORECAST_CHART = (
    OUTPUT_DIR / "actual_vs_forecast_revenue.png"
)

FORECAST_ERROR_CHART = (
    OUTPUT_DIR / "forecast_error_by_month.png"
)

# Additional input files
MONTHLY_SUMMARY_FILE = (
    PROJECT_ROOT / "data" / "outputs" / "monthly_summary.csv"
)

REVENUE_FORECAST_FILE = (
    PROJECT_ROOT / "data" / "outputs" / "revenue_forecast.csv"
)

DEMAND_TREND_FILE = (
    PROJECT_ROOT / "data" / "outputs" / "demand_trend_seasonality.csv"
)

DEMAND_PERIOD_FILE = (
    PROJECT_ROOT / "data" / "outputs" / "demand_period_analysis.csv"
)

# Additional chart outputs
FUTURE_REVENUE_CHART = (
    OUTPUT_DIR / "future_revenue_forecast.png"
)

DEMAND_TREND_CHART = (
    OUTPUT_DIR / "demand_trend_and_periods.png"
)

# ============================================================
# LOAD AND VALIDATE DATA
# ============================================================

def load_predictions():
    """Load and validate historical forecast predictions."""

    if not PREDICTIONS_FILE.exists():
        raise FileNotFoundError(
            f"Prediction file not found: {PREDICTIONS_FILE}"
        )

    df = pd.read_csv(PREDICTIONS_FILE)

    required_columns = {
        "month",
        "model",
        "actual_revenue",
        "forecast_revenue",
        "error",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing columns: {sorted(missing_columns)}"
        )

    if df[list(required_columns)].isna().any().any():
        raise ValueError(
            "Prediction data contains missing values."
        )

    df["month"] = pd.to_datetime(
        df["month"],
        format="%Y-%m",
        errors="raise",
    )

    df = df.sort_values(["month", "model"]).copy()

    if df.duplicated(["month", "model"]).any():
        raise ValueError(
            "Duplicate month/model combinations found."
        )

    # All models must have the same actual values.
    actual_counts = (
        df.groupby("month")["actual_revenue"].nunique()
    )

    if (actual_counts != 1).any():
        raise ValueError(
            "Actual revenue differs between models for a month."
        )

    # Confirm the error convention used by the comparison script.
    expected_error = (
        df["forecast_revenue"] - df["actual_revenue"]
    )

    if not (
        (df["error"] - expected_error).abs() < 0.01
    ).all():
        raise ValueError(
            "The error column does not match "
            "forecast_revenue - actual_revenue."
        )

    return df


# ============================================================
# CHART 1: ACTUAL VS FORECAST
# ============================================================

def create_actual_vs_forecast_chart(df):
    """Plot actual revenue against each model's forecast."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    actual = (
        df[["month", "actual_revenue"]]
        .drop_duplicates("month")
        .sort_values("month")
    )

    fig, ax = plt.subplots(figsize=(13, 7))

    ax.plot(
        actual["month"],
        actual["actual_revenue"] / 1_000_000,
        label="Actual Revenue",
        color="black",
        linewidth=3,
        marker="o",
        markersize=5,
    )

    for model, model_df in df.groupby("model"):
        model_df = model_df.sort_values("month")

        ax.plot(
            model_df["month"],
            model_df["forecast_revenue"] / 1_000_000,
            label=model,
            linewidth=1.8,
            marker="o",
            markersize=3,
        )

    ax.set_title(
        "Actual vs Forecast Monthly Revenue (2025)",
        fontsize=15,
        pad=15,
    )
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (Millions)")
    ax.yaxis.set_major_formatter(
        mticker.StrMethodFormatter("{x:,.0f}")
    )

    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", frameon=True)

    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(
        ACTUAL_FORECAST_CHART,
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(fig)

    print(f"SAVED | {ACTUAL_FORECAST_CHART}")


# ============================================================
# CHART 2: MONTHLY FORECAST ERROR
# ============================================================

def create_forecast_error_chart(df):
    """
    Plot forecast errors.

    Positive error = overforecast.
    Negative error = underforecast.
    """

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    models = sorted(df["model"].unique())

    fig, axes = plt.subplots(
        nrows=len(models),
        ncols=1,
        figsize=(13, 10),
        sharex=True,
    )

    if len(models) == 1:
        axes = [axes]

    for ax, model in zip(axes, models):
        model_df = (
            df[df["model"] == model]
            .sort_values("month")
        )

        errors_millions = model_df["error"] / 1_000_000

        # Green = overforecast; red = underforecast.
        bar_colors = [
            "seagreen" if error > 0 else "indianred"
            for error in errors_millions
        ]

        ax.bar(
            model_df["month"],
            errors_millions,
            width=20,
            color=bar_colors,
            alpha=0.85,
        )

        ax.axhline(
            0,
            color="black",
            linewidth=1.2,
        )

        ax.set_title(model, loc="left", fontsize=11)
        ax.set_ylabel("Error (Millions)")
        ax.grid(axis="y", alpha=0.25)

        ax.text(
            0.99,
            0.95,
            "Above zero: overforecast\nBelow zero: underforecast",
            transform=ax.transAxes,
            ha="right",
            va="top",
            fontsize=8,
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": "white",
                "alpha": 0.8,
            },
        )

    axes[-1].set_xlabel("Month")

    axes[-1].set_xticks(
        pd.date_range("2025-01-01", "2025-12-01", freq="MS")
    )

    axes[-1].set_xticklabels(
        pd.date_range("2025-01-01", "2025-12-01", freq="MS")
        .strftime("%b")
    )

    fig.suptitle(
        "Monthly Forecast Error by Model (2025)",
        fontsize=15,
        y=1.01,
    )

    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(
        FORECAST_ERROR_CHART,
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(fig)

    print(f"SAVED | {FORECAST_ERROR_CHART}")


# ============================================================
# CHART 3: FUTURE REVENUE FORECAST
# ============================================================

def create_future_revenue_forecast_chart():
    """Plot historical monthly revenue and future revenue forecasts."""

    if not MONTHLY_SUMMARY_FILE.exists():
        raise FileNotFoundError(
            f"Monthly summary file not found: {MONTHLY_SUMMARY_FILE}"
        )

    if not REVENUE_FORECAST_FILE.exists():
        raise FileNotFoundError(
            f"Revenue forecast file not found: {REVENUE_FORECAST_FILE}"
        )

    actual_df = pd.read_csv(MONTHLY_SUMMARY_FILE)
    forecast_df = pd.read_csv(REVENUE_FORECAST_FILE)

    # Validate required columns.
    if not {"month", "revenue"}.issubset(actual_df.columns):
        raise ValueError(
            "monthly_summary.csv must contain month and revenue."
        )

    if not {"forecast_month", "forecast_revenue"}.issubset(
        forecast_df.columns
    ):
        raise ValueError(
            "revenue_forecast.csv must contain "
            "forecast_month and forecast_revenue."
        )

    # Parse dates and numeric values.
    actual_df["month"] = pd.to_datetime(
        actual_df["month"], format="%Y-%m", errors="raise"
    )
    forecast_df["forecast_month"] = pd.to_datetime(
        forecast_df["forecast_month"], errors="raise"
    )

    actual_df["revenue"] = pd.to_numeric(
        actual_df["revenue"], errors="raise"
    )
    forecast_df["forecast_revenue"] = pd.to_numeric(
        forecast_df["forecast_revenue"], errors="raise"
    )

    if actual_df[["month", "revenue"]].isna().any().any():
        raise ValueError("Historical revenue contains missing values.")

    if forecast_df[
        ["forecast_month", "forecast_revenue"]
    ].isna().any().any():
        raise ValueError("Forecast revenue contains missing values.")

    actual_df = actual_df.sort_values("month").copy()
    forecast_df = forecast_df.sort_values("forecast_month").copy()

    if actual_df["month"].duplicated().any():
        raise ValueError("Duplicate months found in monthly summary.")

    if forecast_df["forecast_month"].duplicated().any():
        raise ValueError("Duplicate months found in revenue forecast.")

    # Show only complete historical months before the forecast begins.
    forecast_start = forecast_df["forecast_month"].min()
    historical = actual_df[actual_df["month"] < forecast_start].copy()

    if historical.empty:
        raise ValueError("No historical months precede the forecast period.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    ax.plot(
        historical["month"],
        historical["revenue"] / 1_000_000,
        label="Historical Revenue",
        color="black",
        linewidth=2.2,
        marker="o",
        markersize=3.5,
    )

    ax.plot(
        forecast_df["forecast_month"],
        forecast_df["forecast_revenue"] / 1_000_000,
        label="Forecast Revenue",
        color="royalblue",
        linewidth=2.2,
        marker="o",
        markersize=5,
        linestyle="--",
    )

    # Mark the boundary between observed history and forecast.
    ax.axvline(
        forecast_start,
        color="gray",
        linestyle=":",
        linewidth=1.5,
        label="Forecast Starts",
    )

    ax.set_title(
        "Historical and Forecast Monthly Revenue",
        fontsize=15,
        pad=15,
    )
    ax.set_xlabel("Month")
    ax.set_ylabel("Revenue (Millions)")
    ax.yaxis.set_major_formatter(
        mticker.StrMethodFormatter("{x:,.0f}")
    )

    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")

    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(
        FUTURE_REVENUE_CHART,
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(fig)

    print(f"SAVED | {FUTURE_REVENUE_CHART}")
    print(f"Historical months plotted: {len(historical)}")
    print(f"Forecast months plotted: {len(forecast_df)}")


# ============================================================
# CHART 4: DEMAND TREND AND DEMAND PERIODS
# ============================================================

def create_demand_trend_chart():
    """Plot monthly quantity, moving average, and demand periods."""

    if not DEMAND_TREND_FILE.exists():
        raise FileNotFoundError(
            f"Demand trend file not found: {DEMAND_TREND_FILE}"
        )

    if not DEMAND_PERIOD_FILE.exists():
        raise FileNotFoundError(
            f"Demand period file not found: {DEMAND_PERIOD_FILE}"
        )

    trend_df = pd.read_csv(DEMAND_TREND_FILE)
    period_df = pd.read_csv(DEMAND_PERIOD_FILE)

    required_trend = {
        "month",
        "quantity",
        "moving_average_3m",
        "calendar_pattern",
    }
    required_period = {"month", "demand_period"}

    if not required_trend.issubset(trend_df.columns):
        raise ValueError(
            "Demand trend file is missing required columns: "
            f"{sorted(required_trend - set(trend_df.columns))}"
        )

    if not required_period.issubset(period_df.columns):
        raise ValueError(
            "Demand period file is missing required columns: "
            f"{sorted(required_period - set(period_df.columns))}"
        )

    trend_df["month"] = pd.to_datetime(
        trend_df["month"], errors="raise"
    )
    period_df["month"] = pd.to_datetime(
        period_df["month"], errors="raise"
    )

    for column in ["quantity", "moving_average_3m"]:
        trend_df[column] = pd.to_numeric(
            trend_df[column], errors="raise"
        )

    if trend_df["month"].duplicated().any():
        raise ValueError("Duplicate months found in demand trend data.")

    if period_df["month"].duplicated().any():
        raise ValueError("Duplicate months found in demand period data.")

    # Join demand classifications to the monthly trend.
    df = trend_df.merge(
        period_df[["month", "demand_period"]],
        on="month",
        how="left",
        validate="one_to_one",
    )

    if df["demand_period"].isna().any():
        raise ValueError(
            "Some months have no matching demand-period classification."
        )

    df = df.sort_values("month").copy()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    # Monthly quantity.
    ax.plot(
        df["month"],
        df["quantity"],
        label="Monthly Quantity",
        color="steelblue",
        linewidth=1.6,
        marker="o",
        markersize=4,
    )

    # Three-month moving average.
    ax.plot(
        df["month"],
        df["moving_average_3m"],
        label="3-Month Moving Average",
        color="darkorange",
        linewidth=2.5,
    )

    # Highlight high and low demand observations.
    low_mask = df["demand_period"].eq("Low")
    high_mask = df["demand_period"].eq("High")

    ax.scatter(
        df.loc[low_mask, "month"],
        df.loc[low_mask, "quantity"],
        label="Low Demand Period",
        color="indianred",
        marker="v",
        s=65,
        zorder=4,
    )

    ax.scatter(
        df.loc[high_mask, "month"],
        df.loc[high_mask, "quantity"],
        label="High Demand Period",
        color="seagreen",
        marker="^",
        s=65,
        zorder=4,
    )

    ax.set_title(
        "Monthly Demand Trend and Demand Periods",
        fontsize=15,
        pad=15,
    )
    ax.set_xlabel("Month")
    ax.set_ylabel("Quantity Sold")
    ax.yaxis.set_major_formatter(
        mticker.StrMethodFormatter("{x:,.0f}")
    )

    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", ncol=2)

    fig.text(
        0.5,
        0.015,
        "High/Low periods are relative to the historical median. "
        "Recurring seasonality is not established.",
        ha="center",
        fontsize=9,
    )

    fig.autofmt_xdate()
    fig.tight_layout(rect=[0, 0.045, 1, 1])

    fig.savefig(
        DEMAND_TREND_CHART,
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(fig)

    print(f"SAVED | {DEMAND_TREND_CHART}")
    print(f"Demand months plotted: {len(df)}")
    print(f"Low-demand months: {int(low_mask.sum())}")
    print(f"High-demand months: {int(high_mask.sum())}")


# ============================================================
# MAIN
# ============================================================


def main():
    print("=" * 60)
    print("FORECAST AND DEMAND VISUALIZATION")
    print("=" * 60)

    # Validate historical forecast comparison data.
    df = load_predictions()

    print(f"Prediction rows: {len(df)}")
    print(f"Months: {df['month'].nunique()}")
    print(f"Models: {df['model'].nunique()}")

    # Existing charts.
    create_actual_vs_forecast_chart(df)
    create_forecast_error_chart(df)

    # New charts.
    create_future_revenue_forecast_chart()
    create_demand_trend_chart()

    print("\nAll visualization generation completed.")


if __name__ == "__main__":
    main()
