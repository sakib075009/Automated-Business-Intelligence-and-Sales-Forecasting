# Automated Business Intelligence & Sales Forecasting Platform

An end-to-end Business Intelligence and sales forecasting portfolio project combining Python data validation, sales analytics, baseline forecasting, automated business insights, and interactive Power BI dashboards.

The long-term goal is to develop a reproducible analytics pipeline that can generate incremental synthetic sales data, validate it, refresh analytics outputs, and run on a scheduled GitHub Actions workflow.

## Project Overview

Businesses need to understand sales performance, identify profitable products and customer segments, monitor regional performance, and anticipate future revenue.

This project demonstrates how a Python analytics pipeline and a Power BI dashboard can turn synthetic retail/e-commerce transaction data into actionable business insights.

**Current status:** Core analytics, forecasting, the eight-page Power BI dashboard, and the initial incremental data generator are implemented. Generator scheduling and recovery tests pass. Production activation, scheduled GitHub Actions execution, and public portfolio deployment remain to be completed.

## Key Features

### Data Engineering and Validation

- Structured synthetic retail/e-commerce transaction data.
- Data quality checks for required columns, missing values, duplicate keys, invalid foreign keys, and business rules.
- Validation of transaction dates, customer signup dates, quantities, discounts, revenue, costs, and profit calculations.
- CSV-based data processing.
- Incremental sales generation with configurable simulated-date scheduling.
- Recovery and rollback mechanisms designed to protect source data during failed writes.
- Automated tests for scheduling, generated financial values, state persistence, and recovery behavior.

### Business Intelligence and Analytics

- Monthly revenue, cost, profit, order, and customer summaries.
- Product and regional performance analysis.
- Sales channel and payment analysis.
- Customer-level revenue and purchase-frequency analytics.
- Business KPI generation.
- Rule-based automated business insights.
- Profitability and negative-profit transaction analysis.

### Revenue Forecasting

- Seasonal-naive baseline forecasting.
- Six-month revenue forecast for January–June 2026.
- Historical holdout evaluation using 2024 as the reference year and 2025 as the test year.
- Forecast evaluation using Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Mean Absolute Percentage Error (MAPE).

### Interactive Power BI Dashboard

The report contains eight pages:

1. Executive Overview
2. Sales & Revenue Analysis
3. Customer Analytics
4. Product & Pareto Analysis
5. Regional Performance
6. Channel & Payment Analysis
7. Promotion & Discount Analysis
8. Decision Support

The Decision Support page includes the Python-generated revenue forecast and forecast evaluation metrics.

## Dataset

The project uses synthetic data for demonstration and portfolio purposes. It does not represent actual business transactions.

| Dataset | Records |
|---|---:|
| Fact Sales | 120,000 |
| Dim Customer | 1,500 |
| Dim Date | 731 |
| Dim Product | 75 |
| Dim Region | 8 |

The historical sales period runs from January 1, 2024, through December 31, 2025.

The data follows a dimensional model with a sales fact table and customer, date, product, and region dimensions.

### Business Metrics

The analytics pipeline calculates metrics including:

- Total revenue, cost, and profit
- Profit margin
- Total orders and customers
- Average order value
- Revenue by product, region, and sales channel
- Customer-level revenue and purchase frequency
- Forecast accuracy metrics

## Forecasting Methodology

The initial forecasting model uses a seasonal-naive baseline. Each forecast month uses the actual revenue from the corresponding month in the previous year.

For example, January 2026 uses January 2025 revenue as its forecast.

The baseline is evaluated on the 12 months of 2025, using the corresponding months of 2024 as forecasts.

### Historical Holdout Results

| Metric | Result |
|---|---:|
| MAE | Approximately 40.87 million |
| RMSE | Approximately 41.05 million |
| MAPE | 22.51% |

These results describe historical holdout performance and do not guarantee the same accuracy for future months. The baseline provides a benchmark for evaluating more advanced forecasting approaches.

## Incremental Data Generation

The incremental generator is designed to extend the historical sales dataset while preserving data integrity.

Its intended workflow is:

1. Determine the next simulated sales date.
2. Apply the configured batch schedule and 90-day cutoff.
3. Generate approximately 40–50 sales records per simulated day.
4. Validate generated financial values and relationships.
5. Update the sales fact table and date dimension.
6. Save generator state and maintain recovery information.
7. Restore original files if a write or integrity check fails.

### Scheduling Design

- The historical dataset ends on December 31, 2025.
- During the remainder of 2026, the planned batch pattern is 3, 3, 3, and 4 simulated days per run.
- Beginning January 1, 2027, the planned batch size becomes one simulated day per run.
- The generator is designed to maintain at least a 90-day gap between the real run date and the latest simulated sales date.

The schedule and recovery logic have passed the current automated test suite. Production activation and end-to-end scheduled execution still require validation.

## Technology Stack

- **Language:** Python
- **Data processing:** Pandas and NumPy
- **Analytics and validation:** Python
- **Forecasting:** Seasonal-naive baseline
- **Visualization and BI:** Microsoft Power BI and DAX
- **Testing:** Python `unittest`
- **Version control:** Git and GitHub
- **Planned scheduling:** GitHub Actions
- **Planned portfolio deployment:** GitHub Pages

## Project Structure

```text
project-01/
├── .github/
│   └── workflows/
├── data/
│   ├── raw/
│   ├── processed/
│   ├── outputs/
│   └── backups/
├── notebooks/
├── powerbi/
├── src/
│   ├── analytics_engine.py
│   ├── audit_sales_data.py
│   ├── data_validation.py
│   └── incremental_data_generator.py
├── tests/
│   └── test_incremental_recovery.py
├── .gitignore
├── README.md
└── requirements.txt
```

The source code generates analytics outputs for monthly performance, products, regions, channels, customers, KPIs, business insights, and forecasting. Exact output files depend on the pipeline implementation.

## Getting Started

### Prerequisites

- Python
- Git
- Microsoft Power BI Desktop to explore the dashboard

### 1. Clone the Repository

```bash
git clone https://github.com/sakib075009/automated-bi-sales-forecasting.git
cd automated-bi-sales-forecasting
```

### 2. Create and Activate a Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```powershell
python -m pip install -r requirements.txt
```

### 4. Validate the Dataset

```powershell
python src/data_validation.py
```

### 5. Run the Analytics and Forecasting Pipeline

```powershell
python src/analytics_engine.py
```

The pipeline generates analytics summaries, business KPIs, automated insights, forecast inputs, revenue forecasts, and evaluation metrics in the configured output directory.

### 6. Run the Automated Tests

```powershell
python -m unittest tests.test_incremental_recovery -v
```

The tests cover incremental scheduling, financial calculations, state persistence, and recovery behavior.

### 7. Preview the Incremental Generator

The generator defaults to preview mode. To preview a planned batch using a specified date:

```powershell
python src/incremental_data_generator.py --today 2026-10-10
```

Use the project's current configuration and review the preview before any production write. Do not use the `--apply` option until production paths, backups, recovery behavior, and validation have been reviewed.

### 8. Explore the Power BI Report

Open the appropriate `.pbix` file in the `powerbi/` directory. If necessary, update the data-source paths to match your local project directory, then refresh the report.

## Current Implementation Status

### Implemented

- Synthetic historical dataset and data preparation
- Data validation and analytics pipeline
- Business KPI and insight generation
- Seasonal-naive revenue forecasting and evaluation
- Eight-page Power BI dashboard
- Python-generated forecast outputs
- Incremental generator scheduling and recovery logic
- Automated tests for the generator
- GitHub repository and version control

### Remaining Work

- Complete production-readiness checks for incremental generation
- Validate the full update and downstream analytics workflow
- Complete README screenshots and final documentation review
- Configure and test scheduled execution with GitHub Actions
- Define how updated analytics outputs will be published
- Build and deploy the GitHub Pages portfolio project page
- Add advanced forecasting and model comparison

## Future Development

Potential enhancements include:

- Comparing baseline forecasts with statistical and machine-learning models
- Sales anomaly detection
- Customer retention and RFM analytics
- Inventory and demand planning
- Scenario analysis
- Automated report publishing
- An AI-assisted business analytics interface

These features will be documented as they are implemented and tested.

## Screenshots

Add screenshots of the Power BI dashboard and relevant analytics outputs here.

Suggested screenshots:

- Executive Overview
- Product and Pareto Analysis
- Regional Performance
- Decision Support and Forecasting

## Author and Repository

**GitHub repository:** https://github.com/sakib075009/automated-bi-sales-forecasting

This project is a practical portfolio demonstration of Business Intelligence, data analytics, forecasting, data quality validation, and workflow automation.