# Automated Business Intelligence & Sales Forecasting Platform

An end-to-end Business Intelligence and sales forecasting portfolio
project combining Python data validation, sales analytics, forecasting,
demand planning, automated business insights, incremental synthetic data
generation, Power BI dashboards, automated tests, and GitHub Actions.

-   **Live portfolio website:**
    https://sakib075009.github.io/automated-bi-sales-forecasting/
-   **GitHub repository:**
    https://github.com/sakib075009/automated-bi-sales-forecasting

------------------------------------------------------------------------

## Project Overview

This project demonstrates how a reproducible analytics pipeline can
transform synthetic retail/e-commerce transaction data into business
KPIs, forecasts, customer segments, anomaly reports, scenario
comparisons, demand-planning summaries, and management recommendations.

The project combines Python analytics and validation with a Power BI
dashboard. It also includes an incremental synthetic-data generator with
integrity checks and recovery safeguards, automated tests, and a GitHub
Actions workflow.

**Current status:** The analytics pipeline, forecast model comparison,
demand-planning analysis, chart generation, nine-page Phase 5 Power BI
report, incremental generator, automated tests, GitHub Actions workflow,
and GitHub Pages website are implemented. Production activation of
incremental data generation and automatic publishing of refreshed
analytics to the portfolio website remain separate tasks.

## Key Features

### Data Engineering and Validation

-   Synthetic retail/e-commerce transaction data.
-   Validation of required columns, missing values, duplicate keys,
    foreign-key relationships, and business rules.
-   Validation of transaction dates, quantities, discounts, revenue,
    costs, and profit.
-   Incremental data generator with configurable simulated-date
    scheduling.
-   SHA-256 source-integrity checks.
-   State persistence, recovery journaling, backups, and rollback
    mechanisms.
-   Automated tests for scheduling, financial calculations, state
    persistence, source integrity, and recovery behavior.

### Business Intelligence and Analytics

-   Monthly revenue, cost, profit, order, customer, and quantity
    analysis.
-   Product, regional, channel, and payment-method performance.
-   Customer purchase-frequency and RFM segmentation.
-   Business KPI summaries and rule-based business insights.
-   Daily sales anomaly detection.
-   Sales scenario analysis.
-   Automated analytics-output validation.

### Revenue Forecasting

The project compares three forecasting baselines: **3-Month Moving
Average**, **Previous-Month Naive**, and **Seasonal Naive**.

Evaluation metrics include Mean Absolute Error (MAE), Root Mean Squared
Error (RMSE), Mean Absolute Percentage Error (MAPE), and forecast bias.
The model comparison uses a 12-month holdout period covering
January--December 2025. Forecast bias is calculated as
`forecast_revenue - actual_revenue`.

  ----------------------------------------------------------------------------
  Model                       MAE           RMSE           MAPE  Forecast Bias
  ---------------- -------------- -------------- -------------- --------------
  3-Month Moving    20.70 million  25.84 million         10.95%  -4.19 million
  Average

  Previous-Month    21.62 million  25.55 million         11.81%  +1.59 million
  Naive

  Seasonal Naive    40.87 million  41.05 million         22.51% -40.87 million
  ----------------------------------------------------------------------------

On this evaluation period, the 3-Month Moving Average has the lowest MAE
and MAPE, while Previous-Month Naive has the lowest RMSE. These results
are specific to this holdout period and do not guarantee future
performance.

The Seasonal Naive forward forecast uses revenue from the corresponding
month in the prior year. The current generated six-month point forecast
covers January--June 2026. Forecasts are estimates, not guaranteed
future revenue, and the current forecast does not include prediction
intervals. Holt-Winters was skipped by the current model-comparison
implementation because its minimum training-history requirement was not
met.

### Demand Trend and Planning

The demand-planning analysis produces monthly demand summaries, product
priorities, regional priorities, and management recommendations.

Current analysis includes:

- 24 complete monthly periods from January 2024 through December 2025.
- Historical monthly quantity and a three-month moving average.
- Year-over-year quantity comparisons.
- Exploratory calendar-month comparisons.
- High/Low demand-period classifications based on monthly quantity relative to the historical median.
- Product demand priorities for 75 products.
- Regional demand priorities for 8 regions.
- Five management recommendations.

The demand-period labels are historical comparisons against the median;
they are not, by themselves, proof of recurring seasonality, inventory
shortage, or operational underperformance. Only two years of monthly
observations are available, so calendar patterns should be treated as
exploratory.

Current highlights:

- Highest-quantity product in the current summary: **P0047**, with 9,984 units.
- Highest-quantity region in the current summary: **R03**, with 51,688 units.

#### Inventory Data Limitations

The current input data does not establish stock on hand, supplier lead
time, or stockout history. Therefore, the project does **not** currently
calculate defensible reorder points, safety stock, inventory coverage,
or stockout risk. Those calculations require appropriate inventory and
replenishment data.

### Generated Forecast and Demand Visualizations

The visualization script generates these charts under
`dashboard/figures/`:

-   `actual_vs_forecast_revenue.png`
-   `forecast_error_by_month.png`
-   `future_revenue_forecast.png`
-   `demand_trend_and_periods.png`

The future revenue chart combines historical monthly revenue with the
January--June 2026 point forecast. The demand trend chart presents
historical monthly quantity, the three-month moving average, and
exploratory high/low demand periods.

### Interactive Power BI Dashboard

The Phase 5 report contains nine pages:

1.  Business Intelligence Overview
2.  Sales & Revenue Analysis
3.  Customer Analytics
4.  Product & Pareto Analysis
5.  Regional Performance
6.  Channel & Payment Analysis
7.  Promotion & Discount Analysis
8.  Decision Support
9.  Forecasting & Demand Planning

The new **Forecasting & Demand Planning** page includes:

- Forecast model accuracy comparison using MAPE.
- Monthly revenue forecast for January--June 2026.
- Monthly demand trend and three-month moving average.
- Average quantity comparison for historically High and Low demand periods.
- Top 10 products by historical quantity.
- Regional demand priorities by quantity.
- Management recommendations.

The Phase 5 Power BI file is
`powerbi/Automated_BI_Sales_Forecasting_Phase5.pbix`. Earlier report
versions are retained separately for version history.

## Dataset

The project uses **synthetic data** for demonstration and portfolio
purposes. It does not represent actual business transactions.

  Dataset          Initial record count
  -------------- ----------------------
  Fact Sales                    120,000
  Dim Customer                    1,500
  Dim Date                          731
  Dim Product                        75
  Dim Region                          8

The original historical sales period runs from January 1, 2024, through
December 31, 2025. The incremental generator is designed to extend the
sales fact table and date dimension when explicitly activated. The local
working dataset may contain additional simulated records created during
development.

The data follows a dimensional model with a sales fact table and
customer, date, product, and region dimensions.

### Business Metrics

The analytics pipeline calculates total revenue, cost, profit, profit
margin, orders, customers, average order value, product and regional
revenue, sales-channel and payment-method performance, customer purchase
frequency and RFM segments, forecast accuracy and bias, daily sales
anomalies, scenario-based outcomes, demand trends, and product/regional
priorities.

## Incremental Data Generation

The incremental generator is designed to extend the dataset while
protecting source-data integrity.

Its intended workflow is: 1. Determine the next simulated sales date. 2.
Apply the configured simulated-date schedule and date cutoff. 3.
Generate approximately 40--50 sales records per simulated day. 4.
Validate generated financial values and data relationships. 5. Update
the sales fact table and date dimension. 6. Persist generator state and
integrity metadata. 7. Use recovery mechanisms to protect against failed
writes.

The generator uses SHA-256 source-integrity checks, state tracking, a
pending-operation journal, backups, and recovery mechanisms. The
existing recovery and integrity test suite contains 13 tests. An
isolated end-to-end test has also successfully exercised incremental
generation, data validation, the analytics pipeline, and output
validation without modifying production data.

**Important:** The generator defaults to preview mode. Production
activation has not been established as an automated production process.
Review the date-selection logic, configuration, source paths, backups,
and recovery procedures before using `--apply` on important data.

## Analytics Pipeline and Output Validation

Run the configured analytics pipeline:

``` powershell
python src/run_analytics_pipeline.py
```

The configured pipeline runs forecast model comparison, anomaly
detection, customer RFM segmentation, scenario analysis, business
insights, and output validation.

Demand-planning analysis and chart generation are separate scripts:

``` powershell
python src/demand_planning_analysis.py
python src/forecast_visualizations.py
python src/validate_analytics_outputs.py
```

During Phase 5 development, output validation completed with **76 checks
passed and 0 failed** after the refreshed outputs were generated.
Results can change when source data or code changes, so rerun validation
after future modifications.

Generated analytics outputs under `data/outputs/` are reproducible and
excluded from Git tracking. Visualization PNG files are generated under
`dashboard/figures/`.

## GitHub Actions Automation

The repository includes `.github/workflows/daily_pipeline.yml`.

The workflow: 1. Checks out the repository. 2. Sets up Python 3.12. 3.
Installs analytics dependencies. 4. Validates the committed source
dataset. 5. Runs the configured analytics pipeline. 6. Uploads generated
analytics outputs as a downloadable workflow artifact.

The workflow supports manual execution and scheduled execution at 03:00
UTC (09:00 Bangladesh time).

Generated outputs are uploaded as artifacts with a 14-day retention
period. The workflow currently processes the committed source dataset;
it does not automatically activate incremental data generation or
publish refreshed analytics to the portfolio website.

## Technology Stack

-   **Programming:** Python
-   **Data processing:** Pandas, NumPy
-   **Analytics and validation:** Python
-   **Forecasting:** Moving-average, previous-month naive, and
    seasonal-naive baselines
-   **Business Intelligence:** Microsoft Power BI, DAX
-   **Testing:** Python `unittest`
-   **Version control:** Git, GitHub
-   **Automation:** GitHub Actions
-   **Portfolio deployment:** GitHub Pages

## Project Structure

```text
project-01/
|-- .github/
|   `-- workflows/
|       `-- daily_pipeline.yml
|-- dashboard/
|   `-- figures/
|       |-- actual_vs_forecast_revenue.png
|       |-- forecast_error_by_month.png
|       |-- future_revenue_forecast.png
|       `-- demand_trend_and_periods.png
|-- data/
|   |-- raw/
|   |-- processed/
|   |-- outputs/                  # Generated; excluded from Git
|   `-- backups/                  # Local backups; excluded from Git
|-- notebooks/
|-- powerbi/
|   |-- Automated_BI_Sales_Forecasting.pbix
|   |-- Automated_BI_Sales_Forecasting_Phase2_DAX_Complete.pbix
|   `-- Automated_BI_Sales_Forecasting_Phase5.pbix
|-- src/
|   |-- data_validation.py
|   |-- incremental_data_generator.py
|   |-- demand_planning_analysis.py
|   |-- forecast_model_comparison.py
|   |-- forecast_visualizations.py
|   |-- sales_anomaly_detection.py
|   |-- customer_rfm_segmentation.py
|   |-- sales_scenario_analysis.py
|   |-- business_insights_engine.py
|   |-- validate_analytics_outputs.py
|   `-- run_analytics_pipeline.py
|-- tests/
|   |-- test_incremental_recovery.py
|   `-- test_demand_planning.py
|-- .gitignore
|-- README.md
`-- requirements.txt
```
## Getting Started

### Prerequisites

-   Python 3.12 recommended for the automation workflow
-   Git
-   Microsoft Power BI Desktop to explore the report

### 1. Clone the Repository

``` powershell
git clone https://github.com/sakib075009/automated-bi-sales-forecasting.git
cd automated-bi-sales-forecasting
```

### 2. Create and Activate a Virtual Environment

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

``` powershell
python -m pip install -r requirements.txt
```

### 4. Validate the Dataset

``` powershell
python src/data_validation.py
```

### 5. Run the Analytics Pipeline

``` powershell
python src/run_analytics_pipeline.py
```

### 6. Run Demand Planning and Refresh Visualizations

``` powershell
python src/demand_planning_analysis.py
python src/forecast_visualizations.py
python src/validate_analytics_outputs.py
```

### 7. Run the Tests

``` powershell
python -m unittest tests.test_incremental_recovery -v
python -m unittest tests.test_demand_planning -v
```

### 8. Preview the Incremental Generator

``` powershell
python src/incremental_data_generator.py
```

Preview mode does not activate production writes. Do not use `--apply`
until the configuration, date-selection behavior, backups, source
integrity, and recovery behavior have been reviewed.

### 9. Explore the Power BI Report

Open `powerbi/Automated_BI_Sales_Forecasting_Phase5.pbix` in Power BI
Desktop to explore the nine-page Phase 5 report. Update data-source
paths if necessary, then refresh the report.

## Current Implementation Status

### Implemented

-   Synthetic historical sales dataset and dimensional data model
-   Source-data validation
-   Configured analytics pipeline and output validation
-   Forecast model comparison and prediction outputs
-   Forecast visualization generation
-   Sales anomaly detection
-   Customer RFM segmentation
-   Sales scenario analysis
-   Business KPI and insight generation
-   Demand trend, product and regional demand-priority analysis
-   Management recommendations with documented inventory-data
    limitations
-   Nine-page Phase 5 Power BI report
-   Incremental generator with integrity and recovery safeguards
-   Automated tests
-   GitHub Actions workflow with artifact upload
-   GitHub Pages portfolio website

### Remaining Work

-   Complete production-readiness review of incremental generation,
    including date-selection behavior.
-   Decide when and how to activate incremental generation safely.
-   Validate the intended long-term scheduled workflow with an
    appropriate data strategy.
-   Decide whether and how refreshed analytics should be published to
    the website.
-   Add inventory-on-hand, supplier lead-time, and stockout data before
    implementing inventory optimization calculations.
-   Refresh the website screenshots to show the new report page.
-   Complete final repository review and publish approved changes.

## Future Development

Potential enhancements include more advanced forecasting models,
inventory and replenishment planning using inventory inputs, automated
report publishing, expanded business decision support, and an
AI-assisted business analytics interface.

New features should be added after the existing pipeline,
data-generation behavior, and automation are fully reviewed.

## Screenshots and Portfolio

The portfolio website presents the project and its dashboard
screenshots:

**Website:**
https://sakib075009.github.io/automated-bi-sales-forecasting/

The website screenshots may need to be refreshed separately to reflect
the new Forecasting & Demand Planning page.

## Author and Repository

**GitHub repository:**
https://github.com/sakib075009/automated-bi-sales-forecasting

This project demonstrates practical skills in Business Intelligence,
Python analytics, forecasting, demand planning, data validation,
automated testing, workflow automation, and portfolio deployment.
