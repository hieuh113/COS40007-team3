"""Stage 1 of MLOps Retraining & Monitoring Pipeline: Preprocess incoming new_data.csv.

Validates schema, deduplicates incoming Vegemite batch observations, scales/encodes
features using reference training data, and saves centralized numpy arrays and preprocessing
artifacts under `artifacts/`.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler

ROOT_DIR = Path(__file__).resolve().parent.parent
THEME_SPLIT_DIR = (
    ROOT_DIR / "Theme3" / "Processed_Data"
    if (ROOT_DIR / "Theme3" / "Processed_Data" / "train.csv").is_file()
    else ROOT_DIR.parent / "Theme3" / "Processed_Data"
)
DATA_DIR = ROOT_DIR / "data"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
LOGS_DIR = ROOT_DIR / "logs"

CLASS_NAMES = ["good", "low_bad", "high_bad"]
NON_FEATURE_COLUMNS = {
    "VYP batch",
    "Part",
    "Set Time",
    "quality_class",
    "source_file",
    "source_rows",
    "duplicate_count",
    "split",
    "parsed_time",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def log_message(log_path: Path, message: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [PREPROCESS] {message}"
    print(line)
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_reference_datasets() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    full_train = THEME_SPLIT_DIR / "train.csv"
    full_val = THEME_SPLIT_DIR / "validation.csv"
    if full_train.is_file() and full_val.is_file():
        return pd.read_csv(full_train), pd.read_csv(full_val), "Theme3/Processed_Data (Full Local Split)"
    ci_train = DATA_DIR / "reference_train.csv"
    ci_eval = DATA_DIR / "holdout_eval.csv"
    if ci_train.is_file() and ci_eval.is_file():
        return pd.read_csv(ci_train), pd.read_csv(ci_eval), "data/reference_train.csv (CI Stratified Subset)"
    raise FileNotFoundError("Neither full Theme3 splits nor CI reference datasets found.")


def main() -> None:
    training_log = LOGS_DIR / "training.log"
    monitoring_log = LOGS_DIR / "monitoring.log"

    train_df, test_df, source_mode = load_reference_datasets()
    new_data_path = DATA_DIR / "new_data.csv"
    if not new_data_path.is_file():
        raise FileNotFoundError(f"Incoming data file not found: {new_data_path}")
    new_df = pd.read_csv(new_data_path)

    feature_columns = [c for c in train_df.columns if c not in NON_FEATURE_COLUMNS]
    if not feature_columns:
        raise ValueError("No numeric process features found in reference training dataset.")

    # Schema & data quality check on incoming new_data.csv
    missing_cols = [c for c in feature_columns if c not in new_df.columns]
    if missing_cols:
        raise ValueError(f"Incoming new_data.csv is missing required feature columns: {missing_cols}")

    before_dedup = len(new_df)
    new_df = new_df.drop_duplicates(subset=[*feature_columns, "quality_class"] if "quality_class" in new_df.columns else feature_columns).reset_index(drop=True)
    duplicates_removed = before_dedup - len(new_df)

    x_train_raw = train_df[feature_columns].apply(pd.to_numeric, errors="coerce")
    x_test_raw = test_df[feature_columns].apply(pd.to_numeric, errors="coerce")
    x_new_raw = new_df[feature_columns].apply(pd.to_numeric, errors="coerce")

    missing_in_new = int(x_new_raw.isna().sum().sum())
    if missing_in_new > 0:
        medians = x_train_raw.median()
        x_new_raw = x_new_raw.fillna(medians)

    # Fit scaler and encoder on reference training data only
    scaler = StandardScaler()
    scaler.fit(x_train_raw.to_numpy(dtype=float))

    encoder = LabelEncoder()
    encoder.fit(CLASS_NAMES)

    y_train = encoder.transform(train_df["quality_class"].to_numpy())
    y_test = encoder.transform(test_df["quality_class"].to_numpy())
    y_new = (
        encoder.transform(new_df["quality_class"].to_numpy())
        if "quality_class" in new_df.columns
        else np.full(len(new_df), -1, dtype=int)
    )

    # Create centralized artifact directories matching Studio 9 specification
    data_art_dir = ARTIFACTS_DIR / "data"
    prep_art_dir = ARTIFACTS_DIR / "preprocessing"
    meta_art_dir = ARTIFACTS_DIR / "metadata"
    for d in (data_art_dir, prep_art_dir, meta_art_dir):
        d.mkdir(parents=True, exist_ok=True)

    np.save(data_art_dir / "X_train.npy", x_train_raw.to_numpy(dtype=float))
    np.save(data_art_dir / "y_train.npy", y_train)
    np.save(data_art_dir / "X_test.npy", x_test_raw.to_numpy(dtype=float))
    np.save(data_art_dir / "y_test.npy", y_test)
    np.save(data_art_dir / "X_new.npy", x_new_raw.to_numpy(dtype=float))
    np.save(data_art_dir / "y_new.npy", y_new)

    (prep_art_dir / "feature_columns.json").write_text(
        json.dumps(
            {
                "feature_count": len(feature_columns),
                "feature_columns": feature_columns,
                "setpoint_columns": [c for c in feature_columns if c.endswith(" SP")],
                "sensor_pv_columns": [c for c in feature_columns if not c.endswith(" SP")],
                "class_names": list(encoder.classes_),
                "source_mode": source_mode,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    joblib.dump(scaler, prep_art_dir / "scaler.pkl")
    joblib.dump(encoder, prep_art_dir / "encoder.pkl")

    new_sha = sha256_file(new_data_path)[:12]
    data_version = f"v1.0.{new_sha} ({len(train_df) + len(new_df)} total rows)"
    (meta_art_dir / "data_version.txt").write_text(data_version + "\n", encoding="utf-8")

    log_message(
        training_log,
        f"Loaded {source_mode}: train={len(train_df)} rows, eval={len(test_df)} rows, new_data={len(new_df)} rows "
        f"(deduplicated={duplicates_removed}, missing_imputed={missing_in_new}).",
    )
    log_message(
        monitoring_log,
        f"Data version updated to {data_version}. Saved X_train.npy, y_train.npy, X_test.npy, y_test.npy, X_new.npy.",
    )


if __name__ == "__main__":
    main()
