import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs"


def read_csv(filename, input_dir=OUTPUT_DIR):
    path = Path(input_dir) / filename
    if not path.exists():
        raise FileNotFoundError(f"Required analytics output not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def number(value, default=None):
    try:
        result = float(value)
        return result if result == result and abs(result) != float("inf") else default
    except (TypeError, ValueError):
        return default


def generate_insights(input_dir=OUTPUT_DIR, output_dir=OUTPUT_DIR):
    """Create transparent, rule-based business insights from existing outputs."""
    output_dir = Path(output_dir)

    kpis = read_csv("business_kpi_summary.csv", input_dir)
    anomalies = read_csv("daily_sales_anomalies.csv", input_dir)
    forecasts = read_csv("forecast_model_comparison.csv", input_dir)
    segments = read_csv("customer_rfm_summary.csv", input_dir)
    scenarios = read_csv("sales_scenario_results.csv", input_dir)
    demand = read_csv("demand_planning_recommendations.csv", input_dir)

    alerts = []
    recommendations = []
    findings = []

    # 1. Monthly KPI movements
    for row in kpis:
        metric = row.get("Metric", "Unknown metric")
        current = number(row.get("Current_Value"))
        change = number(row.get("Change_Pct"))

        if current is None or change is None:
            continue

        findings.append(
            f"- **{metric}:** current value {current:,.2f}; "
            f"change {change:+.2f}% versus the previous month."
        )

        if change <= -5:
            alerts.append({
                "severity": "High" if change <= -10 else "Medium",
                "category": "KPI movement",
                "date": row.get("Current_Month", ""),
                "message": f"{metric} declined by {abs(change):.2f}% versus the previous month.",
                "metric_value": f"{current:.2f}",
            })
            recommendations.append({
                "priority": "High" if change <= -10 else "Review",
                "category": "KPI movement",
                "finding": f"{metric} declined by {abs(change):.2f}%.",
                "recommended_action": "Investigate the underlying product, regional, pricing, and volume drivers before deciding on corrective action.",
                "evidence": f"Current value={current:.2f}; change={change:.2f}%",
            })

    # 2. Sales anomalies
    scored_anomalies = [
        row for row in anomalies
        if row.get("anomaly_type") in ("High Revenue", "Low Revenue")
    ]
    scored_anomalies.sort(key=lambda row: row.get("date", ""), reverse=True)

    recent_anomalies = scored_anomalies[:10]
    for row in recent_anomalies:
        anomaly_type = row.get("anomaly_type", "Unknown")
        revenue = number(row.get("daily_revenue"))
        z_score = number(row.get("robust_z_score"))

        alerts.append({
            "severity": "High" if z_score is not None and abs(z_score) >= 5 else "Medium",
            "category": "Sales anomaly",
            "date": row.get("date", ""),
            "message": f"{anomaly_type} detected; investigate the day's sales drivers.",
            "metric_value": "" if revenue is None else f"{revenue:.2f}",
        })

    if scored_anomalies:
        recommendations.append({
            "priority": "Review",
            "category": "Sales anomalies",
            "finding": f"{len(scored_anomalies)} historical days were classified as high- or low-revenue anomalies.",
            "recommended_action": "Review the most recent flagged dates against promotions, stock availability, order volume, and data quality.",
            "evidence": "daily_sales_anomalies.csv; latest flagged dates listed in the risk alerts output",
        })

    # 3. Forecast model performance
    valid_forecasts = [
        row for row in forecasts
        if number(row.get("MAPE")) is not None
    ]
    if valid_forecasts:
        best = min(valid_forecasts, key=lambda row: number(row.get("MAPE")))
        findings.append(
            f"- **Best forecast model by MAPE:** {best.get('model')} "
            f"({number(best.get('MAPE')):.2f}% MAPE)."
        )
        recommendations.append({
            "priority": "Review",
            "category": "Forecasting",
            "finding": f"{best.get('model')} has the lowest MAPE among the compared models.",
            "recommended_action": "Use it as the leading candidate, while monitoring future forecast errors and comparing alternatives periodically.",
            "evidence": f"MAPE={number(best.get('MAPE')):.2f}%; source=forecast_model_comparison.csv",
        })

    # 4. Customer concentration
    valid_segments = [
        row for row in segments
        if number(row.get("Revenue_Contribution_Percentage")) is not None
    ]
    if valid_segments:
        top_segment = max(
            valid_segments,
            key=lambda row: number(row.get("Revenue_Contribution_Percentage")),
        )
        contribution = number(top_segment.get("Revenue_Contribution_Percentage"))
        findings.append(
            f"- **Largest customer-segment revenue contribution:** "
            f"{top_segment.get('Customer_Segment')} ({contribution:.2f}%)."
        )
        recommendations.append({
            "priority": "Review",
            "category": "Customer concentration",
            "finding": f"{top_segment.get('Customer_Segment')} contributes {contribution:.2f}% of revenue.",
            "recommended_action": "Track retention and repeat purchasing for this segment while developing other valuable customer groups.",
            "evidence": f"customer_rfm_summary.csv; contribution={contribution:.2f}%",
        })

    # 5. Downside scenario
    baseline = next(
        (row for row in scenarios if row.get("Scenario") == "Baseline"),
        None,
    )
    downside = next(
        (row for row in scenarios if row.get("Scenario") == "Combined Downside"),
        None,
    )
    if baseline and downside:
        base_profit = number(baseline.get("Total_Profit"))
        downside_profit = number(downside.get("Total_Profit"))
        if base_profit is not None and downside_profit is not None:
            profit_change = downside_profit - base_profit
            findings.append(
                f"- **Combined downside scenario:** profit changes by "
                f"{profit_change:,.2f} compared with baseline."
            )
            recommendations.append({
                "priority": "High" if profit_change < 0 else "Review",
                "category": "Scenario risk",
                "finding": f"Combined downside scenario profit change is {profit_change:,.2f}.",
                "recommended_action": "Stress-test pricing, unit costs, and volume assumptions; prepare mitigation options before applying changes.",
                "evidence": f"Baseline profit={base_profit:.2f}; downside profit={downside_profit:.2f}",
            })

    # 6. Existing demand-planning recommendations
    for row in demand[:5]:
        recommendations.append({
            "priority": row.get("priority", "Review"),
            "category": row.get("area", "Demand planning"),
            "finding": row.get("finding", ""),
            "recommended_action": row.get("recommended_action", ""),
            "evidence": row.get("evidence", ""),
        })

    # Deterministic, auditable outputs; no external AI service is called.
    output_dir.mkdir(parents=True, exist_ok=True)

    alert_fields = ["severity", "category", "date", "message", "metric_value"]
    with (output_dir / "ai_risk_alerts.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=alert_fields)
        writer.writeheader()
        writer.writerows(alerts)

    recommendation_fields = [
        "priority", "category", "finding", "recommended_action", "evidence"
    ]
    with (output_dir / "ai_business_recommendations.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=recommendation_fields)
        writer.writeheader()
        writer.writerows(recommendations)

    summary_path = output_dir / "ai_executive_summary.md"
    with summary_path.open("w", encoding="utf-8", newline="\n") as file:
        file.write("# AI-Assisted Business Analytics Summary\n\n")
        file.write("> Generated with transparent, rule-based analysis. ")
        file.write("Findings are decision support, not causal proof.\n\n")
        file.write("## Key findings\n\n")
        file.write("\n".join(findings) if findings else "No usable findings were available.")
        file.write("\n\n## Risk alerts\n\n")
        file.write(f"- Total alerts generated: **{len(alerts)}**\n")
        file.write(f"- Recommendations generated: **{len(recommendations)}**\n")
        file.write("\n## Recommended next step\n\n")
        file.write(
            "Review high-priority alerts and verify the supporting metrics "
            "before making operational or financial decisions.\n"
        )

    print("AI ANALYTICS MVP COMPLETED")
    print(f"Executive summary: {summary_path}")
    print(f"Risk alerts: {output_dir / 'ai_risk_alerts.csv'}")
    print(f"Recommendations: {output_dir / 'ai_business_recommendations.csv'}")
    print(f"Alerts generated: {len(alerts)}")
    print(f"Recommendations generated: {len(recommendations)}")


if __name__ == "__main__":
    generate_insights()
