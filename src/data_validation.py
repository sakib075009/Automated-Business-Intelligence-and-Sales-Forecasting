from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = PROJECT_ROOT / "data" / "raw"


# ============================================================
# REQUIRED FILES
# ============================================================

REQUIRED_FILES = {
    "dim_customer": "dim_customer.csv",
    "dim_date": "dim_date.csv",
    "dim_product": "dim_product.csv",
    "dim_region": "dim_region.csv",
    "fact_sales": "fact_sales.csv",
}


# ============================================================
# REQUIRED COLUMNS
# ============================================================

REQUIRED_COLUMNS = {
    "dim_customer": [
        "customer_id",
        "customer_name",
        "gender",
        "age",
        "city",
        "region_id",
        "signup_date",
        "customer_type",
        "behavior_profile",
    ],

    "dim_date": [
        "date",
        "year",
        "quarter",
        "month_number",
        "month_name",
        "week_number",
        "day",
        "day_name",
        "is_weekend",
        "month_year",
    ],

    "dim_product": [
        "product_id",
        "product_name",
        "category",
        "subcategory",
        "brand",
        "unit_cost",
        "standard_price",
        "supplier_id",
        "popularity",
    ],

    "dim_region": [
        "region_id",
        "region_name",
    ],

    "fact_sales": [
        "sales_id",
        "order_id",
        "order_date",
        "customer_id",
        "product_id",
        "region_id",
        "quantity",
        "unit_price",
        "discount_pct",
        "revenue",
        "cost",
        "profit",
        "payment_method",
        "sales_channel",
        "promotion_flag",
    ],
}


# ============================================================
# EXPECTED ROW COUNTS
# ============================================================

EXPECTED_ROW_COUNTS = {
    "dim_customer": 1500,
    "dim_date": 731,
    "dim_product": 75,
    "dim_region": 8,
    "fact_sales": 120000,
}

# These tables may grow as new sales dates are ingested.
GROWING_TABLES = {"dim_date", "fact_sales"}


# ============================================================
# PRIMARY KEYS
# ============================================================

PRIMARY_KEYS = {
    "dim_customer": "customer_id",
    "dim_date": "date",
    "dim_product": "product_id",
    "dim_region": "region_id",
    "fact_sales": "sales_id",
}


# ============================================================
# FOREIGN KEYS
# ============================================================

FOREIGN_KEYS = {
    "customer_id": ("dim_customer", "customer_id"),
    "product_id": ("dim_product", "product_id"),
    "region_id": ("dim_region", "region_id"),
    "order_date": ("dim_date", "date"),
}


# ============================================================
# 1. FILE CHECK
# ============================================================

def check_files():
    """Check whether all required CSV files exist."""

    print("\n=== FILE CHECK ===")

    all_passed = True

    for table_name, filename in REQUIRED_FILES.items():

        file_path = DATA_RAW / filename

        if file_path.exists():

            print(f"PASS | {table_name}: {filename}")

        else:

            print(f"FAIL | {table_name}: {filename} NOT FOUND")
            all_passed = False

    return all_passed


# ============================================================
# 2. DATA LOADING
# ============================================================

def load_data():
    """Load all required CSV files into pandas DataFrames."""

    print("\n=== DATA LOADING ===")

    data = {}

    for table_name, filename in REQUIRED_FILES.items():

        file_path = DATA_RAW / filename

        df = pd.read_csv(file_path)

        # Normalize date columns so date comparisons are reliable
        if table_name == "fact_sales":
            df["order_date"] = pd.to_datetime(
                df["order_date"],
                errors="raise"
            )

        elif table_name == "dim_date":
            df["date"] = pd.to_datetime(
                df["date"],
                errors="raise"
            )

        elif table_name == "dim_customer":
            df["signup_date"] = pd.to_datetime(
                df["signup_date"],
                errors="raise"
            )

        data[table_name] = df

        print(
            f"LOADED | {table_name}: "
            f"{df.shape}"
        )

    return data


# ============================================================
# 3. COLUMN CHECK
# ============================================================

def check_columns(data):
    """Check whether all required columns exist."""

    print("\n=== COLUMN CHECK ===")

    all_passed = True

    for table_name, required_columns in REQUIRED_COLUMNS.items():

        actual_columns = set(data[table_name].columns)

        missing_columns = [
            column
            for column in required_columns
            if column not in actual_columns
        ]

        if not missing_columns:

            print(
                f"PASS | {table_name}: "
                f"{len(required_columns)} required columns found"
            )

        else:

            print(
                f"FAIL | {table_name}: "
                f"missing columns: {missing_columns}"
            )

            all_passed = False

    return all_passed


# ============================================================
# 4. ROW COUNT CHECK
# ============================================================

def check_row_counts(data):
    """Check fixed table counts and minimum counts for growing tables."""

    print("\n=== ROW COUNT CHECK ===")
    all_passed = True

    for table_name, expected_count in EXPECTED_ROW_COUNTS.items():
        actual_count = len(data[table_name])

        if table_name in GROWING_TABLES:
            passed = actual_count >= expected_count
            requirement = f"at least {expected_count:,}"
        else:
            passed = actual_count == expected_count
            requirement = f"exactly {expected_count:,}"

        if passed:
            print(
                f"PASS | {table_name}: {actual_count:,} rows "
                f"(expected {requirement})"
            )
        else:
            print(
                f"FAIL | {table_name}: expected {requirement} rows, "
                f"found {actual_count:,}"
            )
            all_passed = False

    return all_passed


# ============================================================
# 5. MISSING VALUE CHECK
# ============================================================

def check_missing_values(data):
    """Check for missing values."""

    print("\n=== MISSING VALUE CHECK ===")

    all_passed = True

    for table_name, df in data.items():

        missing_count = int(df.isna().sum().sum())

        if missing_count == 0:

            print(
                f"PASS | {table_name}: "
                f"0 missing values"
            )

        else:

            print(
                f"FAIL | {table_name}: "
                f"{missing_count:,} missing values"
            )

            all_passed = False

    return all_passed


# ============================================================
# 6. PRIMARY KEY CHECK
# ============================================================

def check_duplicate_keys(data):
    """Check for duplicate primary keys."""

    print("\n=== PRIMARY KEY CHECK ===")

    all_passed = True

    for table_name, key_column in PRIMARY_KEYS.items():

        duplicate_count = int(
            data[table_name][key_column].duplicated().sum()
        )

        if duplicate_count == 0:

            print(
                f"PASS | {table_name}[{key_column}]: "
                f"0 duplicates"
            )

        else:

            print(
                f"FAIL | {table_name}[{key_column}]: "
                f"{duplicate_count:,} duplicates"
            )

            all_passed = False

    return all_passed


# ============================================================
# 7. FOREIGN KEY CHECK
# ============================================================

def check_foreign_keys(data):
    """Check foreign-key integrity between fact and dimension tables."""

    print("\n=== FOREIGN KEY CHECK ===")

    all_passed = True

    fact_sales = data["fact_sales"]

    for fact_column, (dimension_name, dimension_column) in FOREIGN_KEYS.items():

        fact_values = set(
            fact_sales[fact_column].dropna().unique()
        )

        dimension_values = set(
            data[dimension_name][dimension_column].dropna().unique()
        )

        invalid_values = fact_values - dimension_values

        if not invalid_values:

            print(
                f"PASS | fact_sales[{fact_column}] -> "
                f"{dimension_name}[{dimension_column}]: "
                f"0 invalid keys"
            )

        else:

            print(
                f"FAIL | fact_sales[{fact_column}] -> "
                f"{dimension_name}[{dimension_column}]: "
                f"{len(invalid_values):,} invalid keys"
            )

            all_passed = False

    return all_passed


# ============================================================
# MAIN VALIDATION PIPELINE
# ============================================================

def main():

    print("=" * 60)
    print("DATA PIPELINE VALIDATION")
    print("=" * 60)

    # 1. File check
    files_ok = check_files()

    if not files_ok:

        print(
            "\nVALIDATION FAILED: "
            "Required files are missing."
        )

        raise SystemExit(1)

    # 2. Load data
    data = load_data()

    # 3. Column check
    columns_ok = check_columns(data)

    if not columns_ok:

        print(
            "\nVALIDATION FAILED: "
            "Required columns are missing."
        )

        raise SystemExit(1)

    # 4. Row count check
    row_counts_ok = check_row_counts(data)

    if not row_counts_ok:

        print(
            "\nVALIDATION FAILED: "
            "Unexpected row counts detected."
        )

        raise SystemExit(1)

    # 5. Missing value check
    missing_values_ok = check_missing_values(data)

    if not missing_values_ok:

        print(
            "\nVALIDATION FAILED: "
            "Missing values detected."
        )

        raise SystemExit(1)

    # 6. Primary-key check
    duplicate_keys_ok = check_duplicate_keys(data)

    if not duplicate_keys_ok:

        print(
            "\nVALIDATION FAILED: "
            "Duplicate primary keys detected."
        )

        raise SystemExit(1)

    # 7. Foreign-key check
    foreign_keys_ok = check_foreign_keys(data)

    if not foreign_keys_ok:

        print(
            "\nVALIDATION FAILED: "
            "Foreign-key integrity problems detected."
        )

        raise SystemExit(1)

    # 8. Business-rule check
    business_rules_ok = check_business_rules(data)

    if not business_rules_ok:

        print(
            "\nVALIDATION FAILED: "
            "Business-rule violations detected."
        )

        raise SystemExit(1)
    
    # Final success message
    print("\n" + "=" * 60)
    print("DATA STRUCTURE VALIDATION PASSED")
    print("=" * 60)

# ============================================================
# 8. BUSINESS RULE CHECK
# ============================================================

def check_business_rules(data):
    """Check business logic and calculation rules."""

    print("\n=== BUSINESS RULE CHECK ===")

    all_passed = True

    fact_sales = data["fact_sales"]
    dim_customer = data["dim_customer"]
    dim_product = data["dim_product"]
    dim_region = data["dim_region"]

    # --------------------------------------------------------
    # 1. Sales date range
    # --------------------------------------------------------

    min_date = fact_sales["order_date"].min()
    max_date = fact_sales["order_date"].max()

    expected_min_date = pd.Timestamp("2024-01-01")

    if min_date == expected_min_date and max_date >= expected_min_date:

        print(
            f"PASS | Sales date range: "
            f"{min_date.date()} to {max_date.date()}"
        )

    else:

        print(
            f"FAIL | Sales date range: "
            f"{min_date.date()} to {max_date.date()}"
        )

        all_passed = False

    # --------------------------------------------------------
    # 2. Customer signup-date rule
    # Sales cannot occur before customer signup
    # --------------------------------------------------------

    customer_signup = dim_customer[
        ["customer_id", "signup_date"]
    ]

    sales_with_signup = fact_sales.merge(
        customer_signup,
        on="customer_id",
        how="left"
    )

    signup_violations = (
        sales_with_signup["order_date"]
        < sales_with_signup["signup_date"]
    ).sum()

    if signup_violations == 0:

        print(
            "PASS | Customer signup-date rule: "
            "0 violations"
        )

    else:

        print(
            f"FAIL | Customer signup-date rule: "
            f"{signup_violations:,} violations"
        )

        all_passed = False

    # --------------------------------------------------------
    # 3. Quantity validity
    # --------------------------------------------------------

    negative_quantity = (
        fact_sales["quantity"] < 0
    ).sum()

    if negative_quantity == 0:

        print(
            "PASS | Quantity validity: "
            "0 negative quantities"
        )

    else:

        print(
            f"FAIL | Quantity validity: "
            f"{negative_quantity:,} negative quantities"
        )

        all_passed = False

    # --------------------------------------------------------
    # 4. Revenue validity
    # --------------------------------------------------------

    negative_revenue = (
        fact_sales["revenue"] < 0
    ).sum()

    if negative_revenue == 0:

        print(
            "PASS | Revenue validity: "
            "0 negative revenue values"
        )

    else:

        print(
            f"FAIL | Revenue validity: "
            f"{negative_revenue:,} negative revenue values"
        )

        all_passed = False

    # --------------------------------------------------------
    # 5. Cost validity
    # --------------------------------------------------------

    negative_cost = (
        fact_sales["cost"] < 0
    ).sum()

    if negative_cost == 0:

        print(
            "PASS | Cost validity: "
            "0 negative cost values"
        )

    else:

        print(
            f"FAIL | Cost validity: "
            f"{negative_cost:,} negative cost values"
        )

        all_passed = False

    # --------------------------------------------------------
    # 6. Revenue calculation
    # Revenue = Quantity × Unit Price × (1 - Discount)
    # --------------------------------------------------------

    calculated_revenue = (
    fact_sales["quantity"]
    * fact_sales["unit_price"]
    * (1 - fact_sales["discount_pct"] / 100)
    )

    revenue_difference = (
        calculated_revenue
        - fact_sales["revenue"]
    ).abs()

    revenue_errors = (
        revenue_difference > 0.01
    ).sum()

    max_revenue_error = revenue_difference.max()

    if revenue_errors == 0:

        print(
            "PASS | Revenue calculation: "
            f"0 errors "
            f"(max difference: {max_revenue_error:.4f})"
        )

    else:

        print(
            f"FAIL | Revenue calculation: "
            f"{revenue_errors:,} errors "
            f"(max difference: {max_revenue_error:.4f})"
        )

        all_passed = False

    # --------------------------------------------------------
    # 7. Profit calculation
    # Profit = Revenue - Cost
    # --------------------------------------------------------

    calculated_profit = (
        fact_sales["revenue"]
        - fact_sales["cost"]
    )

    profit_difference = (
        calculated_profit
        - fact_sales["profit"]
    ).abs()

    profit_errors = (
        profit_difference > 0.011
    ).sum()

    max_profit_error = profit_difference.max()

    if profit_errors == 0:

        print(
            "PASS | Profit calculation: "
            f"0 errors "
            f"(max difference: {max_profit_error:.4f})"
        )

    else:

        print(
            f"FAIL | Profit calculation: "
            f"{profit_errors:,} errors "
            f"(max difference: {max_profit_error:.4f})"
        )

        all_passed = False

    # --------------------------------------------------------
    # 8. Discount percentage validity
    # --------------------------------------------------------

    invalid_discount = (
        (fact_sales["discount_pct"] < 0)
        |
        (fact_sales["discount_pct"] > 20)
    ).sum()

    if invalid_discount == 0:

        print(
            "PASS | Discount percentage: "
            "0 invalid values"
        )

    else:

        print(
            f"FAIL | Discount percentage: "
            f"{invalid_discount:,} invalid values"
        )

        all_passed = False

    # --------------------------------------------------------
    # 9. Product dimension coverage
    # --------------------------------------------------------

    products_used = (
        fact_sales["product_id"]
        .nunique()
    )

    total_products = (
        dim_product["product_id"]
        .nunique()
    )

    if products_used == total_products:

        print(
            f"PASS | Product coverage: "
            f"{products_used} of {total_products} products used"
        )

    else:

        print(
            f"FAIL | Product coverage: "
            f"{products_used} of {total_products} products used"
        )

        all_passed = False

    # --------------------------------------------------------
    # 10. Region dimension coverage
    # --------------------------------------------------------

    regions_used = (
        fact_sales["region_id"]
        .nunique()
    )

    total_regions = (
        dim_region["region_id"]
        .nunique()
    )

    if regions_used == total_regions:

        print(
            f"PASS | Region coverage: "
            f"{regions_used} of {total_regions} regions used"
        )

    else:

        print(
            f"FAIL | Region coverage: "
            f"{regions_used} of {total_regions} regions used"
        )

        all_passed = False

    return all_passed


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()