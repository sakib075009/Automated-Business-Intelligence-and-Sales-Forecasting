# Automated Business Intelligence & Sales Forecasting Platform

An end-to-end Business Intelligence and sales forecasting portfolio project combining Python data engineering, sales analytics, forecasting, customer analytics, anomaly detection, demand planning, scenario analysis, rule-based business insights, Power BI dashboards, automated tests, and GitHub Actions.

<p align="center">
  <a href="https://sakib075009.github.io/Automated-Business-Intelligence-and-Sales-Forecasting">Live Portfolio Website</a> ·
  <a href="https://sakib075009.github.io/automated-bi-sales-forecasting/#dashboard">Dashboard Gallery</a> ·
  <a href="https://github.com/sakib075009/automated-bi-sales-forecasting">GitHub Repository</a> ·
  <a href="https://github.com/sakib075009/automated-bi-sales-forecasting/actions">GitHub Actions</a>
</p>

---

## Project Overview

This project demonstrates how a reproducible analytics pipeline can transform synthetic retail and e-commerce transaction data into business KPIs, revenue forecasts, customer summaries, anomaly reports, scenario comparisons, demand-planning outputs, and management recommendations.

The project combines Python data validation and analytics, a Power BI report, an incremental synthetic-data generator with integrity and recovery safeguards, automated tests, and a GitHub Actions workflow.

**Data note:** The project uses synthetic data for demonstration and portfolio purposes. It does not represent actual business transactions.

## Project Resources

- **Live portfolio:** https://sakib075009.github.io/automated-bi-sales-forecasting/
- **Dashboard gallery:** https://sakib075009.github.io/automated-bi-sales-forecasting/#dashboard
- **GitHub repository:** https://github.com/sakib075009/automated-bi-sales-forecasting
- **Source code:** https://github.com/sakib075009/automated-bi-sales-forecasting/tree/main/src
- **Power BI reports:** https://github.com/sakib075009/automated-bi-sales-forecasting/tree/main/powerbi
- **Automated tests:** https://github.com/sakib075009/automated-bi-sales-forecasting/tree/main/tests
- **GitHub Actions workflow:** https://github.com/sakib075009/automated-bi-sales-forecasting/blob/main/.github/workflows/daily_pipeline.yml
- **Workflow execution history:** https://github.com/sakib075009/automated-bi-sales-forecasting/actions
- **Python dependencies:** https://github.com/sakib075009/automated-bi-sales-forecasting/blob/main/requirements.txt

## Key Features

### Data Engineering and Validation

- Synthetic retail and e-commerce transaction data.
- Validation of required columns, missing values, duplicate keys, foreign-key relationships, and business rules.
- Checks for transaction dates, quantities, discounts, revenue, costs, and profit.
- Incremental data generation with simulated-date scheduling and safety controls.
- SHA-256 source-integrity checks.
- State persistence, pending-operation journaling, backups, and recovery mechanisms.
- Automated tests for generator scheduling, financial calculations, state persistence, source integrity, and recovery behavior.

### Business Intelligence and Sales Analytics

- Revenue, cost, profit, profit margin, orders, customers, quantity, and average order value.
- Product, regional, sales-channel, and payment-method performance.
- Customer purchase-frequency and RFM summaries.
- KPI summaries and rule-based business insights.
- Daily sales anomaly detection.
- Sales scenario analysis.
- Automated analytics-output validation.

### Revenue Forecasting

The project compares three forecasting baselines: **3-Month Moving Average**, **Previous-Month Naive**, and **Seasonal Naive**.

The comparison uses a 12-month holdout period covering January–December 2025. Evaluation metrics include Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), Mean Absolute Percentage Error (MAPE), and forecast bias. Forecast bias is calculated as `forecast_revenue - actual_revenue`.

#### Recorded holdout results

| Model | MAE | RMSE | MAPE | Forecast bias |
|---|---:|---:|---:|---:|
| 3-Month Moving Average | 20.70 million | 25.84 million | 10.95% | -4.19 million |
| Previous-Month Naive | 21.62 million | 25.55 million | 11.81% | +1.59 million |
| Seasonal Naive | 40.87 million | 41.05 million | 22.51% | -40.87 million |

For this evaluation period, the 3-Month Moving Average has the lowest MAE and MAPE, while Previous-Month Naive has the lowest RMSE. These results describe this holdout period only and do not guarantee future performance.

The Seasonal Naive forward forecast uses revenue from the corresponding month in the prior year. The documented forecast output covers January–June 2026. These are point estimates, not guaranteed future revenue, and the forecast does not include prediction intervals. The original model-comparison documentation reports that Holt-Winters was skipped because its minimum training-history requirement was not met. Re-run the comparison to confirm behavior for the current data and code.

### Demand Trend and Planning

The demand-planning analysis produces monthly demand summaries, product priorities, regional priorities, and management recommendations.

The documented analysis includes:

- 24 monthly periods from January 2024 through December 2025.
- Historical monthly quantity and a three-month moving average.
- Year-over-year quantity comparisons.
- Exploratory calendar-month comparisons.
- High/Low demand-period classifications based on monthly quantity relative to the historical median.
- Product demand priorities for 75 products.
- Regional demand priorities for 8 regions.
- Five management recommendations.

Recorded highlights in the original analysis were product **P0047**, with 9,984 units, and region **R03**, with 51,688 units. These are historical analysis outputs; rerun demand planning to verify them against current data.

The demand-period labels are comparisons against the historical median. They are not, by themselves, proof of recurring seasonality, inventory shortage, or operational underperformance. With only two years of monthly observations in that analysis, calendar patterns should be treated as exploratory.

#### Inventory data limitations

The documented input data does not establish stock on hand, supplier lead time, or stockout history. Therefore, the project should not claim to calculate defensible reorder points, safety stock, inventory coverage, or stockout risk without appropriate inventory and replenishment data.

### Generated Forecast and Demand Visualizations

The visualization script generates charts under `dashboard/figures/`:

- `actual_vs_forecast_revenue.png`
- `forecast_error_by_month.png`
- `future_revenue_forecast.png`
- `demand_trend_and_periods.png`

The future-revenue chart combines historical monthly revenue with the January–June 2026 point forecast. The demand-trend chart presents historical monthly quantity, the three-month moving average, and exploratory high/low demand periods.

### Interactive Power BI Dashboard

The original Phase 5 report documentation lists nine pages:

1. Business Intelligence Overview
2. Sales & Revenue Analysis
3. Customer Analytics
4. Product & Pareto Analysis
5. Regional Performance
6. Channel & Payment Analysis
7. Promotion & Discount Analysis
8. Decision Support
9. Forecasting & Demand Planning

The documented **Forecasting & Demand Planning** page includes forecast-model accuracy comparison using MAPE, the January–June 2026 monthly revenue forecast, monthly demand trends and a three-month moving average, average quantity comparisons for historical High and Low demand periods, top 10 products by historical quantity, regional demand priorities, and management recommendations.

The tracked Phase 5 report is `powerbi/Automated_BI_Sales_Forecasting_Phase5.pbix`. Earlier report versions may be available in the `powerbi/` directory. Check the current repository for the exact tracked files and use Microsoft Power BI Desktop to open the intended report. If the report uses local file paths, update its data-source settings before refreshing.

## Dataset and Data Model

The project uses synthetic retail and e-commerce data. The data model includes a sales fact table and customer, date, product, and region dimensions.

The original dataset documentation recorded these initial counts:

| Dataset | Initial record count |
|---|---:|
| Fact Sales | 120,000 |
| Dim Customer | 1,500 |
| Dim Date | 731 |
| Dim Product | 75 |
| Dim Region | 8 |

The original historical sales period ran from January 1, 2024, through December 31, 2025. The incremental generator is designed to extend the sales fact table and date dimension when activated. Local working data can therefore contain different row counts from the original dataset. Treat the figures above as documented initial counts, not a guarantee of the current local or committed row counts.

The analytics workflow covers revenue, cost, profit, profit margin, orders, customers, average order value, product and regional performance, channel and payment-method performance, customer purchase frequency and RFM summaries, forecast accuracy and bias, daily anomalies, scenario outcomes, demand trends, and product/regional priorities.

## AI Analytics MVP

The AI Analytics MVP converts structured analytics outputs into executive-readable findings, risk alerts, and business recommendations.

**Implementation approach:** The current module uses Python and predefined rules. It does not require a generative AI API.

### Input files

The module expects the following CSV inputs in its configured analytics output directory, documented as `data/outputs/`:

- `business_kpi_summary.csv`
- `daily_sales_anomalies.csv`
- `forecast_model_comparison.csv`
- `customer_rfm_summary.csv`
- `sales_scenario_results.csv`
- `demand_planning_recommendations.csv`

### Generated outputs

| File | Purpose |
|---|---|
| `ai_executive_summary.md` | Executive-readable summary of analytical findings |
| `ai_risk_alerts.csv` | Structured risk alerts and supporting metrics |
| `ai_business_recommendations.csv` | Recommended actions and supporting evidence |

The documented rules include KPI declines, revenue anomalies, forecast-model selection, customer revenue concentration, downside-scenario profit risk, and demand-planning recommendations.

The risk-alert CSV schema is:

`severity, category, date, message, metric_value`

The business-recommendation CSV schema is:

`priority, category, finding, recommended_action, evidence`

The module depends on the quality and availability of upstream analytics outputs. Recommendations should be reviewed against the underlying data and business context before use.

**Previously reported local test result:** 13 AI Analytics MVP tests passed with zero failures and zero errors. This is a historical development result, not a claim that the current working tree or public repository has been freshly tested. Re-run the tests after changes.

## Incremental Synthetic Data Generation

The incremental generator is designed to extend the dataset while protecting source-data integrity.

The documented workflow is to determine the next simulated sales date, apply the configured simulated-date schedule and date cutoff, generate approximately 40–50 sales records per simulated day, validate generated financial values and data relationships, update the sales fact table and date dimension, persist generator state and integrity metadata, and use recovery mechanisms to protect against failed writes.

The documented safeguards include SHA-256 source-integrity checks, state tracking, a pending-operation journal, backups, and recovery mechanisms. The original recovery and integrity test suite was documented as containing 13 tests. An isolated end-to-end test was also reported to have exercised incremental generation, data validation, the analytics pipeline, and output validation without modifying production data. Re-run the relevant tests to verify the current state.

### Important operational note

The GitHub Actions workflow currently invokes the generator with `--apply`. This differs from a local preview-only run: the workflow can apply incremental changes and subsequently commit selected data and state files to `main`. Review the generator's current source code, integrity checks, recovery behavior, workflow permissions, and repository state before changing or manually triggering this process. Do not bypass safety checks to force a successful run.

## Analytics Pipeline and Output Validation

Run the configured analytics pipeline:

```powershell
python src/run_analytics_pipeline.py
```

The configured pipeline has included forecast-model comparison, anomaly detection, customer RFM segmentation, scenario analysis, business insights, and output validation. Consult the current source code and terminal output for the exact stages executed by the current version.

Demand-planning analysis, chart generation, and output validation can be run separately:

```powershell
python src/demand_planning_analysis.py
python src/forecast_visualizations.py
python src/validate_analytics_outputs.py
```

The structured source-data validator can be run with:

```powershell
python src/data_validation.py
```

A historical Phase 5 development run reported **76 output-validation checks passed and 0 failed**. A later development run was reported as **89 checks passed and 0 failures**. These are historical results; validation counts and outcomes may change with code, data, or configuration. Re-run validation after changes and use the current terminal output as the source of truth.

Generated analytics outputs are stored under `data/outputs/` and may be excluded from Git tracking. Generated visualization PNG files are stored under `dashboard/figures/`.

## GitHub Actions Automation

The repository includes `.github/workflows/daily_pipeline.yml`.

The currently inspected workflow configuration:

1. Checks out the repository.
2. Sets up Python 3.12 on an Ubuntu 24.04 runner.
3. Installs the configured analytics dependencies.
4. Validates source data.
5. Runs incremental synthetic-data generation with `--apply`.
6. Validates the updated source data.
7. Runs the analytics pipeline.
8. Uploads `data/outputs/` as the `bi-analytics-outputs` artifact with a 14-day retention period.
9. Commits changed `data/raw/fact_sales.csv`, `data/raw/dim_date.csv`, and `data/raw/incremental_generator_state.json` to `main` when staged changes exist.

The workflow supports manual execution and is configured with the cron expression `17 1 * * *` and timezone `Asia/Dhaka` (01:17 Bangladesh time daily). Actual run success and artifact availability should be confirmed in the [GitHub Actions history](https://github.com/sakib075009/automated-bi-sales-forecasting/actions).

The workflow has `contents: write` permission and uses the GitHub Actions bot identity to push selected changed files. It does not, based on the inspected workflow file, publish refreshed analytics directly to the GitHub Pages portfolio website. Confirm the workflow configuration after future changes.

## Technology Stack

| Area | Technologies |
|---|---|
| Programming | Python |
| Data processing | pandas, NumPy |
| Analytics and validation | Python analytical modules |
| Forecasting | Moving-average, previous-month naive, and seasonal-naive baselines |
| Business Intelligence | Microsoft Power BI, DAX |
| AI Analytics MVP | Python and deterministic business rules |
| Testing | Python `unittest` |
| Version control | Git, GitHub |
| Automation | GitHub Actions |
| Portfolio hosting | GitHub Pages |
| Data storage | CSV inputs and outputs |

See `requirements.txt` for the project's Python dependencies.

## Repository Structure

This is a representative structure; additional source modules, tests, backups, generated files, and documentation may exist.

```text
automated-bi-sales-forecasting/
├── .github/
│   └── workflows/
│       └── daily_pipeline.yml
├── dashboard/
│   └── figures/
├── data/
│   ├── raw/
│   ├── processed/
│   └── outputs/
├── notebooks/
├── powerbi/
├── src/
│   ├── ai_analytics_mvp.py
│   ├── data_validation.py
│   ├── demand_planning_analysis.py
│   ├── forecast_model_comparison.py
│   ├── forecast_visualizations.py
│   ├── incremental_data_generator.py
│   ├── run_analytics_pipeline.py
│   └── validate_analytics_outputs.py
├── tests/
│   ├── test_ai_analytics_mvp.py
│   └── test_incremental_recovery.py
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12 is used by the inspected GitHub Actions workflow.
- Git.
- Microsoft Power BI Desktop to explore `.pbix` reports.
- PowerShell on Windows or another compatible terminal.

### 1. Clone the repository

```powershell
git clone https://github.com/sakib075009/automated-bi-sales-forecasting.git
cd automated-bi-sales-forecasting
```

### 2. Create and activate a virtual environment

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Validate the source dataset

```powershell
python src/data_validation.py
```

Investigate reported validation failures before using the data downstream.

### 5. Run the analytics pipeline

```powershell
python src/run_analytics_pipeline.py
```

Review the terminal output and confirm that the configured stages complete successfully.

### 6. Validate analytics outputs

```powershell
python src/validate_analytics_outputs.py
```

Investigate reported failures before relying on generated results.

### 7. Run the AI Analytics MVP tests

```powershell
python -m unittest tests.test_ai_analytics_mvp -v
```

### 8. Run incremental recovery tests

```powershell
python -m unittest tests.test_incremental_recovery -v
```

### 9. Run the complete test suite

```powershell
python -m unittest discover -s tests -v
```

Use the current terminal output as the source of truth for the test count and result.

### 10. Run demand planning and generate charts

```powershell
python src/demand_planning_analysis.py
python src/forecast_visualizations.py
```

### 11. Preview incremental generation

Check the current generator source code for its supported arguments and preview command before running it. Review the proposed changes, integrity checks, backups, and recovery behavior. Do not use `--apply` on important data unless you have reviewed the implications and intentionally want to apply changes.

### 12. Explore the Power BI report

Browse the [`powerbi/` directory](https://github.com/sakib075009/automated-bi-sales-forecasting/tree/main/powerbi), open the intended `.pbix` file in Power BI Desktop, and update local data-source paths if necessary.

## Testing and Verification

The project uses Python's built-in `unittest` framework. Tests have covered incremental-generator recovery and integrity behavior, demand planning, and AI Analytics MVP behavior. The exact modules and coverage can change as the project evolves.

The AI Analytics MVP test module has been documented as covering KPI decline and recovery, forecast selection, invalid numeric values, empty inputs, recommendation evidence, anomaly and demand-planning recommendations, and output schemas and counts.

Always rerun relevant tests and validation after source-code, data, or configuration changes. Historical test and validation results in this README are not substitutes for a fresh run.

## Current Implementation Status

### Implemented components

- Synthetic sales data and data validation.
- Analytics pipeline and output validation.
- Forecasting and model comparison.
- Customer analytics and RFM summaries.
- Anomaly detection.
- Demand-planning analysis.
- Scenario analysis.
- Power BI reporting.
- Incremental data generation with integrity and recovery safeguards.
- GitHub Actions workflow configuration, including automated data updates.
- GitHub Pages portfolio website.
- AI Analytics MVP and its local unit tests.

### Ongoing verification

- Confirm successful scheduled workflow runs and artifact availability.
- Review incremental-generation safeguards and recovery behavior.
- Verify the current AI Analytics MVP files and tests in the public repository.
- Run the full test suite after integration changes.
- Validate generated outputs after new data is introduced.
- Review forecast evaluation methodology and assumptions.
- Confirm documented commands match the current script interfaces.
- Confirm Power BI report contents and data-source settings against the intended version.

## Future Development

Potential enhancements include:

- Forecast backtesting and model monitoring.
- Additional customer retention and lifetime-value analysis.
- Demand planning using stock, supplier, and replenishment data.
- More comprehensive scenario modeling.
- Expanded data-quality and regression tests.
- Improved business explanations and decision-support outputs.
- Monitoring of automated data updates and workflow failures.
- Automated report refresh or publishing, if explicitly implemented and tested.

Future enhancements should be evaluated against reproducibility, maintainability, data quality, and operating cost.

## Portfolio and Screenshots

- [Open the live portfolio](https://sakib075009.github.io/automated-bi-sales-forecasting/)
- [Explore the dashboard gallery](https://sakib075009.github.io/automated-bi-sales-forecasting/#dashboard)
- [Browse the source repository](https://github.com/sakib075009/automated-bi-sales-forecasting)
- [Inspect workflow runs and artifacts](https://github.com/sakib075009/automated-bi-sales-forecasting/actions)

## Author and Repository

**Project:** Automated Business Intelligence & Sales Forecasting Platform

**GitHub:** [sakib075009/automated-bi-sales-forecasting](https://github.com/sakib075009/automated-bi-sales-forecasting)

**Portfolio website:** [Automated BI — Sales Forecasting Platform](https://sakib075009.github.io/automated-bi-sales-forecasting/)

This project demonstrates practical skills in Business Intelligence, Python analytics, forecasting, data validation, customer analytics, automated testing, workflow automation, and portfolio deployment.

---

*This is a portfolio and learning project using synthetic data. Forecasts, alerts, and recommendations should be validated before being used for real operational or financial decisions.*
