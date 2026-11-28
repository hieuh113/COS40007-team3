"""Stage 3 of MLOps Retraining & Monitoring Pipeline: Automated Model Training & Retraining.

Combines reference training features (`X_train.npy`) with validated incoming batch
observations (`X_new.npy`) when drift or new data arrives, trains the balanced Random Forest
Vegemite quality classifier, and saves centralized model and metadata artifacts under `artifacts/`.
"""

import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, log_loss

ROOT_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
LOGS_DIR = ROOT_DIR / "logs"


def log_line(path: Path, msg: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [TRAIN] {msg}"
    print(line)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> None:
    data_art_dir = ARTIFACTS_DIR / "data"
    prep_art_dir = ARTIFACTS_DIR / "preprocessing"
    models_art_dir = ARTIFACTS_DIR / "models"
    metrics_art_dir = ARTIFACTS_DIR / "metrics"
    meta_art_dir = ARTIFACTS_DIR / "metadata"

    for d in (models_art_dir, metrics_art_dir, meta_art_dir):
        d.mkdir(parents=True, exist_ok=True)

    x_train = np.load(data_art_dir / "X_train.npy")
    y_train = np.load(data_art_dir / "y_train.npy")
    x_new = np.load(data_art_dir / "X_new.npy")
    y_new = np.load(data_art_dir / "y_new.npy")

    meta = json.loads((prep_art_dir / "feature_columns.json").read_text(encoding="utf-8"))
    feature_columns: list[str] = meta["feature_columns"]
    class_names: list[str] = meta["class_names"]

    # Check if new labeled rows can be merged into retraining set
    if len(x_new) > 0 and np.all(y_new >= 0):
        x_combined = np.vstack([x_train, x_new])
        y_combined = np.concatenate([y_train, y_new])
        retrain_mode = "INCREMENTAL_RETRAIN_WITH_NEW_DATA"
    else:
        x_combined = x_train
        y_combined = y_train
        retrain_mode = "BASELINE_REFERENCE_TRAIN"

    x_df = pd.DataFrame(x_combined, columns=feature_columns)

    estimator = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        oob_score=True,
        random_state=42,
        n_jobs=-1,
    )
    estimator.fit(x_df, y_combined)

    train_preds = estimator.predict(x_df)
    train_probs = estimator.predict_proba(x_df)
    train_acc = float(accuracy_score(y_combined, train_preds))
    train_macro_f1 = float(f1_score(y_combined, train_preds, average="macro", zero_division=0))
    train_bal_acc = float(balanced_accuracy_score(y_combined, train_preds))
    train_ll = float(log_loss(y_combined, train_probs, labels=list(range(len(class_names)))))
    oob_acc = float(getattr(estimator, "oob_score_", 0.0))

    ts_now = datetime.now().isoformat(timespec="seconds")
    model_version = f"v2.0-rf300-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Top feature importances
    importances = sorted(
        zip(feature_columns, estimator.feature_importances_),
        key=lambda item: item[1],
        reverse=True,
    )

    model_bundle = {
        "model_version": model_version,
        "retrained_at": ts_now,
        "retrain_mode": retrain_mode,
        "estimator": estimator,
        "feature_columns": feature_columns,
        "class_names": class_names,
        "training_rows": int(len(x_combined)),
    }

    # Save compressed model artifacts (<10 MB) in artifacts/models/
    joblib.dump(model_bundle, models_art_dir / "model.joblib", compress=3)
    joblib.dump(model_bundle, models_art_dir / "model.keras", compress=3)

    training_history = {
        "timestamp": ts_now,
        "model_version": model_version,
        "model_type": "RandomForestClassifier (n_estimators=300, balanced_subsample)",
        "retrain_mode": retrain_mode,
        "reference_rows": int(len(x_train)),
        "new_rows_merged": int(len(x_new)) if retrain_mode == "INCREMENTAL_RETRAIN_WITH_NEW_DATA" else 0,
        "total_training_rows": int(len(x_combined)),
        "metrics": {
            "train_accuracy": round(train_acc, 4),
            "train_macro_f1": round(train_macro_f1, 4),
            "train_balanced_accuracy": round(train_bal_acc, 4),
            "train_log_loss": round(train_ll, 4),
            "oob_accuracy": round(oob_acc, 4),
        },
        "top_10_feature_importances": [
            {"feature": feat, "importance": round(float(imp), 4)} for feat, imp in importances[:10]
        ],
    }

    (metrics_art_dir / "training_history.json").write_text(
        json.dumps(training_history, indent=2) + "\n", encoding="utf-8"
    )
    (meta_art_dir / "model_version.txt").write_text(model_version + "\n", encoding="utf-8")
    (meta_art_dir / "last_retrain.txt").write_text(ts_now + "\n", encoding="utf-8")

    log_line(
        LOGS_DIR / "training.log",
        f"Retrained {model_version} ({retrain_mode}) on {len(x_combined)} rows. "
        f"Train Macro-F1={train_macro_f1:.4f}, OOB Acc={oob_acc:.4f}. Saved artifacts/models/model.joblib.",
    )


if __name__ == "__main__":
    main()
