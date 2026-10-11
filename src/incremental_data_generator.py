
"""Incremental synthetic sales generator for the Automated BI project.

Default behavior is preview-only. Use --apply to append a validated batch.
Uses Python's standard library to avoid importing pandas/PyArrow.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile
import os
import hashlib
import io


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
FACT_FILE = RAW / "fact_sales.csv"
DATE_FILE = RAW / "dim_date.csv"
STATE_FILE = RAW / "incremental_generator_state.json"
JOURNAL_FILE = RAW / "incremental_generator_pending.json"

CUTOFF_DAYS = 90
FIRST_SIMULATED_DATE = date(2026, 1, 1)
BATCH_PATTERN = (3, 3, 3, 4)
MIN_LINES_PER_DAY = 40
MAX_LINES_PER_DAY = 50
RANDOM_SEED = 42

FACT_COLUMNS = [
    "sales_id", "order_id", "order_date", "customer_id",
    "product_id", "region_id", "quantity", "unit_price",
    "discount_pct", "revenue", "cost", "profit",
    "payment_method", "sales_channel", "promotion_flag",
]

DATE_COLUMNS = [
    "date", "year", "quarter", "month_number", "month_name",
    "week_number", "day", "day_name", "is_weekend", "month_year",
]


def parse_date(value: str) -> date:
    """Accept the date formats commonly written by pandas/Excel."""
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unsupported date format: {value!r}")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def date_output_format(sample: str) -> str:
    return "%m/%d/%Y" if "/" in sample else "%Y-%m-%d"


def format_date(value: date, fmt: str) -> str:
    return value.strftime(fmt)


def next_numeric_id(values: list[str], prefix: str) -> int:
    numbers = []
    for value in values:
        match = re.fullmatch(rf"{re.escape(prefix)}(\d+)", value.strip())
        if match:
            numbers.append(int(match.group(1)))
    if not numbers:
        raise ValueError(f"No IDs matching {prefix}<number> were found.")
    return max(numbers) + 1



def make_date_row(day: date, fmt: str) -> dict[str, str]:
    return {
        "date": format_date(day, fmt),
        "year": str(day.year),
        "quarter": f"Q{((day.month - 1) // 3) + 1}",
        "month_number": str(day.month),
        "month_name": day.strftime("%B"),
        "week_number": str(day.isocalendar().week),
        "day": str(day.day),
        "day_name": day.strftime("%A"),
        "is_weekend": "1" if day.weekday() >= 5 else "0",
        "month_year": day.strftime("%Y-%m"),
    }



def atomic_write_csv(
    path: Path,
    rows: list[dict[str, str]],
    columns: list[str],
) -> None:
    """Write to a temporary file, then replace the destination."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_name = None
    try:
        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp_name, path)
    finally:
        if temp_name and os.path.exists(temp_name):
            os.unlink(temp_name)



def restore_original_files(
    original_contents: dict[Path, bytes | None],
) -> list[str]:
    """Restore original files and return any restoration errors."""
    rollback_errors = []

    for path, contents in original_contents.items():
        try:
            if contents is None:
                if path.exists():
                    path.unlink()
            else:
                restore_temp = path.with_suffix(path.suffix + ".restore")
                try:
                    restore_temp.write_bytes(contents)
                    os.replace(restore_temp, path)
                finally:
                    if restore_temp.exists():
                        restore_temp.unlink()
        except Exception as rollback_error:
            rollback_errors.append(
                f"{path.name}: {rollback_error}"
            )

    return rollback_errors



def atomic_write_json(path: Path, data: dict) -> None:
    """Write JSON atomically using consistent UTF-8 bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")

    try:
        content = json.dumps(data, indent=2).encode("utf-8")
        temp_path.write_bytes(content)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()



    def test_failed_write_restores_original_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            fact = temp / "fact_sales.csv"
            dates = temp / "dim_date.csv"
            state = temp / "state.json"

            originals = {
                fact: b"original sales\n",
                dates: b"original dates\n",
                state: b"original state\n",
            }

            for path, content in originals.items():
                path.write_bytes(content)

            # Simulate a partially changed sales file.
            fact.write_bytes(b"partially changed sales\n")

            # The production rollback function must restore every file.
            rollback_errors = generator.restore_original_files(originals)

            self.assertEqual(rollback_errors, [])

            for path, content in originals.items():
                self.assertTrue(path.exists())
                self.assertEqual(path.read_bytes(), content)



def sha256_file(path: Path) -> str | None:
    """Return a file's SHA-256 hash, or None if it doesn't exist."""
    if not path.exists():
        return None

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()



def sha256_bytes(content: bytes) -> str:
    """Calculate the SHA-256 hash of bytes."""
    return hashlib.sha256(content).hexdigest()


def sha256_csv_rows(
    rows: list[dict[str, str]],
    columns: list[str],
) -> str:
    """Hash the CSV content exactly as the CSV writer would produce it."""
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return sha256_bytes(buffer.getvalue().encode("utf-8"))


def sha256_json_data(data: dict) -> str:
    """Hash JSON using the same formatting as atomic_write_json()."""
    content = json.dumps(data, indent=2).encode("utf-8")
    return sha256_bytes(content)



def load_pending_journal() -> dict | None:
    """Load an unfinished batch journal, if one exists."""
    if not JOURNAL_FILE.exists():
        return None

    with JOURNAL_FILE.open("r", encoding="utf-8") as handle:
        journal = json.load(handle)

    required_keys = {
        "status",
        "sales_rows",
        "date_rows",
        "next_state",
    }
    missing = required_keys - journal.keys()

    if missing:
        raise ValueError(
            f"Pending journal is incomplete; missing keys: {sorted(missing)}"
        )

    if journal["status"] != "pending":
        raise ValueError(
            f"Unexpected journal status: {journal['status']!r}"
        )

    if not isinstance(journal["sales_rows"], list):
        raise ValueError("Journal sales_rows must be a list.")

    if not isinstance(journal["date_rows"], list):
        raise ValueError("Journal date_rows must be a list.")

    if not isinstance(journal["next_state"], dict):
        raise ValueError("Journal next_state must be a dictionary.")

    return journal



def recover_pending_journal() -> bool:
    """Validate and safely resume a pending batch transaction."""
    journal = load_pending_journal()

    if journal is None:
        print("No pending recovery journal found.")
        return False

    required_hash_keys = {"original_hashes", "expected_hashes"}
    missing = required_hash_keys - journal.keys()
    if missing:
        raise ValueError(
            f"Journal lacks required integrity hashes: {sorted(missing)}"
        )

    original_hashes = journal["original_hashes"]
    expected_hashes = journal["expected_hashes"]

    targets = {
        str(FACT_FILE): FACT_FILE,
        str(DATE_FILE): DATE_FILE,
        str(STATE_FILE): STATE_FILE,
    }

    for label, hashes in (
        ("original_hashes", original_hashes),
        ("expected_hashes", expected_hashes),
    ):
        if not isinstance(hashes, dict) or set(hashes) != set(targets):
            raise ValueError(
                f"Journal {label} does not contain the expected file paths."
            )

    sales_rows = journal["sales_rows"]
    date_rows = journal["date_rows"]
    next_state = journal["next_state"]


    if not isinstance(sales_rows, list) or not sales_rows:
        raise ValueError("Journal sales rows must be a non-empty list.")

    if not isinstance(date_rows, list) or not date_rows:
        raise ValueError("Journal date rows must be a non-empty list.")

    if not isinstance(next_state, dict):
        raise ValueError("Journal next_state must be a dictionary.")

    if not all(isinstance(row, dict) for row in sales_rows):
        raise ValueError("Journal contains an invalid sales row.")

    if not all(isinstance(row, dict) for row in date_rows):
        raise ValueError("Journal contains an invalid date row.")


    # Verify every row has the exact expected schema.
    if any(list(row.keys()) != FACT_COLUMNS for row in sales_rows):
        raise ValueError("Journal sales rows have an invalid schema.")

    if any(list(row.keys()) != DATE_COLUMNS for row in date_rows):
        raise ValueError("Journal date rows have an invalid schema.")

    # Verify the saved payload actually matches its expected hashes.
    if sha256_csv_rows(sales_rows, FACT_COLUMNS) != expected_hashes[str(FACT_FILE)]:
        raise ValueError("Journal sales payload failed its hash check.")

    if sha256_csv_rows(date_rows, DATE_COLUMNS) != expected_hashes[str(DATE_FILE)]:
        raise ValueError("Journal date payload failed its hash check.")

    if sha256_json_data(next_state) != expected_hashes[str(STATE_FILE)]:
        raise ValueError("Journal state payload failed its hash check.")

    # Do not overwrite files changed by anything other than this transaction.
    for path_key, path in targets.items():
        current_hash = sha256_file(path)
        original_hash = original_hashes[path_key]
        expected_hash = expected_hashes[path_key]

        if current_hash not in {original_hash, expected_hash}:
            raise RuntimeError(
                f"Recovery stopped: {path.name} matches neither its "
                "original nor expected hash. Preserve the journal and "
                "inspect the file before proceeding."
            )

    # The transaction is validated. Replaying these complete replacement
    # tables is idempotent: it does not generate new IDs or rows.
    atomic_write_csv(FACT_FILE, sales_rows, FACT_COLUMNS)
    atomic_write_csv(DATE_FILE, date_rows, DATE_COLUMNS)
    atomic_write_json(STATE_FILE, next_state)

    # Confirm all three files match the intended final state.
    for path_key, path in targets.items():
        if sha256_file(path) != expected_hashes[path_key]:
            raise RuntimeError(
                f"Recovery verification failed for {path.name}. "
                "The journal has been retained for investigation."
            )

    # Delete the journal only after the final verification succeeds.
    JOURNAL_FILE.unlink()

    print("RECOVERY SUCCESS")
    print(f"Sales rows in restored table: {len(sales_rows):,}")
    print(f"Date rows in restored table: {len(date_rows):,}")
    print("All recovered files passed their hash checks.")

    return True



def planned_batch_size(run_date: date, batch_index: int) -> int:
    """Return the number of simulated dates for a scheduled run."""
    if run_date >= date(2027, 1, 1):
        return 1

    return BATCH_PATTERN[batch_index % len(BATCH_PATTERN)]


def plan_simulated_dates(
    start_date: date,
    run_date: date,
    batch_index: int,
) -> list[date]:
    """Plan consecutive simulated dates subject to the 90-day cutoff."""
    cutoff = run_date - timedelta(days=CUTOFF_DAYS)
    requested_days = planned_batch_size(run_date, batch_index)

    planned: list[date] = []
    candidate = start_date

    while len(planned) < requested_days and candidate <= cutoff:
        planned.append(candidate)
        candidate += timedelta(days=1)

    return planned



def validate_source_integrity(source_hashes: dict) -> None:
    """Stop if tracked source CSVs differ from the last successful batch."""
    expected_keys = {"fact_sales", "dim_date"}

    if not isinstance(source_hashes, dict) or set(source_hashes) != expected_keys:
        raise ValueError("Invalid source-integrity metadata in generator state.")

    actual_hashes = {
        "fact_sales": sha256_file(FACT_FILE),
        "dim_date": sha256_file(DATE_FILE),
    }

    if actual_hashes != source_hashes:
        raise RuntimeError(
            "Source-integrity check failed: fact_sales.csv or "
            "dim_date.csv changed since the last successful batch. "
            "No new batch was generated. Inspect the files and state."
        )


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"next_batch_index": 0, "last_run_date": None}
    with STATE_FILE.open("r", encoding="utf-8") as handle:
        state = json.load(handle)
    state.setdefault("next_batch_index", 0)
    state.setdefault("last_run_date", None)
    return state


def validate_dimensions(
    customers: list[dict[str, str]],
    products: list[dict[str, str]],
    regions: list[dict[str, str]],
    fact_rows: list[dict[str, str]],
    date_rows: list[dict[str, str]],
) -> None:
    for label, rows, key in (
        ("customers", customers, "customer_id"),
        ("products", products, "product_id"),
        ("regions", regions, "region_id"),
    ):
        if not rows or any(not row.get(key) for row in rows):
            raise ValueError(f"Dimension {label} is empty or has missing {key} values.")

    if not fact_rows:
        raise ValueError("The existing sales fact table is empty.")

    if list(fact_rows[0].keys()) != FACT_COLUMNS:
        raise ValueError(
            "The sales fact columns do not match the expected 15-column schema."
        )

    if list(date_rows[0].keys()) != DATE_COLUMNS:
        raise ValueError("The date dimension columns do not match the expected schema.")

    customer_ids = {row["customer_id"] for row in customers}
    product_ids = {row["product_id"] for row in products}
    region_ids = {row["region_id"] for row in regions}

    if any(row["customer_id"] not in customer_ids for row in fact_rows):
        raise ValueError("Existing sales contain an invalid customer reference.")
    if any(row["product_id"] not in product_ids for row in fact_rows):
        raise ValueError("Existing sales contain an invalid product reference.")
    if any(row["region_id"] not in region_ids for row in fact_rows):
        raise ValueError("Existing sales contain an invalid region reference.")


def generate_day(
    day: date,
    line_count: int,
    customers: list[dict[str, str]],
    products: list[dict[str, str]],
    rng: random.Random,
    next_sales_number: int,
    next_order_number: int,
    fact_date_fmt: str,
) -> tuple[list[dict[str, str]], int, int]:
    """Generate sales lines for one simulated date."""
    eligible_customers = [
        c for c in customers
        if parse_date(c["signup_date"]) <= day
    ]
    if not eligible_customers:
        raise ValueError(f"No customers are eligible on {day}.")

    product_by_id = {p["product_id"]: p for p in products}


    # Convert categorical popularity into numeric selection weights.
    popularity_weights = {
        "low": 1.0,
        "medium": 2.0,
        "high": 3.0,
    }

    product_weights = [
        popularity_weights.get(
            str(p.get("popularity", "medium")).strip().lower(),
            1.0,
        )
        for p in products
    ]


    lines: list[dict[str, str]] = []
    remaining = line_count

    payment_methods = ["Mobile Banking", "Card", "Cash", "Bank Transfer"]
    payment_weights = [0.35, 0.30, 0.20, 0.15]
    channels = ["Online", "Store", "Marketplace"]
    channel_weights = [0.50, 0.30, 0.20]

    while remaining > 0:
        line_size = min(remaining, rng.choices([1, 2, 3, 4], [0.20, 0.40, 0.30, 0.10])[0])
        customer = rng.choice(eligible_customers)
        region_id = customer["region_id"]

        selected_products = rng.choices(
            products, weights=product_weights, k=1
        )
        while len(selected_products) < line_size:
            candidate = rng.choices(products, weights=product_weights, k=1)[0]
            if candidate["product_id"] not in {
                p["product_id"] for p in selected_products
            }:
                selected_products.append(candidate)

        order_id = f"O{next_order_number:06d}"
        next_order_number += 1

        payment = rng.choices(payment_methods, payment_weights, k=1)[0]
        channel = rng.choices(channels, channel_weights, k=1)[0]

        for product in selected_products:
            quantity = rng.randint(1, 5)
            standard_price = float(product["standard_price"])
            unit_cost = float(product["unit_cost"])

            unit_price = round(
                standard_price * rng.uniform(0.95, 1.05), 2
            )
            promotion_flag = 1 if rng.random() < 0.175 else 0
            discount_pct = (
                round(rng.uniform(5, 20), 2)
                if promotion_flag
                else 0.0
            )

            revenue = round(
                quantity * unit_price * (1 - discount_pct / 100), 2
            )
            cost = round(quantity * unit_cost, 2)
            profit = round(revenue - cost, 2)

            lines.append({
                "sales_id": f"S{next_sales_number:06d}",
                "order_id": order_id,
                "order_date": format_date(day, fact_date_fmt),
                "customer_id": customer["customer_id"],
                "product_id": product["product_id"],
                "region_id": region_id,
                "quantity": str(quantity),
                "unit_price": f"{unit_price:.2f}",
                "discount_pct": f"{discount_pct:.2f}",
                "revenue": f"{revenue:.2f}",
                "cost": f"{cost:.2f}",
                "profit": f"{profit:.2f}",
                "payment_method": payment,
                "sales_channel": channel,
                "promotion_flag": str(promotion_flag),
            })
            next_sales_number += 1

        remaining -= line_size

    return lines, next_sales_number, next_order_number


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a safe incremental batch of synthetic sales."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the new sales and date dimension. Default is preview only.",
    )

    parser.add_argument(
        "--today",
        help="Optional test date in YYYY-MM-DD format; does not change the system clock.",
    )
    parser.add_argument(
        "--recover",
        action="store_true",
        help="Resume a pending transaction from its recovery journal.",
    )
    args = parser.parse_args()


    if args.recover:
        if not JOURNAL_FILE.exists():
            print("No pending recovery journal found. Nothing to recover.")
            return 0

        recover_pending_journal()
        return 0

    if JOURNAL_FILE.exists():
        print("STOP: A pending recovery journal exists.")
        print("Review the pending transaction before generating another batch.")
        print("Inspect the journal and source files before running --recover.")
        return 2


    today = parse_date(args.today) if args.today else date.today()
    cutoff = today - timedelta(days=CUTOFF_DAYS)

    # Load source tables.
    customers = read_csv(RAW / "dim_customer.csv")
    products = read_csv(RAW / "dim_product.csv")
    regions = read_csv(RAW / "dim_region.csv")
    fact_rows = read_csv(FACT_FILE)
    date_rows = read_csv(DATE_FILE)

    validate_dimensions(
        customers, products, regions, fact_rows, date_rows
    )

    fact_dates = [
        parse_date(row["order_date"]) for row in fact_rows
    ]
    date_dimension_dates = {
        parse_date(row["date"]) for row in date_rows
    }
    latest_fact_date = max(fact_dates)

    # Find the next incremental date.
    existing_incremental_dates = [
        d for d in fact_dates if d >= FIRST_SIMULATED_DATE
    ]
    next_day = (
        max(existing_incremental_dates) + timedelta(days=1)
        if existing_incremental_dates
        else FIRST_SIMULATED_DATE
    )

    state_file_existed = STATE_FILE.exists()
    state = load_state()

    # Fail closed if a previously tracked source table has changed.
    if state_file_existed:
        source_hashes = state.get("source_hashes")

        if not isinstance(source_hashes, dict):
            raise ValueError(
                "Existing generator state has no source-integrity hashes. "
                "Verify the source data and explicitly initialize a new "
                "baseline before continuing."
            )

        expected_source_keys = {"fact_sales", "dim_date"}
        if set(source_hashes) != expected_source_keys:
            raise ValueError(
                "Generator state contains invalid source-integrity metadata."
            )

        validate_source_integrity(source_hashes)

    if args.apply and state.get("last_run_date") == today.isoformat():
        print("STOP: An apply run has already completed today.")
        print("No files were changed.")
        return 2


    batch_index = int(state["next_batch_index"]) % len(BATCH_PATTERN)
    requested_days = planned_batch_size(today, batch_index)
    eligible_days = plan_simulated_dates(
        next_day, today, batch_index
    )


    print("=" * 60)
    print("INCREMENTAL SALES GENERATOR")
    print("=" * 60)
    print(f"Mode: {'APPLY' if args.apply else 'PREVIEW ONLY'}")
    print(f"Today: {today}")
    print(f"90-day cutoff: {cutoff}")
    print(f"Latest existing sales date: {latest_fact_date}")
    print(f"Next incremental date: {next_day}")
    print(f"Batch pattern: {BATCH_PATTERN}")
    print(f"Current batch: {requested_days} date(s)")
    print(f"Eligible date count: {len(eligible_days)}")

    if not eligible_days:
        print("No eligible dates are available. No changes made.")
        return 0

    print(
        f"Planned dates: {eligible_days[0]} through "
        f"{eligible_days[-1]}"
    )

    # Plan reproducible, variable row counts for each date.
    row_count_rng = random.Random(
        RANDOM_SEED + sum(d.toordinal() for d in eligible_days)
    )
    daily_line_counts = {
        day: row_count_rng.randint(
            MIN_LINES_PER_DAY, MAX_LINES_PER_DAY
        )
        for day in eligible_days
    }

    print("Planned rows by date:")
    for day, count in daily_line_counts.items():
        print(f"  {day}: {count} sales rows")

    planned_total = sum(daily_line_counts.values())
    print(f"Planned sales lines: {planned_total:,}")

    if not args.apply:
        print("\nPreview complete. No files were changed.")
        print("Run with --apply only after reviewing the plan.")
        return 0

    # Prepare ID sequences and date formats.
    fact_fmt = date_output_format(fact_rows[0]["order_date"])
    dim_fmt = date_output_format(date_rows[0]["date"])

    next_sales_number = next_numeric_id(
        [row["sales_id"] for row in fact_rows], "S"
    )
    next_order_number = next_numeric_id(
        [row["order_id"] for row in fact_rows], "O"
    )

    # Reproducible synthetic values for this planned batch.
    batch_seed = (
        RANDOM_SEED
        + next_sales_number
        + batch_index
        + sum(d.toordinal() for d in eligible_days)
    )
    rng = random.Random(batch_seed)

    new_sales: list[dict[str, str]] = []

    for day in eligible_days:
        daily_lines, next_sales_number, next_order_number = generate_day(
            day=day,
            line_count=daily_line_counts[day],
            customers=customers,
            products=products,
            rng=rng,
            next_sales_number=next_sales_number,
            next_order_number=next_order_number,
            fact_date_fmt=fact_fmt,
        )
        new_sales.extend(daily_lines)

    # Validate IDs and dimension references before writing anything.
    old_sales_ids = {row["sales_id"] for row in fact_rows}
    old_order_ids = {row["order_id"] for row in fact_rows}
    new_sales_ids = [row["sales_id"] for row in new_sales]
    new_order_ids = {row["order_id"] for row in new_sales}

    if len(new_sales_ids) != len(set(new_sales_ids)):
        raise ValueError("New batch contains duplicate sales IDs.")

    if old_sales_ids.intersection(new_sales_ids):
        raise ValueError("New sales IDs overlap existing IDs.")

    if old_order_ids.intersection(new_order_ids):
        raise ValueError("New order IDs overlap existing IDs.")

    customer_ids = {row["customer_id"] for row in customers}
    product_ids = {row["product_id"] for row in products}
    region_ids = {row["region_id"] for row in regions}

    if any(
        row["customer_id"] not in customer_ids for row in new_sales
    ):
        raise ValueError("New batch contains an invalid customer ID.")

    if any(
        row["product_id"] not in product_ids for row in new_sales
    ):
        raise ValueError("New batch contains an invalid product ID.")

    if any(
        row["region_id"] not in region_ids for row in new_sales
    ):
        raise ValueError("New batch contains an invalid region ID.")

    if any(
        parse_date(row["order_date"]) > cutoff for row in new_sales
    ):
        raise ValueError("New batch exceeds the 90-day cutoff.")

    if len(new_sales) != planned_total:
        raise ValueError(
            f"Generated {len(new_sales)} rows; expected {planned_total}."
        )

    product_costs = {
        product["product_id"]: float(product["unit_cost"]) for product in products
    }

    # Validate financial calculations in every generated sales row.
    for row in new_sales:
        quantity = int(row["quantity"])
        unit_price = float(row["unit_price"])
        discount_pct = float(row["discount_pct"])
        revenue = float(row["revenue"])
        cost = float(row["cost"])
        profit = float(row["profit"])

        expected_revenue = round(
            quantity * unit_price * (1 - discount_pct / 100), 2
        )
        expected_cost = round(
            quantity * product_costs[row["product_id"]], 2
        )
        expected_profit = round(revenue - cost, 2)

        if revenue != expected_revenue:
            raise ValueError(
                f"Revenue calculation failed for {row['sales_id']}."
            )

        if cost != expected_cost:
            raise ValueError(
                f"Cost calculation failed for {row['sales_id']}."
            )

        if profit != expected_profit:
            raise ValueError(
                f"Profit calculation failed for {row['sales_id']}."
            )


    if any(
        not MIN_LINES_PER_DAY <= daily_line_counts[day] <= MAX_LINES_PER_DAY
        for day in eligible_days
    ):
        raise ValueError("A planned daily row count is outside the allowed 40-50 range.")

    # Prepare replacement tables in memory.
    combined_sales = fact_rows + new_sales
    new_dates = [
        day for day in eligible_days
        if day not in date_dimension_dates
    ]
    updated_date_rows = date_rows + [
        make_date_row(day, dim_fmt) for day in new_dates
    ]


    # Validate that every generated sales date exists in the updated date dimension.
    updated_date_values = {
        parse_date(row["date"]) for row in updated_date_rows
    }

    missing_sales_dates = {
        parse_date(row["order_date"]) for row in new_sales
    } - updated_date_values

    if missing_sales_dates:
        raise ValueError(
            "Generated sales dates are missing from the updated "
            f"date dimension: {sorted(missing_sales_dates)}"
        )


    # Back up all files that will change, including the state file.
    backup_dir = ROOT / "data" / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    targets = [FACT_FILE, DATE_FILE, STATE_FILE]
    original_contents = {
        path: path.read_bytes() if path.exists() else None
        for path in targets
    }

    for path in targets:
        if original_contents[path] is not None:
            backup_path = backup_dir / f"{path.stem}_{stamp}{path.suffix}"
            backup_path.write_bytes(original_contents[path])

    # Update state only as part of the successful write sequence.
    updated_state = dict(state)
    updated_state["source_hashes"] = {
        "fact_sales": sha256_csv_rows(combined_sales, FACT_COLUMNS),
        "dim_date": sha256_csv_rows(updated_date_rows, DATE_COLUMNS),
    }
    updated_state["next_batch_index"] = (
        batch_index + 1
    ) % len(BATCH_PATTERN)
    updated_state["last_run_date"] = today.isoformat()
    updated_state["last_generated_date"] = eligible_days[-1].isoformat()
    updated_state["last_generated_lines"] = len(new_sales)
    updated_state["daily_line_counts"] = {
        day.isoformat(): count
        for day, count in daily_line_counts.items()
    }


    # Persist the complete intended transaction before changing any files.
    journal = {
    "status": "pending",
    "created_at": datetime.now().isoformat(timespec="seconds"),
    "sales_rows": combined_sales,
    "date_rows": updated_date_rows,
    "next_state": updated_state,
    "original_hashes": {
        str(FACT_FILE): sha256_file(FACT_FILE),
        str(DATE_FILE): sha256_file(DATE_FILE),
        str(STATE_FILE): sha256_file(STATE_FILE),
    },
    "expected_hashes": {
        str(FACT_FILE): sha256_csv_rows(combined_sales, FACT_COLUMNS),
        str(DATE_FILE): sha256_csv_rows(updated_date_rows, DATE_COLUMNS),
        str(STATE_FILE): sha256_json_data(updated_state),
    },
    }
    atomic_write_json(JOURNAL_FILE, journal)

    print("Recovery journal saved.")



    try:
        # Write all three files.
        atomic_write_csv(FACT_FILE, combined_sales, FACT_COLUMNS)
        atomic_write_csv(DATE_FILE, updated_date_rows, DATE_COLUMNS)
        atomic_write_json(STATE_FILE, updated_state)

        # Verify every written file before declaring success.
        expected_hashes = journal["expected_hashes"]

        for path in targets:
            if sha256_file(path) != expected_hashes[str(path)]:
                raise RuntimeError(
                    f"Post-write integrity check failed for {path.name}."
                )

    except Exception:
        rollback_errors = restore_original_files(original_contents)

        if rollback_errors:
            print(
                "CRITICAL: Some original files could not be restored:",
                file=sys.stderr,
            )
            for error in rollback_errors:
                print(f"  - {error}", file=sys.stderr)
            print(
                "Preserve the recovery journal and inspect the files "
                "before attempting another run.",
                file=sys.stderr,
            )
        else:
            print(
                "ERROR: The write or integrity check failed. "
                "Original files were restored.",
                file=sys.stderr,
            )
            print(
                "The recovery journal has been retained for inspection.",
                file=sys.stderr,
            )

        raise






    # Verify the written files before clearing the recovery journal.
    expected_hashes = journal["expected_hashes"]

    for path in targets:
        if sha256_file(path) != expected_hashes[str(path)]:
            raise RuntimeError(
                f"Post-write integrity check failed for {path.name}. "
                "The recovery journal has been retained for investigation."
            )

    # Clear the journal only after all writes and checks succeed.
    JOURNAL_FILE.unlink()


    print("\nSUCCESS")
    print(f"New sales lines: {len(new_sales):,}")
    print(f"Total sales lines: {len(combined_sales):,}")
    print(f"New date dimension rows: {len(new_dates):,}")
    print(f"Backup files: {backup_dir}")
    print("Next step: run the project validation and analytics pipeline.")
    return 0



if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
