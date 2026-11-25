"""Read-only audit for the Theme 3 quality-label CSV files."""

import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
THEME_DIR = PROJECT_DIR / "Theme3" if (PROJECT_DIR / "Theme3" / "data_02_07_2019-26-06-2020").exists() else PROJECT_DIR.parent / "Theme3"
DATA_DIR = THEME_DIR / "data_02_07_2019-26-06-2020"
CLASS_FILES = {
    "good": DATA_DIR / "good.csv",
    "low_bad": DATA_DIR / "low bad.csv",
    "high_bad": DATA_DIR / "high bad.csv",
}
TIME_FORMATS = ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S")


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        return list(reader), reader.fieldnames


def parse_set_time(value: str) -> datetime | None:
    for date_format in TIME_FORMATS:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue
    return None


def audit_class(label: str, path: Path) -> tuple[dict[str, object], list[dict[str, str]]]:
    rows, columns = read_csv(path)
    counts = Counter(tuple(row.get(column, "") for column in columns) for row in rows)
    duplicate_groups = sum(count > 1 for count in counts.values())
    duplicate_excess = sum(count - 1 for count in counts.values())
    blank_by_column = {
        column: sum(not (row.get(column) or "").strip() for row in rows)
        for column in columns
    }
    numeric_errors: Counter[str] = Counter()
    non_finite: Counter[str] = Counter()
    timestamps: list[datetime] = []
    invalid_timestamps = 0

    for row in rows:
        timestamp = parse_set_time(row.get("Set Time", ""))
        if timestamp is None:
            invalid_timestamps += 1
        else:
            timestamps.append(timestamp)

        for column in columns[3:]:
            value = (row.get(column) or "").strip()
            if not value:
                continue
            try:
                numeric_value = float(value)
            except ValueError:
                numeric_errors[column] += 1
                continue
            if not math.isfinite(numeric_value):
                non_finite[column] += 1

    result = {
        "label": label,
        "file": path.relative_to(THEME_DIR.parent).as_posix(),
        "rows": len(rows),
        "columns": len(columns),
        "batch_count": len({row.get("VYP batch", "") for row in rows}),
        "parts": sorted({row.get("Part", "") for row in rows}),
        "duplicate_groups": duplicate_groups,
        "duplicate_excess": duplicate_excess,
        "blank_cells": sum(blank_by_column.values()),
        "blank_by_column": {key: value for key, value in blank_by_column.items() if value},
        "invalid_set_time": invalid_timestamps,
        "set_time_min": min(timestamps).isoformat(sep=" ") if timestamps else None,
        "set_time_max": max(timestamps).isoformat(sep=" ") if timestamps else None,
        "numeric_parse_errors": dict(numeric_errors),
        "non_finite_numeric_values": dict(non_finite),
        "sp_columns": [column for column in columns if column.endswith(" SP")],
        "columns_list": columns,
    }
    return result, rows


def main() -> None:
    class_results: list[dict[str, object]] = []
    labels_by_signature: dict[tuple[str, ...], set[str]] = defaultdict(set)
    labels_by_batch: dict[str, set[str]] = defaultdict(set)
    source_batches: set[str] = set()
    source_columns: list[str] | None = None

    for label, path in CLASS_FILES.items():
        result, rows = audit_class(label, path)
        class_results.append(result)
        columns = result["columns_list"]
        if source_columns is None:
            source_columns = columns
        elif columns != source_columns:
            raise ValueError(f"Column mismatch in {path}")
        for row in rows:
            signature = tuple(row.get(column, "") for column in columns)
            batch = row.get("VYP batch", "")
            labels_by_signature[signature].add(label)
            labels_by_batch[batch].add(label)
            source_batches.add(batch)

    output_log_path = DATA_DIR / "output_log.csv"
    output_log, _ = read_csv(output_log_path)
    log_labels_by_batch: dict[str, set[str]] = defaultdict(set)
    for row in output_log:
        log_labels_by_batch[row.get("VYP batch", "")].add(row.get("Run", ""))

    conflicting_batches = {
        batch: sorted(labels)
        for batch, labels in labels_by_batch.items()
        if len(labels) > 1
    }
    log_disagreements = {
        batch: {
            "class_files": sorted(labels),
            "output_log": sorted(log_labels_by_batch.get(batch, set())),
        }
        for batch, labels in labels_by_batch.items()
        if labels != log_labels_by_batch.get(batch, set())
    }
    cross_label_rows = sum(len(labels) > 1 for labels in labels_by_signature.values())
    missing_log_batches = sorted(source_batches - set(log_labels_by_batch))
    extra_log_batches = sorted(set(log_labels_by_batch) - source_batches)

    report = {
        "data_directory": DATA_DIR.relative_to(THEME_DIR.parent).as_posix(),
        "source_files_modified": False,
        "class_rows_total": sum(int(item["rows"]) for item in class_results),
        "class_results": class_results,
        "class_row_percentages": {
            str(item["label"]): round(int(item["rows"]) / sum(int(result["rows"]) for result in class_results) * 100, 2)
            for item in class_results
        },
        "unique_source_batches": len(source_batches),
        "identical_full_rows_in_multiple_class_files": cross_label_rows,
        "conflicting_label_batches": conflicting_batches,
        "output_log": {
            "rows": len(output_log),
            "unique_batches": len(log_labels_by_batch),
            "duplicate_rows": len(output_log) - len(log_labels_by_batch),
            "missing_source_batches": missing_log_batches,
            "extra_batches": extra_log_batches,
            "conflicting_batches": {
                batch: sorted(labels)
                for batch, labels in log_labels_by_batch.items()
                if len(labels) > 1
            },
            "resolves_source_label_conflicts": not bool(conflicting_batches),
            "label_disagreements": log_disagreements,
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()