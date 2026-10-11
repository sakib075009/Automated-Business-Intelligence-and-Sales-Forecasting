# Automated Business Intelligence & Sales Forecasting Platform

An end-to-end Business Intelligence and sales forecasting portfolio project combining Python data validation, sales analytics, forecasting, automated business insights, incremental synthetic data generation, Power BI dashboards, and GitHub Actions.

**Live portfolio website:** https://sakib075009.github.io/automated-bi-sales-forecasting/  
**GitHub repository:** https://github.com/sakib075009/automated-bi-sales-forecasting

## Project Overview

This project demonstrates how a reproducible analytics pipeline can transform synthetic retail/e-commerce transaction data into business KPIs, forecasts, customer segments, anomaly reports, scenario comparisons, and actionable insights.

The long-term objective is to support incremental synthetic data generation, automated validation, analytics refreshes, and scheduled execution.

**Current status:** The core analytics pipeline, forecasting and model comparison, anomaly detection, RFM segmentation, scenario analysis, business insights, eight-page Power BI dashboard, incremental generator, automated tests, GitHub Actions workflow, and GitHub Pages website are implemented. Production activation of incremental data generation and automatic website publishing remain separate tasks.

## Key Features

### Data Engineering and Validation

- Synthetic retail/e-commerce transaction dataset.
- Data validation for required columns, missing values, duplicate keys, foreign-key relationships, and business rules.
- Validation of transaction dates, quantities, discounts, revenue, costs, and profit.
- Incremental data generator with configurable scheduling.
- Source-integrity checks using SHA-256 hashes.
- State persistence, recovery journaling, backups, and rollback mechanisms.
- Automated tests for scheduling, financial calculations, state persistence, source integrity, and recovery behavior.

### Business Intelligence and Analytics

- Monthly revenue, cost, profit, order, and customer analysis.
- Product, regional, channel, and payment-method performance.
- Customer purchase-frequency and RFM segmentation.
- Business KPI summaries and rule-based business insights.
- Daily sales anomaly detection.
- Sales scenario analysis.
- Automated analytics-output validation.

### Revenue Forecasting

- Seasonal-naive baseline forecasting.
- Forecast model comparison and prediction outputs.
- Forecast evaluation using Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Mean Absolute Percentage Error (MAPE).
- Historical holdout evaluation.
- Forecast outputs designed for business decision support.

The seasonal-naive baseline uses the corresponding month from the previous year as its forecast. More advanced models are evaluated separately through the model-comparison pipeline.

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

The Decision Support page includes Python-generated forecasting outputs and evaluation metrics.

## Dataset

The project uses **synthetic data** for demonstration and portfolio purposes. It does not represent actual business transactions.

| Dataset | Initial record count |
|---|---:|
| Fact Sales | 120,000 |
| Dim Customer | 1,500 |
| Dim Date | 731 |
| Dim Product | 75 |
| Dim Region | 8 |

The original historical sales period runs from January 1, 2024, through December 31, 2025. The incremental generator is designed to extend the sales fact table and date dimension when explicitly activated.

The data follows a dimensional model with a sales fact table and customer, date, product, and region dimensions.

### Business Metrics

The analytics pipeline calculates metrics including:

- Total revenue, cost, and profit
- Profit margin
- Total orders and customers
- Average order value
- Product and regional revenue
- Sales-channel and payment-method performance
- Customer purchase frequency and RFM segments
- Forecast accuracy
- Daily sales anomalies
- Scenario-based business outcomes

## Forecasting Methodology

The project includes a seasonal-naive baseline and a separate model-comparison pipeline.

For the seasonal-naive baseline, each forecast month uses actual revenue from the corresponding month of the previous year. For example, January 2026 uses January 2025 revenue.

The historical baseline evaluation uses the 12 months of 2025 as the test period, with corresponding months of 2024 as forecasts.

### Historical Baseline Results

| Metric | Result |
|---|---:|
| MAE | Approximately 40.87 million |
| RMSE | Approximately 41.05 million |
| MAPE | 22.51% |

These results describe the original seasonal-naive holdout evaluation. They should not be confused with metrics from other models or evaluation windows. Historical accuracy does not guarantee future performance.

## Incremental Data Generation

The incremental generator is designed to extend the historical dataset while protecting source-data integrity.

Its intended workflow is:

1. Determine the next simulated sales date.
2. Apply the configured simulated-date schedule and 90-day cutoff.
3. Generate approximately 40–50 sales records per simulated day.
4. Validate generated financial values and data relationships.
5. Update the sales fact table and date dimension.
6. Persist generator state and integrity metadata.
7. Use recovery mechanisms to protect against failed writes.

### Integrity and Recovery

The generator uses SHA-256 source-integrity checks, state tracking, a pending-operation journal, and recovery mechanisms. Its automated test suite covers scheduling, financial calculations, state persistence, modified-source detection, and recovery behavior.

The current automated test suite contains 13 recovery and integrity tests. An isolated end-to-end test has also successfully exercised incremental generation, data validation, the complete analytics pipeline, and output validation without modifying production data.

**Important:** Production incremental generation has not been activated. The generator defaults to preview mode; review the configuration and recovery procedures before using `--apply` on production data.

## GitHub Actions Automation

The repository includes a GitHub Actions workflow at `.github/workflows/daily_pipeline.yml`.

The workflow:

1. Checks out the repository.
2. Sets up Python 3.12.
3. Installs analytics dependencies.
4. Validates the committed source dataset.
5. Runs the complete analytics pipeline.
6. Uploads generated analytics outputs as a downloadable workflow artifact.

The workflow supports manual execution and scheduled execution at 03:00 UTC (09:00 Bangladesh time).

Generated outputs are uploaded as artifacts with a 14-day retention period. The workflow currently processes the committed source dataset; it does not automatically run the incremental generator or publish updated analytics to the portfolio website.

## Technology Stack

- **Programming:** Python
- **Data processing:** Pandas, NumPy
- **Analytics:** Python
- **Forecasting:** Seasonal-naive baseline and model comparison
- **Business Intelligence:** Microsoft Power BI, DAX
- **Testing:** Python `unittest`
- **Version control:** Git, GitHub
- **Automation:** GitHub Actions
- **Portfolio deployment:** GitHub Pages

## Project Structure

```text
project-01/
├── .github/
│   └── workflows/
├── data/
│   ├── raw/
│   ├── processed/
│   └── outputs/
├── notebooks/
├── powerbi/
├── src/
│   ├── data_validation.py
│   ├── incremental_data_generator.py
│   ├── forecast_model_comparison.py
│   ├── sales_anomaly_detection.py
│   ├── customer_rfm_segmentation.py
│   ├── sales_scenario_analysis.py
│   ├── business_insights_engine.py
│   ├── validate_analytics_outputs.py
│   └── run_analytics_pipeline.py
├── tests/
│   └── test_incremental_recovery.py
├── .gitignore
├── README.md
└── requirements.txt
```

The pipeline generates forecast comparisons and predictions, anomaly reports, RFM segments and summaries, scenario results, KPI summaries, and business insights. These outputs are reproducible and are excluded from Git tracking; successful GitHub Actions runs upload them as workflow artifacts.

## Getting Started

### Prerequisites

- Python 3.12 recommended for the automation workflow
- Git
- Microsoft Power BI Desktop to explore the dashboard

### 1. Clone the Repository

```powershell
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

### 5. Run the Complete Analytics Pipeline

```powershell
python src/run_analytics_pipeline.py
```

The pipeline runs the configured analytics steps and validates their outputs.

### 6. Run the Incremental Generator Tests

```powershell
python -m unittest tests.test_incremental_recovery -v
```

### 7. Preview the Incremental Generator

```powershell
python src/incremental_data_generator.py --today 2026-10-11
```

Preview mode does not activate production writes. Do not use `--apply` until production paths, backups, source integrity, and recovery behavior have been reviewed.

### 8. Explore the Power BI Report

Open the tracked `.pbix` report in the `powerbi/` directory. Update data-source paths if necessary, then refresh the report in Power BI Desktop.

## Current Implementation Status

### Implemented

- Synthetic historical sales dataset and dimensional data model
- Source-data validation
- Complete analytics pipeline and output validation
- Forecasting and model comparison
- Sales anomaly detection
- Customer RFM segmentation
- Sales scenario analysis
- Business KPI and insight generation
- Eight-page Power BI dashboard
- Incremental generator with integrity and recovery safeguards
- Automated generator tests
- GitHub Actions workflow with artifact upload
- GitHub Pages portfolio website

### Remaining Work

- Complete production-readiness review of incremental generation.
- Decide when and how to activate incremental generation safely.
- Validate the intended long-term scheduled workflow with an appropriate production-data strategy.
- Decide whether and how refreshed analytics should be published to the website.
- Complete final documentation, testing, and portfolio review.

## Future Development

Potential enhancements include:

- More advanced forecasting and model evaluation
- Inventory and demand planning
- Automated report publishing
- Expanded business decision-support capabilities
- An AI-assisted business analytics interface

New features will be added after the existing pipeline and automation are fully reviewed.

## Screenshots

The portfolio website presents the project and its dashboard screenshots:

**Website:** https://sakib075009.github.io/automated-bi-sales-forecasting/

## Author and Repository

**GitHub repository:** https://github.com/sakib075009/automated-bi-sales-forecasting

This project demonstrates practical skills in Business Intelligence, Python analytics, forecasting, data validation, automated testing, workflow automation, and portfolio deployment.
