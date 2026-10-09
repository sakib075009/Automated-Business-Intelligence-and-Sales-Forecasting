# Automated Business Intelligence & Sales Forecasting Platform

An end-to-end Business Intelligence and sales forecasting portfolio project combining Python analytics, data validation, baseline forecasting, and interactive Power BI dashboards.

## Project Overview

Businesses need to understand sales performance, identify profitable products and customer segments, monitor regional performance, and anticipate future revenue.

This project demonstrates how a reproducible Python analytics pipeline and a Power BI dashboard can turn synthetic retail/e-commerce transaction data into actionable business insights.

The V1 implementation includes data quality validation, business KPI generation, customer/product/regional analytics, automated insight generation, and a six-month revenue forecast.

**Project status:** V1 analytics and forecasting implemented; scheduled automation and public website deployment are planned next.

## Key Features

### Data Engineering and Validation
- Structured synthetic retail/e-commerce dataset.
- Data quality checks for required columns, missing values, duplicate primary keys, and invalid foreign keys.
- Business rule validation for transaction dates, customer signup dates, quantities, costs, revenue, discounts, and profit calculations.
- Reproducible CSV-based processing pipeline.

### Business Intelligence and Analytics
- Monthly revenue, cost, profit, order, and customer summaries.
- Product and regional performance analysis.
- Sales channel and customer-level analytics.
- Business KPI generation.
- Rule-based automated business insights.
- Profitability and negative-profit transaction analysis.

### Revenue Forecasting
- Seasonal-naive baseline forecasting.
- Six-month revenue forecast for January–June 2026.
- Historical holdout evaluation using 2024 as the reference year and 2025 as the test year.
- Forecast evaluation metrics: Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and Mean Absolute Percentage Error (MAPE).

### Interactive Power BI Dashboard

The report contains eight dashboard pages:

1. Executive Overview
2. Sales & Revenue Analysis
3. Customer Analytics
4. Product & Pareto Analysis
5. Regional Performance
6. Channel & Payment Analysis
7. Promotion & Discount Analysis
8. Decision Support

The Decision Support page also includes the Python-generated revenue forecast and forecast evaluation metrics.

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

The dataset follows a dimensional model with a sales fact table and customer, date, product, and region dimensions.

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

V1 uses a seasonal-naive baseline. Each forecast month uses the actual revenue from the corresponding month in the previous year.

For example, January 2026 uses January 2025 revenue as its forecast.

The baseline is evaluated on the 12 months of 2025, using the corresponding months of 2024 as forecasts.

**Baseline evaluation results:**

| Metric | Result |
|---|---:|
| MAE | Approximately 40.87 million |
| RMSE | Approximately 41.05 million |
| MAPE | 22.51% |

These results describe historical holdout performance. They do not guarantee the same level of accuracy for future months. The baseline provides a benchmark for evaluating more advanced forecasting approaches in later versions.

## Technology Stack

- **Language:** Python
- **Data processing:** Pandas, NumPy
- **Analytics and validation:** Python
- **Forecasting:** Seasonal-naive baseline
- **Visualization and BI:** Microsoft Power BI, DAX
- **Version control:** Git and GitHub
- **Planned automation:** GitHub Actions
- **Planned deployment:** GitHub Pages

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
│   ├── analytics_engine.py
│   └── data_validation.py
├── tests/
├── .gitignore
├── README.md
└── requirements.txt
```

The `data/outputs/` directory contains generated CSV files for monthly, product, regional, channel, customer, KPI, insight, and forecasting results.

## Getting Started

### Prerequisites

- Python installed on your system
- Git
- Microsoft Power BI Desktop to explore the dashboard

### 1. Clone the Repository

```bash
git clone https://github.com/sakib075009/automated-bi-sales-forecasting.git
cd automated-bi-sales-forecasting
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it in Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Validate the Dataset

```bash
python src/data_validation.py
```

The validation script checks dataset structure, key integrity, missing values, relationships, and business rules.

### 5. Run the Analytics and Forecasting Pipeline

```bash
python src/analytics_engine.py
```

The pipeline generates analytics summaries, business KPIs, automated insights, forecast inputs, future revenue forecasts, and forecast evaluation metrics in `data/outputs/`.

### 6. Explore the Power BI Report

Open the Power BI report in the `powerbi/` directory. If necessary, update the data-source paths to match your local project directory, then refresh the report.

## Current Implementation Status

### Completed
- Synthetic dataset generation and data preparation
- Data pipeline validation
- Python analytics engine
- Business KPI and insight generation
- Seasonal-naive revenue forecasting
- MAE, RMSE, and MAPE evaluation
- Eight-page Power BI dashboard
- Power BI integration with forecast outputs
- GitHub version control and repository update

### Planned
- Scheduled Python pipeline execution with GitHub Actions
- Automated daily synthetic transaction generation
- Automated regeneration and publication of analytics outputs
- GitHub Pages portfolio deployment
- Advanced forecasting and model comparison
- Anomaly detection and additional decision-support capabilities

## Future Development

The project is intended to evolve into a more comprehensive analytics platform.

Potential future enhancements include:

- Comparing seasonal-naive forecasts with statistical and machine-learning models
- Sales anomaly detection
- Customer retention and RFM analytics
- Inventory and demand planning
- Scenario analysis
- Automated report publishing
- An AI-assisted business analytics interface

These enhancements will be implemented and documented as they become available.

## Author and Repository

**GitHub:** https://github.com/sakib075009/automated-bi-sales-forecasting

This project is developed as a practical portfolio demonstration of Business Intelligence, data analytics, forecasting, data quality validation, and workflow automation.