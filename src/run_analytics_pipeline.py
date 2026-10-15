
from pathlib import Path
import subprocess
import sys


# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON_EXECUTABLE = sys.executable

PIPELINE_STEPS = [
    (
        "Forecast Model Comparison",
        "src/forecast_model_comparison.py",
    ),
    (
        "Sales Anomaly Detection",
        "src/sales_anomaly_detection.py",
    ),
    (
        "Customer RFM Segmentation",
        "src/customer_rfm_segmentation.py",
    ),
    (
        "Sales Scenario Analysis",
        "src/sales_scenario_analysis.py",
    ),
    (
        "Business Insights Engine",
        "src/business_insights_engine.py",
    ),
        (
        "Demand Planning Analysis",
        "src/demand_planning_analysis.py",
    ),
    (
        "Forecast Visualizations",
        "src/forecast_visualizations.py",
    ),
    (
        "AI Analytics MVP",
        "src/ai_analytics_mvp.py",
    ),
    (
        "Analytics Output Validation",
        "src/validate_analytics_outputs.py",
    ),
]


# ============================================================
# 2. PIPELINE EXECUTION
# ============================================================

def run_step(step_name, script_path):
    """Run one script and stop the pipeline if it fails."""

    full_script_path = PROJECT_ROOT / script_path

    print("\n" + "=" * 72, flush=True)
    print(f"RUNNING: {step_name}", flush=True)
    print(f"Script:  {script_path}", flush=True)
    print("=" * 72, flush=True)

    result = subprocess.run(
        [PYTHON_EXECUTABLE, str(full_script_path)],
        cwd=PROJECT_ROOT,
        check=False,
    )

    if result.returncode != 0:
        print(
            f"\nPIPELINE FAILED: {step_name}",
            flush=True,
        )
        print(
            f"Exit code: {result.returncode}",
            flush=True,
        )
        return False

    print(
        f"\nCOMPLETED: {step_name}",
        flush=True,
    )
    return True


# ============================================================
# 3. MAIN ENTRY POINT
# ============================================================

def main():
    """Execute all analytics steps in sequence."""

    print("=" * 72)
    print("AUTOMATED BUSINESS INTELLIGENCE PIPELINE")
    print("=" * 72)
    print(f"Project directory: {PROJECT_ROOT}")
    print(f"Python executable: {PYTHON_EXECUTABLE}")

    for step_name, script_path in PIPELINE_STEPS:
        if not run_step(step_name, script_path):
            raise SystemExit(1)

    print("\n" + "=" * 72)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 72)
    print(f"Steps completed: {len(PIPELINE_STEPS)}")
    print("All analytics scripts and output validation succeeded.")


if __name__ == "__main__":
    main()
