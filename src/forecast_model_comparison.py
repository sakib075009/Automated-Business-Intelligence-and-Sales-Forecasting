
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

FACT_SALES_FILE = (
    PROJECT_ROOT / "data" / "raw" / "fact_sales.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"

COMPARISON_FILE = (
    OUTPUT_DIR / "forecast_model_comparison.csv"
)

HOLDOUT_START = "2025-01-01"
HOLDOUT_END = "2025-06-01"


# ============================================================
# LOAD MONTHLY REVENUE
# ============================================================

def load_monthly_revenue():
    """Aggregate historical sales revenue by calendar month."""

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

    monthly = (
        df.set_index("order_date")["revenue"]
        .resample("MS")
        .sum()
        .asfreq("MS", fill_value=0)
    )

    if monthly.empty:
        raise ValueError("No monthly revenue data was found.")

    if not np.isfinite(monthly.to_numpy()).all():
        raise ValueError("Monthly revenue contains non-finite values.")

    if (monthly < 0).any():
        raise ValueError("Monthly revenue contains negative values.")

    expected_months = pd.date_range(
        monthly.index.min(),
        monthly.index.max(),
        freq="MS",
    )

    if not monthly.index.equals(expected_months):
        raise ValueError("Monthly revenue index is not continuous.")

    return monthly.astype(float)


# ============================================================
# FORECAST MODELS
# ============================================================

def forecast_seasonal_naive(train, test_index):
    """Repeat revenue from the same month one year earlier."""

    predictions = []

    for target_month in test_index:
        source_month = target_month - pd.DateOffset(years=1)

        if source_month not in train.index:
            raise ValueError(
                f"Missing seasonal-naive source month: {source_month}"
            )

        predictions.append(train.loc[source_month])

    return pd.Series(predictions, index=test_index)


def forecast_previous_month(train, test_index):
    """Repeat the final observed training month."""

    last_value = train.iloc[-1]

    return pd.Series(
        [last_value] * len(test_index),
        index=test_index,
        dtype=float,
    )


def forecast_moving_average(train, test_index, window=3):
    """Forecast each month using the last three observed months."""

    if len(train) < window:
        raise ValueError(
            f"At least {window} training months are required."
        )

    average = train.tail(window).mean()

    return pd.Series(
        [average] * len(test_index),
        index=test_index,
        dtype=float,
    )


def forecast_holt_winters(train, test_index):
    """Fit Holt-Winters only when two full seasonal cycles exist."""

    if len(train) < 24:
        return None

    model = ExponentialSmoothing(
        train,
        trend="add",
        seasonal="add",
        seasonal_periods=12,
        initialization_method="estimated",
    )

    fitted_model = model.fit(optimized=True)

    predictions = fitted_model.forecast(len(test_index))
    predictions.index = test_index

    return predictions.astype(float)



# ============================================================
# EVALUATION
# ============================================================

def calculate_metrics(actual, predicted):
    """Calculate error metrics; positive bias means over-forecasting."""

    actual_values = actual.to_numpy(dtype=float)
    predicted_values = predicted.to_numpy(dtype=float)

    errors = predicted_values - actual_values

    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors ** 2))

    nonzero_mask = actual_values != 0

    if nonzero_mask.any():
        mape = np.mean(
            np.abs(
                errors[nonzero_mask]
                / actual_values[nonzero_mask]
            )
        ) * 100
    else:
        mape = np.nan

    bias = np.mean(errors)

    return {
        "MAE": mae,
        "RMSE": rmse,
        "MAPE": mape,
        "Forecast_Bias": bias,
    }


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("FORECAST MODEL COMPARISON")
    print("=" * 60)

    monthly = load_monthly_revenue()

    test_start = pd.Timestamp(HOLDOUT_START)
    test_end = pd.Timestamp(HOLDOUT_END)

    train = monthly.loc[monthly.index < test_start]
    actual = monthly.loc[
        (monthly.index >= test_start)
        & (monthly.index <= test_end)
    ]

    if len(actual) != 6:
        raise ValueError(
            f"Expected 6 holdout months; found {len(actual)}."
        )

    if len(train) < 12:
        raise ValueError(
            "At least 12 months of training history are required."
        )

    print(f"Training period: {train.index.min():%Y-%m} "
          f"to {train.index.max():%Y-%m}")
    print(f"Holdout period: {actual.index.min():%Y-%m} "
          f"to {actual.index.max():%Y-%m}")
    print(f"Training months: {len(train)}")
    print(f"Holdout months: {len(actual)}")

    
    forecasts = {
        "Seasonal Naive": forecast_seasonal_naive(
            train, actual.index
        ),
        "Previous-Month Naive": forecast_previous_month(
            train, actual.index
        ),
        "3-Month Moving Average": forecast_moving_average(
            train, actual.index
        ),
        "Holt-Winters Additive": forecast_holt_winters(
            train, actual.index
        ),
    }

    unavailable_models = [
        name for name, predictions in forecasts.items()
        if predictions is None
    ]

    for name in unavailable_models:
        print(
            f"SKIPPED | {name}: insufficient training history "
            "for annual seasonality."
        )

    forecasts = {
        name: predictions
        for name, predictions in forecasts.items()
        if predictions is not None
    }

    results = []
    forecast_rows = []

    for model_name, predicted in forecasts.items():
        predicted = predicted.astype(float)

        if not np.isfinite(predicted.to_numpy()).all():
            raise ValueError(
                f"{model_name} produced non-finite forecasts."
            )

        metrics = calculate_metrics(actual, predicted)

        results.append({
            "model": model_name,
            **metrics,
        })

        for month, actual_value, predicted_value in zip(
            actual.index,
            actual.to_numpy(),
            predicted.to_numpy(),
        ):
            forecast_rows.append({
                "month": month.strftime("%Y-%m"),
                "model": model_name,
                "actual_revenue": actual_value,
                "forecast_revenue": predicted_value,
                "error": predicted_value - actual_value,
            })

    comparison = (
        pd.DataFrame(results)
        .sort_values("MAPE", ascending=True)
        .reset_index(drop=True)
    )

    comparison.insert(
        0,
        "rank_by_mape",
        range(1, len(comparison) + 1),
    )

    forecast_detail = pd.DataFrame(forecast_rows)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    comparison.to_csv(
        COMPARISON_FILE,
        index=False,
    )

    forecast_detail.to_csv(
        OUTPUT_DIR / "forecast_model_predictions.csv",
        index=False,
    )

    print("\n=== MODEL COMPARISON ===")
    print(comparison.to_string(index=False, float_format=lambda x: f"{x:,.2f}"))

    print("\n=== OUTPUT FILES ===")
    print(f"Comparison: {COMPARISON_FILE}")
    print(
        "Predictions: "
        f"{OUTPUT_DIR / 'forecast_model_predictions.csv'}"
    )

    print("\nComparison completed successfully.")


if __name__ == "__main__":
    main()
