from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_OUTPUTS = PROJECT_ROOT / "data" / "outputs"


# ============================================================
# FILE PATHS
# ============================================================

FACT_SALES_FILE = DATA_RAW / "fact_sales.csv"
OUTPUT_FILE = DATA_OUTPUTS / "monthly_summary.csv"

PRODUCT_OUTPUT_FILE = (
    DATA_OUTPUTS / "product_summary.csv"
)

REGIONAL_OUTPUT_FILE = (
    DATA_OUTPUTS / "regional_summary.csv"
)

CHANNEL_OUTPUT_FILE = (
    DATA_OUTPUTS / "channel_summary.csv"
)

CUSTOMER_OUTPUT_FILE = (
    DATA_OUTPUTS / "customer_summary.csv"
)

KPI_OUTPUT_FILE = (
    DATA_OUTPUTS / "business_kpis.csv"
)

INSIGHTS_OUTPUT_FILE = (
    DATA_OUTPUTS / "business_insights.csv"
)

FORECAST_INPUT_FILE = (
    DATA_OUTPUTS / "forecast_input.csv"
)

FORECAST_OUTPUT_FILE = (
    DATA_OUTPUTS / "revenue_forecast.csv"
)

FORECAST_METRICS_FILE = (
    DATA_OUTPUTS / "forecast_metrics.csv"
)

# ============================================================
# LOAD DATA
# ============================================================

def load_sales_data():
    """Load the fact sales dataset."""

    df = pd.read_csv(FACT_SALES_FILE)

    df["order_date"] = pd.to_datetime(
        df["order_date"],
        errors="raise"
    )

    return df


# ============================================================
# MONTHLY ANALYTICS
# ============================================================

def create_monthly_summary(df):
    """Create monthly business performance summary."""

    monthly = (
        df.groupby(
            df["order_date"].dt.to_period("M")
        )
        .agg(
            revenue=("revenue", "sum"),
            cost=("cost", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            customers=("customer_id", "nunique"),
            quantity=("quantity", "sum"),
            sales_lines=("sales_id", "count"),
        )
        .reset_index()
    )

    # Convert Period to string for CSV compatibility
    monthly["month"] = (
        monthly["order_date"]
        .astype(str)
    )

    monthly.drop(
        columns=["order_date"],
        inplace=True
    )

    # Business KPIs
    monthly["profit_margin"] = (
        monthly["profit"]
        / monthly["revenue"]
    )

    monthly["aov"] = (
        monthly["revenue"]
        / monthly["orders"]
    )

    monthly["average_quantity_per_order"] = (
        monthly["quantity"]
        / monthly["orders"]
    )

    # Reorder columns
    monthly = monthly[
        [
            "month",
            "revenue",
            "cost",
            "profit",
            "profit_margin",
            "orders",
            "customers",
            "quantity",
            "sales_lines",
            "aov",
            "average_quantity_per_order",
        ]
    ]

    return monthly

def create_forecast_input(monthly_summary):
    """Prepare monthly revenue data for forecasting."""

    forecast_input = monthly_summary[
        ["month", "revenue"]
    ].copy()

    forecast_input["month"] = pd.to_datetime(
        forecast_input["month"],
        errors="raise"
    )

    forecast_input = forecast_input.sort_values(
        "month"
    )

    forecast_input = forecast_input.reset_index(
        drop=True
    )

    return forecast_input

def create_baseline_forecast(
    forecast_input,
    forecast_periods=6
):
    """Create a seasonal-naive revenue forecast."""

    history = forecast_input.copy()

    history["month"] = pd.to_datetime(
        history["month"],
        errors="raise"
    )

    history = history.sort_values(
        "month"
    ).reset_index(drop=True)

    last_actual_month = history["month"].max()

    forecast_dates = pd.date_range(
        start=last_actual_month
        + pd.DateOffset(months=1),
        periods=forecast_periods,
        freq="MS"
    )

    forecast_rows = []

    for forecast_date in forecast_dates:

        comparable_month = (
            forecast_date
            - pd.DateOffset(years=1)
        )

        matching_history = history[
            history["month"] == comparable_month
        ]

        if matching_history.empty:
            forecast_revenue = None
        else:
            forecast_revenue = (
                matching_history["revenue"]
                .iloc[0]
            )

        forecast_rows.append(
            {
                "forecast_month": forecast_date,
                "forecast_revenue": forecast_revenue,
                "method": "Seasonal Naive",
                "source_month": comparable_month,
            }
        )

    forecast = pd.DataFrame(
        forecast_rows
    )

    return forecast

def evaluate_baseline_forecast(forecast_input):
    """Evaluate seasonal-naive forecast using historical holdout data."""

    data = forecast_input.copy()

    data["month"] = pd.to_datetime(
        data["month"],
        errors="raise"
    )

    data = data.sort_values(
        "month"
    ).reset_index(drop=True)

    # Use 2024 as training history
    train = data[
        data["month"].dt.year == 2024
    ].copy()

    # Use 2025 as the historical test period
    test = data[
        data["month"].dt.year == 2025
    ].copy()

    test["source_month"] = (
        test["month"]
        - pd.DateOffset(years=1)
    )

    test = test.merge(
        train[
            ["month", "revenue"]
        ],
        left_on="source_month",
        right_on="month",
        how="left",
        suffixes=("_actual", "_forecast")
    )

    test = test.rename(
        columns={
            "revenue_actual": "actual_revenue",
            "revenue_forecast": "forecast_revenue",
        }
    )

    test["error"] = (
        test["actual_revenue"]
        - test["forecast_revenue"]
    )

    test["absolute_error"] = (
        test["error"].abs()
    )

    test["squared_error"] = (
        test["error"] ** 2
    )

    test["absolute_percentage_error"] = (
        test["absolute_error"]
        / test["actual_revenue"]
    )

    mae = (
        test["absolute_error"].mean()
    )

    rmse = (
        test["squared_error"].mean()
        ** 0.5
    )

    mape = (
        test["absolute_percentage_error"].mean()
        * 100
    )

    metrics = pd.DataFrame(
        {
            "metric": [
                "MAE",
                "RMSE",
                "MAPE",
            ],
            "value": [
                mae,
                rmse,
                mape,
            ],
        }
    )

    return metrics, test

def save_forecast_metrics(df):
    """Save forecast accuracy metrics."""

    DATA_OUTPUTS.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        FORECAST_METRICS_FILE,
        index=False
    )

    print(
        f"SAVED | {FORECAST_METRICS_FILE}"
    )


def save_forecast_output(df):
    """Save revenue forecast output."""

    DATA_OUTPUTS.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        FORECAST_OUTPUT_FILE,
        index=False
    )

    print(
        f"SAVED | {FORECAST_OUTPUT_FILE}"
    )

def save_forecast_input(df):
    """Save forecasting input dataset."""

    DATA_OUTPUTS.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        FORECAST_INPUT_FILE,
        index=False
    )

    print(
        f"SAVED | {FORECAST_INPUT_FILE}"
    )

# ============================================================
# PRODUCT ANALYTICS
# ============================================================

def create_product_summary(df):
    """Create product-level business performance summary."""

    product = (
        df.groupby("product_id")
        .agg(
            revenue=("revenue", "sum"),
            cost=("cost", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            customers=("customer_id", "nunique"),
            quantity=("quantity", "sum"),
            sales_lines=("sales_id", "count"),
        )
        .reset_index()
    )

    # Business KPIs
    product["profit_margin"] = (
        product["profit"]
        / product["revenue"]
    )

    product["average_selling_price"] = (
        product["revenue"]
        / product["quantity"]
    )

    product["profit_per_unit"] = (
        product["profit"]
        / product["quantity"]
    )

    # Sort by revenue
    product = product.sort_values(
        "revenue",
        ascending=False
    )

    return product

# ============================================================
# REGIONAL ANALYTICS
# ============================================================

def create_regional_summary(df):
    """Create region-level business performance summary."""

    regional = (
        df.groupby("region_id")
        .agg(
            revenue=("revenue", "sum"),
            cost=("cost", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            customers=("customer_id", "nunique"),
            quantity=("quantity", "sum"),
            sales_lines=("sales_id", "count"),
        )
        .reset_index()
    )

    regional["profit_margin"] = (
        regional["profit"]
        / regional["revenue"]
    )

    regional["aov"] = (
        regional["revenue"]
        / regional["orders"]
    )

    regional["revenue_per_customer"] = (
        regional["revenue"]
        / regional["customers"]
    )

    regional = regional.sort_values(
        "revenue",
        ascending=False
    )

    return regional


# ============================================================
# SALES CHANNEL ANALYTICS
# ============================================================

def create_channel_summary(df):
    """Create sales-channel performance summary."""

    channel = (
        df.groupby("sales_channel")
        .agg(
            revenue=("revenue", "sum"),
            cost=("cost", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            customers=("customer_id", "nunique"),
            quantity=("quantity", "sum"),
            sales_lines=("sales_id", "count"),
        )
        .reset_index()
    )

    channel["profit_margin"] = (
        channel["profit"]
        / channel["revenue"]
    )

    channel["aov"] = (
        channel["revenue"]
        / channel["orders"]
    )

    channel["revenue_share"] = (
        channel["revenue"]
        / channel["revenue"].sum()
    )

    channel = channel.sort_values(
        "revenue",
        ascending=False
    )

    return channel



def create_customer_summary(df):
    """Create customer-level business performance summary."""

    customer = (
        df.groupby("customer_id")
        .agg(
            revenue=("revenue", "sum"),
            cost=("cost", "sum"),
            profit=("profit", "sum"),
            orders=("order_id", "nunique"),
            quantity=("quantity", "sum"),
            sales_lines=("sales_id", "count"),
            first_purchase_date=("order_date", "min"),
            last_purchase_date=("order_date", "max"),
        )
        .reset_index()
    )

    customer["profit_margin"] = (
        customer["profit"]
        / customer["revenue"]
    )

    customer["aov"] = (
        customer["revenue"]
        / customer["orders"]
    )

    reference_date = df["order_date"].max()

    customer["days_since_last_purchase"] = (
        reference_date
        - customer["last_purchase_date"]
    ).dt.days

    customer["is_repeat_customer"] = (
        customer["orders"] > 1
    )

    customer = customer.sort_values(
        "revenue",
        ascending=False
    )

    return customer


# ============================================================
# SAVE OUTPUT
# ============================================================

def save_output(df):
    """Save monthly analytics output."""

    DATA_OUTPUTS.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"SAVED | {OUTPUT_FILE}"
    )

def save_product_output(df):
    """Save product analytics output."""

    DATA_OUTPUTS.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        PRODUCT_OUTPUT_FILE,
        index=False
    )

    print(
        f"SAVED | {PRODUCT_OUTPUT_FILE}"
    )

def save_regional_output(df):
    """Save regional analytics output."""

    DATA_OUTPUTS.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        REGIONAL_OUTPUT_FILE,
        index=False
    )

    print(
        f"SAVED | {REGIONAL_OUTPUT_FILE}"
    )


def save_channel_output(df):
    """Save sales-channel analytics output."""

    DATA_OUTPUTS.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        CHANNEL_OUTPUT_FILE,
        index=False
    )

    print(
        f"SAVED | {CHANNEL_OUTPUT_FILE}"
    )

def save_customer_output(df):
    """Save customer analytics output."""

    DATA_OUTPUTS.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        CUSTOMER_OUTPUT_FILE,
        index=False
    )

    print(
        f"SAVED | {CUSTOMER_OUTPUT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PYTHON ANALYTICS ENGINE")
    print("=" * 60)

    # Load
    print("\n=== DATA LOADING ===")

    df = load_sales_data()

    print(
        f"LOADED | fact_sales: "
        f"{df.shape}"
    )

    # Analytics
    print("\n=== MONTHLY ANALYTICS ===")

    monthly = create_monthly_summary(df)

    print(
        f"CREATED | Monthly summary: "
        f"{monthly.shape}"
    )

    # Forecasting input
    print("\n=== FORECASTING INPUT ===")

    forecast_input = create_forecast_input(
        monthly
    )

    print(
        f"CREATED | Forecast input: "
        f"{forecast_input.shape}"
    )

    print("\n=== FORECAST INPUT SAMPLE ===")

    print(
        forecast_input.head(5).to_string(
            index=False
        )
    )

    print("\n=== FORECAST INPUT END ===")

    print(
        forecast_input.tail(5).to_string(
            index=False
        )
    )

    save_forecast_input(
        forecast_input
    )

    # Revenue forecasting
    print("\n=== REVENUE FORECAST ===")

    forecast = create_baseline_forecast(
        forecast_input,
        forecast_periods=6
    )

    print(
        f"CREATED | Revenue forecast: "
        f"{forecast.shape}"
    )

    print("\n=== FORECAST ===")

    print(
        forecast.to_string(
            index=False
        )
    )

    save_forecast_output(
        forecast
    )

    # Display first rows
    print("\n=== SAMPLE OUTPUT ===")

    print(
        monthly.head().to_string(
            index=False
        )
    )

    # Save
    print("\n=== OUTPUT ===")

    save_output(monthly)

    print("\n" + "=" * 60)
    print("ANALYTICS ENGINE COMPLETED")
    print("=" * 60)

    # Product analytics
    print("\n=== PRODUCT ANALYTICS ===")

    product = create_product_summary(df)

    print(
        f"CREATED | Product summary: "
        f"{product.shape}"
    )

    print("\n=== TOP 5 PRODUCTS ===")

    print(
        product.head(5).to_string(
            index=False
        )
    )

    save_product_output(product)

    # Regional analytics
    print("\n=== REGIONAL ANALYTICS ===")

    regional = create_regional_summary(df)

    print(
        f"CREATED | Regional summary: "
        f"{regional.shape}"
    )

    print("\n=== REGIONAL SUMMARY ===")

    print(
        regional.to_string(
            index=False
        )
    )

    save_regional_output(regional)

    # Channel analytics
    print("\n=== CHANNEL ANALYTICS ===")

    channel = create_channel_summary(df)

    print(
        f"CREATED | Channel summary: "
        f"{channel.shape}"
    )

    print("\n=== CHANNEL SUMMARY ===")

    print(
        channel.to_string(
            index=False
        )
    )

    save_channel_output(channel)

    # Customer analytics
    print("\n=== CUSTOMER ANALYTICS ===")

    customer = create_customer_summary(df)

    print(
        f"CREATED | Customer summary: "
        f"{customer.shape}"
    )

    print("\n=== TOP 10 CUSTOMERS ===")

    print(
        customer.head(10).to_string(
            index=False
        )
    )

    save_customer_output(customer)

    # Business KPI summary
    print("\n=== BUSINESS KPI SUMMARY ===")

    kpis = create_business_kpis(df)

    print(
        f"CREATED | Business KPI summary: "
        f"{kpis.shape}"
    )

    print("\n=== BUSINESS KPIs ===")

    print(
        kpis.to_string(
            index=False
        )
    )

    save_kpi_output(kpis)

    # Automated business insights
    print("\n=== AUTOMATED BUSINESS INSIGHTS ===")

    insights = create_business_insights(df)

    print(
        f"CREATED | Business insights: "
        f"{insights.shape}"
    )

    print("\n=== INSIGHTS ===")

    print(
        insights.to_string(
            index=False
        )
    )

    save_insights_output(insights)

    # Forecast accuracy evaluation
    print("\n=== FORECAST ACCURACY ===")

    metrics, forecast_test = (
        evaluate_baseline_forecast(
            forecast_input
        )
    )

    print(
        f"CREATED | Forecast metrics: "
        f"{metrics.shape}"
    )

    print("\n=== FORECAST METRICS ===")

    print(
        metrics.to_string(
            index=False
        )
    )

    print("\n=== HISTORICAL FORECAST TEST ===")

    print(
        forecast_test[
            [
                "month_actual",
                "actual_revenue",
                "forecast_revenue",
                "error",
            ]
        ].to_string(
            index=False
        )
    )

    save_forecast_metrics(
        metrics
    )

def create_business_kpis(df):
    """Create overall business KPI summary."""

    total_revenue = df["revenue"].sum()
    total_cost = df["cost"].sum()
    total_profit = df["profit"].sum()
    total_orders = df["order_id"].nunique()
    total_customers = df["customer_id"].nunique()
    total_quantity = df["quantity"].sum()

    profit_margin = (
        total_profit / total_revenue
        if total_revenue != 0
        else 0
    )

    average_order_value = (
        total_revenue / total_orders
        if total_orders != 0
        else 0
    )

    average_quantity_per_order = (
        total_quantity / total_orders
        if total_orders != 0
        else 0
    )

    kpis = pd.DataFrame(
        {
            "metric": [
                "Total Revenue",
                "Total Cost",
                "Total Profit",
                "Profit Margin",
                "Total Orders",
                "Total Customers",
                "Total Quantity",
                "Average Order Value",
                "Average Quantity per Order",
            ],
            "value": [
                total_revenue,
                total_cost,
                total_profit,
                profit_margin,
                total_orders,
                total_customers,
                total_quantity,
                average_order_value,
                average_quantity_per_order,
            ],
        }
    )

    return kpis

def save_kpi_output(df):
    """Save business KPI output."""

    DATA_OUTPUTS.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        KPI_OUTPUT_FILE,
        index=False
    )

    print(
        f"SAVED | {KPI_OUTPUT_FILE}"
    )


def create_business_insights(df):
    """Generate rule-based business insights."""

    insights = []

    # -----------------------------
    # Overall business performance
    # -----------------------------
    total_revenue = df["revenue"].sum()
    total_profit = df["profit"].sum()

    profit_margin = (
        total_profit / total_revenue
        if total_revenue != 0
        else 0
    )

    insights.append(
        f"Overall profitability: "
        f"profit margin is {profit_margin:.2%}."
    )

    # -----------------------------
    # Year-over-year growth
    # -----------------------------
    df["year"] = df["order_date"].dt.year

    yearly_revenue = (
        df.groupby("year")["revenue"]
        .sum()
        .sort_index()
    )

    yearly_profit = (
        df.groupby("year")["profit"]
        .sum()
        .sort_index()
    )

    if len(yearly_revenue) >= 2:

        current_year = yearly_revenue.index[-1]
        previous_year = yearly_revenue.index[-2]

        revenue_growth = (
            yearly_revenue.loc[current_year]
            / yearly_revenue.loc[previous_year]
            - 1
        )

        profit_growth = (
            yearly_profit.loc[current_year]
            / yearly_profit.loc[previous_year]
            - 1
        )

        insights.append(
            f"Business growth: revenue grew "
            f"{revenue_growth:.2%} and profit grew "
            f"{profit_growth:.2%} from "
            f"{previous_year} to {current_year}."
        )

    # -----------------------------
    # Top product
    # -----------------------------
    product_revenue = (
        df.groupby("product_id")["revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    if not product_revenue.empty:

        top_product = product_revenue.index[0]
        top_product_revenue = product_revenue.iloc[0]

        insights.append(
            f"Top product: {top_product} generated "
            f"{top_product_revenue:,.2f} in revenue."
        )

    # -----------------------------
    # Top region
    # -----------------------------
    region_revenue = (
        df.groupby("region_id")["revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    if not region_revenue.empty:

        top_region = region_revenue.index[0]
        top_region_revenue = region_revenue.iloc[0]

        insights.append(
            f"Top region: {top_region} generated "
            f"{top_region_revenue:,.2f} in revenue."
        )

    # -----------------------------
    # Top sales channel
    # -----------------------------
    channel_revenue = (
        df.groupby("sales_channel")["revenue"]
        .sum()
        .sort_values(ascending=False)
    )

    if not channel_revenue.empty:

        top_channel = channel_revenue.index[0]
        top_channel_revenue = channel_revenue.iloc[0]

        channel_share = (
            top_channel_revenue / total_revenue
            if total_revenue != 0
            else 0
        )

        insights.append(
            f"Top sales channel: {top_channel} "
            f"accounts for {channel_share:.2%} "
            f"of total revenue."
        )

    # -----------------------------
    # Negative-profit transactions
    # -----------------------------
    negative_profit_count = (
        df["profit"] < 0
    ).sum()

    negative_profit_value = (
        df.loc[df["profit"] < 0, "profit"].sum()
    )

    insights.append(
        f"Profit risk: {negative_profit_count:,} "
        f"sales transactions generated negative profit, "
        f"with a combined impact of "
        f"{negative_profit_value:,.2f}."
    )

    # -----------------------------
    # Result dataframe
    # -----------------------------
    result = pd.DataFrame(
        {
            "insight_id": range(
                1,
                len(insights) + 1
            ),
            "insight": insights,
        }
    )

    return result

def save_insights_output(df):
    """Save automated business insights."""

    DATA_OUTPUTS.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        INSIGHTS_OUTPUT_FILE,
        index=False
    )

    print(
        f"SAVED | {INSIGHTS_OUTPUT_FILE}"
    )
# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()

