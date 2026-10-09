
import csv
import hashlib
import io
import json
import random
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import src.incremental_data_generator as generator
import sys

def csv_bytes(rows, columns):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def file_hash(path):
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestIncrementalRecovery(unittest.TestCase):

    def test_generated_sales_have_valid_financials_and_variation(self):
        customers = generator.read_csv(
            generator.RAW / "dim_customer.csv"
        )
        products = generator.read_csv(
            generator.RAW / "dim_product.csv"
        )

        lines, _, _ = generator.generate_day(
            day=date(2026, 1, 1),
            line_count=45,
            customers=customers,
            products=products,
            rng=random.Random(12345),
            next_sales_number=120001,
            next_order_number=42150,
            fact_date_fmt="%m/%d/%Y",
        )

        self.assertEqual(len(lines), 45)
        self.assertEqual(
            len({row["sales_id"] for row in lines}), 45
        )

        revenues = set()
        quantities = set()
        discounts = set()
        payment_methods = set()
        channels = set()

        for row in lines:
            quantity = int(row["quantity"])
            unit_price = float(row["unit_price"])
            discount_pct = float(row["discount_pct"])
            revenue = float(row["revenue"])
            cost = float(row["cost"])
            profit = float(row["profit"])

            product = next(
                p for p in products
                if p["product_id"] == row["product_id"]
            )

            self.assertEqual(
                revenue,
                round(
                    quantity * unit_price
                    * (1 - discount_pct / 100),
                    2,
                ),
            )
            self.assertEqual(
                cost,
                round(quantity * float(product["unit_cost"]), 2),
            )
            self.assertEqual(profit, round(revenue - cost, 2))

            revenues.add(revenue)
            quantities.add(quantity)
            discounts.add(discount_pct)
            payment_methods.add(row["payment_method"])
            channels.add(row["sales_channel"])

        self.assertGreater(len(revenues), 1)
        self.assertGreater(len(quantities), 1)
        self.assertGreater(len(discounts), 1)
        self.assertGreater(len(payment_methods), 1)
        self.assertGreater(len(channels), 1)

    def test_recovery_restores_pending_transaction(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            raw = Path(temp_dir) / "data" / "raw"
            raw.mkdir(parents=True)

            fact = raw / "fact_sales.csv"
            dates = raw / "dim_date.csv"
            state = raw / "incremental_generator_state.json"
            journal_path = raw / "incremental_generator_pending.json"

            fact.write_text("old sales data\n", encoding="utf-8")
            dates.write_text("old date data\n", encoding="utf-8")

            sales_rows = [
                {column: "" for column in generator.FACT_COLUMNS}
            ]
            sales_rows[0]["sales_id"] = "TEST000001"

            date_rows = [
                {column: "" for column in generator.DATE_COLUMNS}
            ]
            date_rows[0]["date"] = "2026-01-01"

            next_state = {"next_batch_index": 1}

            original_hashes = {
                str(fact): file_hash(fact),
                str(dates): file_hash(dates),
                str(state): file_hash(state),
            }

            expected_hashes = {
                str(fact): hashlib.sha256(
                    csv_bytes(sales_rows, generator.FACT_COLUMNS)
                ).hexdigest(),
                str(dates): hashlib.sha256(
                    csv_bytes(date_rows, generator.DATE_COLUMNS)
                ).hexdigest(),
                str(state): hashlib.sha256(
                    json.dumps(next_state, indent=2).encode("utf-8")
                ).hexdigest(),
            }

            journal = {
                "status": "pending",
                "sales_rows": sales_rows,
                "date_rows": date_rows,
                "next_state": next_state,
                "original_hashes": original_hashes,
                "expected_hashes": expected_hashes,
            }

            journal_path.write_text(
                json.dumps(journal, indent=2),
                encoding="utf-8",
            )

            with (
                patch.object(generator, "FACT_FILE", fact),
                patch.object(generator, "DATE_FILE", dates),
                patch.object(generator, "STATE_FILE", state),
                patch.object(generator, "JOURNAL_FILE", journal_path),
            ):
                result = generator.recover_pending_journal()

            self.assertTrue(result)
            self.assertTrue(state.exists())
            self.assertFalse(journal_path.exists())

            self.assertEqual(
                file_hash(fact), expected_hashes[str(fact)]
            )
            self.assertEqual(
                file_hash(dates), expected_hashes[str(dates)]
            )
            self.assertEqual(
                file_hash(state), expected_hashes[str(state)]
            )


    def test_recovery_rejects_unexpected_file_changes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            raw = Path(temp_dir) / "data" / "raw"
            raw.mkdir(parents=True)

            fact = raw / "fact_sales.csv"
            dates = raw / "dim_date.csv"
            state = raw / "incremental_generator_state.json"
            journal_path = raw / "incremental_generator_pending.json"

            fact.write_bytes(b"unexpected external modification\n")
            dates.write_bytes(b"original date data\n")

            sales_rows = [
                {column: "" for column in generator.FACT_COLUMNS}
            ]
            sales_rows[0]["sales_id"] = "TEST000001"

            date_rows = [
                {column: "" for column in generator.DATE_COLUMNS}
            ]
            date_rows[0]["date"] = "2026-01-01"

            next_state = {"next_batch_index": 1}

            original_hashes = {
                str(fact): hashlib.sha256(
                    b"original sales data\n"
                ).hexdigest(),
                str(dates): file_hash(dates),
                str(state): None,
            }

            expected_hashes = {
                str(fact): hashlib.sha256(
                    csv_bytes(sales_rows, generator.FACT_COLUMNS)
                ).hexdigest(),
                str(dates): hashlib.sha256(
                    csv_bytes(date_rows, generator.DATE_COLUMNS)
                ).hexdigest(),
                str(state): hashlib.sha256(
                    json.dumps(next_state, indent=2).encode("utf-8")
                ).hexdigest(),
            }

            journal = {
                "status": "pending",
                "sales_rows": sales_rows,
                "date_rows": date_rows,
                "next_state": next_state,
                "original_hashes": original_hashes,
                "expected_hashes": expected_hashes,
            }

            journal_path.write_text(
                json.dumps(journal, indent=2),
                encoding="utf-8",
            )

            unexpected_contents = fact.read_bytes()

            with (
                patch.object(generator, "FACT_FILE", fact),
                patch.object(generator, "DATE_FILE", dates),
                patch.object(generator, "STATE_FILE", state),
                patch.object(generator, "JOURNAL_FILE", journal_path),
            ):
                with self.assertRaisesRegex(RuntimeError, "matches neither"):
                    generator.recover_pending_journal()

            self.assertEqual(fact.read_bytes(), unexpected_contents)
            self.assertFalse(state.exists())
            self.assertTrue(journal_path.exists())



    def test_failed_write_restores_original_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            raw = temp / "data" / "raw"
            raw.mkdir(parents=True)

            fact = raw / "fact_sales.csv"
            dates = raw / "dim_date.csv"
            state = raw / "incremental_generator_state.json"
            journal = raw / "incremental_generator_pending.json"
            backups = temp / "data" / "backups"

            # Keep the real dimension files unchanged; only the transaction
            # targets are redirected to temporary files.
            customers = generator.read_csv(
                generator.RAW / "dim_customer.csv"
            )
            products = generator.read_csv(
                generator.RAW / "dim_product.csv"
            )
            regions = generator.read_csv(
                generator.RAW / "dim_region.csv"
            )

            original_fact_rows = generator.read_csv(generator.FACT_FILE)
            original_date_rows = generator.read_csv(generator.DATE_FILE)

            fact.write_bytes(
                csv_bytes(original_fact_rows, generator.FACT_COLUMNS)
            )
            dates.write_bytes(
                csv_bytes(original_date_rows, generator.DATE_COLUMNS)
            )

            original_fact = fact.read_bytes()
            original_dates = dates.read_bytes()
            original_state = None

            real_atomic_write_csv = generator.atomic_write_csv
            csv_write_count = 0

            def fail_on_second_csv_write(path, rows, columns):
                nonlocal csv_write_count
                csv_write_count += 1

                if csv_write_count == 2:
                    raise OSError("Simulated date-dimension write failure")

                return real_atomic_write_csv(path, rows, columns)

            with (
                patch.object(generator, "ROOT", temp),
                patch.object(generator, "RAW", raw),
                patch.object(generator, "FACT_FILE", fact),
                patch.object(generator, "DATE_FILE", dates),
                patch.object(generator, "STATE_FILE", state),
                patch.object(generator, "JOURNAL_FILE", journal),
                patch.object(generator, "BATCH_PATTERN", (3, 3, 3, 4)),
                patch.object(generator, "read_csv") as mock_read_csv,
                patch.object(
                    generator, "atomic_write_csv",
                    side_effect=fail_on_second_csv_write,
                ),
                patch.object(
                    sys, "argv",
                    [
                        "incremental_data_generator.py",
                        "--apply",
                        "--today",
                        "2026-04-01",
                    ],
                ),
            ):
                # Route each CSV read to the correct temporary or dimension
                # table, without changing the real project files.
                def read_table(path):
                    path = Path(path)
                    if path == raw / "dim_customer.csv":
                        return customers
                    if path == raw / "dim_product.csv":
                        return products
                    if path == raw / "dim_region.csv":
                        return regions
                    if path == fact:
                        return original_fact_rows
                    if path == dates:
                        return original_date_rows
                    raise AssertionError(f"Unexpected CSV read: {path}")

                mock_read_csv.side_effect = read_table

                with self.assertRaisesRegex(
                    OSError, "Simulated date-dimension write failure"
                ):
                    generator.main()

            self.assertEqual(csv_write_count, 2)
            self.assertEqual(fact.read_bytes(), original_fact)
            self.assertEqual(dates.read_bytes(), original_dates)
            self.assertFalse(state.exists())
            self.assertTrue(journal.exists())



    def test_main_stops_when_pending_journal_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_journal = Path(temp_dir) / "pending.json"
            fake_journal.write_text(
                '{"status": "pending"}',
                encoding="utf-8",
            )

            with (
                patch.object(
                    generator,
                    "JOURNAL_FILE",
                    fake_journal,
                ),
                patch.object(
                    sys,
                    "argv",
                    ["incremental_data_generator.py"],
                ),
            ):

                result = generator.main()

            self.assertEqual(result, 2)
            self.assertTrue(fake_journal.exists())


if __name__ == "__main__":
    unittest.main()
