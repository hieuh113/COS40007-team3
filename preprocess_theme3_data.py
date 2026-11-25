"""Build reproducible, batch-safe, chronological Theme 3 data splits."""

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
THEME_DIR = PROJECT_DIR / "Theme3" if (PROJECT_DIR / "Theme3" / "data_02_07_2019-26-06-2020").exists() else PROJECT_DIR.parent / "Theme3"
DATA_DIR = THEME_DIR / "data_02_07_2019-26-06-2020"
OUTPUT_DIR = THEME_DIR / "Processed_Data"
CLASS_FILES = {
    "good": DATA_DIR / "good.csv",
    "low_bad": DATA_DIR / "low bad.csv",
    "high_bad": DATA_DIR / "high bad.csv",
}
TIME_FORMAT = "%d/%m/%Y %H:%M"
SPLIT_TARGETS = (0.70, 0.85)
METADATA_COLUMNS = {"VYP batch", "Part", "Set Time"}
PROVENANCE_COLUMNS = {"source_file", "source_rows", "duplicate_count", "quality_class", "split"}


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        return list(reader), reader.fieldnames


def parse_time(value: str) -> datetime:
    try:
        return datetime.strptime(value, TIME_FORMAT)
    except ValueError as error:
        raise ValueError(f"Invalid Set Time value: {value!r}") from error


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_deduplicated_rows(columns: list[str]) -> tuple[list[dict[str, str]], dict[str, dict[str, int]]]:
    unique_rows: list[dict[str, str]] = []
    duplicate_stats: dict[str, dict[str, int]] = {}

    for label, path in CLASS_FILES.items():
        rows, file_columns = read_csv(path)
        if file_columns != columns:
            raise ValueError(f"Unexpected schema in {path}")
        grouped: dict[tuple[str, ...], dict[str, object]] = {}
        for source_row_number, row in enumerate(rows, start=2):
            signature = tuple(row[column] for column in columns)
            record = grouped.get(signature)
            if record is None:
                record = {"row": row.copy(), "source_rows": []}
                grouped[signature] = record
            record["source_rows"].append(source_row_number)

        duplicate_groups = sum(len(record["source_rows"]) > 1 for record in grouped.values())
        duplicate_excess = sum(len(record["source_rows"]) - 1 for record in grouped.values())
        duplicate_stats[label] = {
            "source_rows": len(rows),
            "unique_rows": len(grouped),
            "duplicate_groups": duplicate_groups,
            "duplicate_excess": duplicate_excess,
        }

        for record in grouped.values():
            row = record["row"]
            unique_rows.append(
                {
                    **row,
                    "quality_class": label,
                    "source_file": path.relative_to(THEME_DIR.parent).as_posix(),
                    "source_rows": ";".join(map(str, record["source_rows"])),
                    "duplicate_count": str(len(record["source_rows"])),
                }
            )

    return unique_rows, duplicate_stats


def make_batch_splits(rows: list[dict[str, str]]) -> tuple[dict[str, str], dict[str, object]]:
    batch_labels: dict[str, set[str]] = defaultdict(set)
    batch_times: dict[str, list[datetime]] = defaultdict(list)
    for row in rows:
        batch = row["VYP batch"]
        batch_labels[batch].add(row["quality_class"])
        batch_times[batch].append(parse_time(row["Set Time"]))

    conflicts = {batch: sorted(labels) for batch, labels in batch_labels.items() if len(labels) != 1}
    if conflicts:
        raise ValueError(f"Conflicting batches must be quarantined before splitting: {conflicts}")

    ordered_batches = sorted(
        batch_times,
        key=lambda batch: (min(batch_times[batch]), batch),
    )
    batch_count = len(ordered_batches)
    if batch_count < 3:
        raise ValueError("At least three batches are required for train/validation/test splits")

    prefix_end: list[datetime] = []
    running_end: datetime | None = None
    for batch in ordered_batches:
        batch_end = max(batch_times[batch])
        running_end = batch_end if running_end is None else max(running_end, batch_end)
        prefix_end.append(running_end)

    suffix_start: list[datetime] = [min(batch_times[batch]) for batch in ordered_batches]
    for index in range(batch_count - 2, -1, -1):
        suffix_start[index] = min(suffix_start[index], suffix_start[index + 1])

    safe_cuts = [
        index
        for index in range(1, batch_count)
        if prefix_end[index - 1] < suffix_start[index]
    ]
    target_train = round(batch_count * SPLIT_TARGETS[0])
    target_train_validation = round(batch_count * SPLIT_TARGETS[1])
    candidates = [
        (first, second)
        for first in safe_cuts
        for second in safe_cuts
        if first < second
    ]
    if not candidates:
        raise ValueError("No non-overlapping chronological batch boundaries were found")
    first_cut, second_cut = min(
        candidates,
        key=lambda cuts: (
            abs(cuts[0] - target_train) + abs(cuts[1] - target_train_validation),
            abs(cuts[0] - target_train),
            cuts,
        ),
    )

    split_by_batch = {
        batch: "train" if index < first_cut else "validation" if index < second_cut else "test"
        for index, batch in enumerate(ordered_batches)
    }
    boundary_info = {
        "batch_order": "ascending earliest Set Time; each batch remains intact",
        "target_proportions_by_batch": {"train": 0.70, "validation": 0.15, "test": 0.15},
        "safe_boundaries_available": len(safe_cuts),
        "train_validation_gap": {
            "train_latest": prefix_end[first_cut - 1].isoformat(sep=" "),
            "validation_earliest": suffix_start[first_cut].isoformat(sep=" "),
        },
        "validation_test_gap": {
            "validation_latest": prefix_end[second_cut - 1].isoformat(sep=" "),
            "test_earliest": suffix_start[second_cut].isoformat(sep=" "),
        },
        "batch_counts": {
            "train": first_cut,
            "validation": second_cut - first_cut,
            "test": batch_count - second_cut,
        },
    }
    return split_by_batch, boundary_info


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def summarize_rows(rows: list[dict[str, str]]) -> dict[str, object]:
    labels = Counter(row["quality_class"] for row in rows)
    times = [parse_time(row["Set Time"]) for row in rows]
    return {
        "rows": len(rows),
        "batches": len({row["VYP batch"] for row in rows}),
        "class_rows": dict(sorted(labels.items())),
        "set_time_min": min(times).isoformat(sep=" ") if times else None,
        "set_time_max": max(times).isoformat(sep=" ") if times else None,
    }


def main() -> None:
    source_rows, columns = read_csv(CLASS_FILES["good"])
    del source_rows
    unique_rows, duplicate_stats = load_deduplicated_rows(columns)

    labels_by_batch: dict[str, set[str]] = defaultdict(set)
    for row in unique_rows:
        labels_by_batch[row["VYP batch"]].add(row["quality_class"])
    conflicting_batches = {
        batch: sorted(labels)
        for batch, labels in labels_by_batch.items()
        if len(labels) > 1
    }
    conflict_batch_names = set(conflicting_batches)
    quarantined_rows = [
        {**row, "quarantine_reason": "Conflicting class labels at batch level; needs independent confirmation"}
        for row in unique_rows
        if row["VYP batch"] in conflict_batch_names
    ]
    eligible_rows = [row for row in unique_rows if row["VYP batch"] not in conflict_batch_names]

    log_rows, _ = read_csv(DATA_DIR / "output_log.csv")
    log_labels_by_batch: dict[str, set[str]] = defaultdict(set)
    for row in log_rows:
        log_labels_by_batch[row["VYP batch"]].add(row["Run"])
    source_labels_by_batch: dict[str, set[str]] = defaultdict(set)
    for row in unique_rows:
        source_labels_by_batch[row["VYP batch"]].add(row["quality_class"])
    log_mismatches = {
        batch: {"source": sorted(labels), "output_log": sorted(log_labels_by_batch.get(batch, set()))}
        for batch, labels in source_labels_by_batch.items()
        if labels != log_labels_by_batch.get(batch, set())
    }
    if log_mismatches:
        raise ValueError(f"output_log label sets differ from source class files: {log_mismatches}")

    split_by_batch, boundary_info = make_batch_splits(eligible_rows)
    split_rows: dict[str, list[dict[str, str]]] = {"train": [], "validation": [], "test": []}
    for row in eligible_rows:
        split = split_by_batch[row["VYP batch"]]
        split_rows[split].append({**row, "split": split})

    split_fieldnames = [*columns, "quality_class", "source_file", "source_rows", "duplicate_count", "split"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for split, rows in split_rows.items():
        rows.sort(key=lambda row: (parse_time(row["Set Time"]), row["VYP batch"], row["source_file"], row["source_rows"]))
        write_csv(OUTPUT_DIR / f"{split}.csv", split_fieldnames, rows)
    quarantine_fieldnames = [*split_fieldnames[:-1], "quarantine_reason"]
    write_csv(OUTPUT_DIR / "quarantine_conflicting_batches.csv", quarantine_fieldnames, quarantined_rows)

    batch_rows = []
    split_by_batch_info: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in eligible_rows:
        split_by_batch_info[row["VYP batch"]].append(row)
    for batch, rows in split_by_batch_info.items():
        times = [parse_time(row["Set Time"]) for row in rows]
        batch_rows.append(
            {
                "VYP batch": batch,
                "quality_class": rows[0]["quality_class"],
                "split": split_by_batch[batch],
                "Set Time min": min(times).isoformat(sep=" "),
                "Set Time max": max(times).isoformat(sep=" "),
                "deduplicated_rows": str(len(rows)),
            }
        )
    batch_rows.sort(key=lambda row: (row["Set Time min"], row["VYP batch"]))
    write_csv(
        OUTPUT_DIR / "batch_split_manifest.csv",
        ["VYP batch", "quality_class", "split", "Set Time min", "Set Time max", "deduplicated_rows"],
        batch_rows,
    )

    feature_columns = [column for column in columns if column not in METADATA_COLUMNS]
    total_source_rows = sum(result["source_rows"] for result in duplicate_stats.values())
    manifest = {
        "source_files_sha256": {path.name: sha256(path) for path in [*CLASS_FILES.values(), DATA_DIR / "output_log.csv"]},
        "source_files_modified": False,
        "source_rows": total_source_rows,
        "deduplication": duplicate_stats,
        "duplicate_excess_total": sum(result["duplicate_excess"] for result in duplicate_stats.values()),
        "unique_rows_before_quarantine": len(unique_rows),
        "quarantined_batches": conflicting_batches,
        "quarantined_rows": summarize_rows(quarantined_rows),
        "eligible_rows": len(eligible_rows),
        "split_policy": boundary_info,
        "splits": {split: summarize_rows(rows) for split, rows in split_rows.items()},
        "output_log_check": {
            "rows": len(log_rows),
            "unique_batches": len(log_labels_by_batch),
            "label_set_mismatches": log_mismatches,
            "resolves_conflicts": False if conflicting_batches else True,
        },
        "model_input_policy": {
            "feature_candidates": feature_columns,
            "excluded_metadata": sorted(METADATA_COLUMNS),
            "imputation": "Not fitted: source feature cells are complete; if needed later, fit on train only.",
            "categorical_encoding": "Not applied: Part is retained as metadata and excluded pending availability confirmation.",
            "scaling": "Not fitted in this split builder; any scaler must be fit on train only in the model pipeline.",
            "class_imbalance": "No resampling or weighting in this builder; any balancing must use training rows only.",
            "future_readings": "Rows use their recorded values only; no later same-batch observations are aggregated.",
        },
    }
    (OUTPUT_DIR / "preprocessing_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()