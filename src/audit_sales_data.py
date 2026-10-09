
import csv
import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median, stdev

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SALES_FILE = PROJECT_ROOT / "data" / "raw" / "fact_sales.csv"


def quantile(values, probability):
    """Calculate a linearly interpolated quantile."""
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    fraction = position - lower
    return ordered[lower] + fraction * (
        ordered[upper] - ordered[lower]
    )


def print_numeric_summary(name, values):
    if not values:
        return

    print(f"\n{name}")
    print("-" * 50)
    print(f"Count:  {len(values):,}")
    print(f"Mean:   {mean(values):,.2f}")
    print(f"Median: {median(values):,.2f}")
    print(f"Std:    {stdev(values):,.2f}" if len(values) > 1 else "Std: N/A")
    print(f"Q1:     {quantile(values, 0.25):,.2f}")
    print(f"Q3:     {quantile(values, 0.75):,.2f}")
    print(f"Min:    {min(values):,.2f}")
    print(f"Max:    {max(values):,.2f}")


def print_distribution(name, counter):
    total = sum(counter.values())

    print(f"\n{name}")
    print("-" * 50)

    for value, count in counter.most_common():
        percentage = count / total * 100 if total else 0
        print(f"{str(value):25} {count:8,} ({percentage:6.2f}%)")


def main():
    numeric_columns = {
        "quantity": [],
        "unit_price": [],
        "discount_pct": [],
        "revenue": [],
        "cost": [],
        "profit": [],
    }

    categorical_columns = {
        "product_id": Counter(),
        "customer_id": Counter(),
        "order_id": Counter(),
        "payment_method": Counter(),
        "sales_channel": Counter(),
        "promotion_flag": Counter(),
        "order_date": Counter(),
    }

    total_rows = 0
    sales_ids = set()
    order_customer = {}
    duplicate_sales_ids = 0
    inconsistent_order_customers = 0

    with SALES_FILE.open(
        "r", encoding="utf-8-sig", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            total_rows += 1

            sales_id = row["sales_id"]
            if sales_id in sales_ids:
                duplicate_sales_ids += 1
            sales_ids.add(sales_id)

            for column, values in numeric_columns.items():
                values.append(float(row[column]))

            for column, counter in categorical_columns.items():
                counter[row[column]] += 1

            order_id = row["order_id"]
            customer_id = row["customer_id"]

            if order_id in order_customer:
                if order_customer[order_id] != customer_id:
                    inconsistent_order_customers += 1
            else:
                order_customer[order_id] = customer_id

    print("=" * 60)
    print("CURRENT SALES DATA AUDIT")
    print("=" * 60)
    print(f"File: {SALES_FILE}")
    print(f"Sales lines: {total_rows:,}")
    print(f"Unique sales IDs: {len(sales_ids):,}")
    print(f"Unique orders: {len(order_customer):,}")
    print(f"Duplicate sales IDs: {duplicate_sales_ids:,}")
    print(
        "Orders linked to multiple customers: "
        f"{inconsistent_order_customers:,}"
    )

    for name, values in numeric_columns.items():
        print_numeric_summary(name, values)

    for name, counter in categorical_columns.items():
        print_distribution(name, counter)

    print("\nAudit complete. No source files were modified.")


if __name__ == "__main__":
    main()
