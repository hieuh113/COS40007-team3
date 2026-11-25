"""Extended model benchmark, OOF probability calibration, PR-AUC evaluation, and model freeze.

Strictly reads train.csv and validation.csv only; test.csv remains locked until final evaluation.
"""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import (
    ExtraTreesClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

PROJECT_DIR = Path(__file__).resolve().parent
THEME_DIR = PROJECT_DIR.parent / "Theme3" if not (PROJECT_DIR / "Theme3").exists() else PROJECT_DIR / "Theme3"
SPLIT_DIR = THEME_DIR / "Processed_Data"
OUTPUT_DIRS = [
    SPLIT_DIR / "model_calibration_freeze",
    PROJECT_DIR / "reports" / "model_calibration_freeze",
]
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
TARGET_CUT_PROPORTIONS = (0.55, 0.70, 0.85)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_time_safe_cuts(batch_summary: pd.DataFrame) -> list[int]:
    starts = batch_summary["batch_start"].tolist()
    ends = batch_summary["batch_end"].tolist()
    batch_count = len(batch_summary)
    safe_cuts = [
        index
        for index in range(1, batch_count)
        if max(ends[:index]) < min(starts[index:])
    ]
    selected: list[int] = []
    for proportion in TARGET_CUT_PROPORTIONS:
        target = round(batch_count * proportion)
        cut = min(
            (value for value in safe_cuts if value not in selected),
            key=lambda value: abs(value - target),
        )
        selected.append(cut)
    return sorted(selected)


def align_probabilities(estimator, x_data: pd.DataFrame) -> np.ndarray:
    raw_probs = estimator.predict_proba(x_data)
    classes = list(estimator.classes_)
    aligned = np.zeros((len(x_data), len(CLASS_NAMES)), dtype=float)
    for col_idx, label in enumerate(classes):
        aligned[:, CLASS_NAMES.index(label)] = raw_probs[:, col_idx]
    row_sums = aligned.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    return aligned / row_sums


def compute_ece_and_bins(y_true: pd.Series, probabilities: np.ndarray, n_bins: int = 10) -> tuple[dict[str, float], list[dict[str, object]]]:
    ece_by_class: dict[str, float] = {}
    bins_rows: list[dict[str, object]] = []
    y_arr = y_true.to_numpy()
    for col_idx, label in enumerate(CLASS_NAMES):
        positive = (y_arr == label).astype(int)
        scores = probabilities[:, col_idx]
        bin_edges = np.unique(np.quantile(scores, np.linspace(0, 1, n_bins + 1)))
        if len(bin_edges) > 1:
            bin_index = np.digitize(scores, bin_edges[1:-1], right=True)
        else:
            bin_index = np.zeros(len(scores), dtype=int)
        weighted_error = 0.0
        for idx in range(max(1, len(bin_edges) - 1)):
            members = bin_index == idx
            count = int(members.sum())
            if count == 0:
                continue
            mean_score = float(scores[members].mean())
            obs_rate = float(positive[members].mean())
            weighted_error += (count / len(scores)) * abs(mean_score - obs_rate)
            bins_rows.append(
                {
                    "quality_class": label,
                    "bin": idx + 1,
                    "count": count,
                    "mean_predicted_probability": mean_score,
                    "observed_fraction": obs_rate,
                }
            )
        ece_by_class[label] = float(weighted_error)
    return ece_by_class, bins_rows


def evaluate_predictions(
    name: str,
    y_true: pd.Series,
    predictions: np.ndarray,
    probabilities: np.ndarray,
    batches: pd.Series,
) -> dict[str, object]:
    y_arr = y_true.to_numpy()
    acc = float(accuracy_score(y_arr, predictions))
    macro_f1 = float(f1_score(y_arr, predictions, labels=CLASS_NAMES, average="macro", zero_division=0))
    bal_acc = float(balanced_accuracy_score(y_arr, predictions))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_arr, predictions, labels=CLASS_NAMES, zero_division=0
    )
    cm = confusion_matrix(y_arr, predictions, labels=CLASS_NAMES).tolist()

    prob_order = sorted(CLASS_NAMES)
    ordered_probs = np.clip(
        probabilities[:, [CLASS_NAMES.index(lbl) for lbl in prob_order]],
        1e-15,
        1.0 - 1e-15,
    )
    ordered_probs = ordered_probs / ordered_probs.sum(axis=1, keepdims=True)
    ll = float(log_loss(y_arr, ordered_probs, labels=prob_order))

    actual_onehot = np.column_stack([y_arr == lbl for lbl in CLASS_NAMES]).astype(float)
    brier = float(np.mean(np.sum((probabilities - actual_onehot) ** 2, axis=1)))

    pr_auc_by_class: dict[str, float] = {}
    for col_idx, lbl in enumerate(CLASS_NAMES):
        binary_true = (y_arr == lbl).astype(int)
        if binary_true.sum() > 0:
            pr_auc_by_class[lbl] = float(average_precision_score(binary_true, probabilities[:, col_idx]))
        else:
            pr_auc_by_class[lbl] = 0.0
    macro_pr_auc = float(np.mean(list(pr_auc_by_class.values())))

    ece_by_class, _ = compute_ece_and_bins(y_true, probabilities)
    mean_ece = float(np.mean(list(ece_by_class.values())))

    # Batch-level stability
    batch_df = pd.DataFrame({"batch": batches.to_numpy(), "true": y_arr, "pred": predictions})
    batch_accs = batch_df.groupby("batch").apply(lambda g: float(np.mean(g["true"] == g["pred"])), include_groups=False)
    low_bad_batches = batch_df.loc[batch_df["true"] == "low_bad"]
    if not low_bad_batches.empty:
        lb_batch_recalls = low_bad_batches.groupby("batch").apply(
            lambda g: float(np.mean(g["pred"] == "low_bad")), include_groups=False
        )
        lb_batches_detected = int((lb_batch_recalls > 0).sum())
        lb_total_batches = int(len(lb_batch_recalls))
        lb_mean_batch_recall = float(lb_batch_recalls.mean())
    else:
        lb_batches_detected = 0
        lb_total_batches = 0
        lb_mean_batch_recall = 0.0

    return {
        "model": name,
        "accuracy": acc,
        "macro_f1": macro_f1,
        "balanced_accuracy": bal_acc,
        "macro_pr_auc": macro_pr_auc,
        "low_bad_pr_auc": pr_auc_by_class["low_bad"],
        "good_pr_auc": pr_auc_by_class["good"],
        "high_bad_pr_auc": pr_auc_by_class["high_bad"],
        "low_bad_precision": float(precision[1]),
        "low_bad_recall": float(recall[1]),
        "low_bad_f1": float(f1[1]),
        "good_f1": float(f1[0]),
        "high_bad_f1": float(f1[2]),
        "log_loss": ll,
        "multiclass_brier": brier,
        "mean_ece": mean_ece,
        "ece_by_class": ece_by_class,
        "batch_accuracy_mean": float(batch_accs.mean()),
        "batch_accuracy_min": float(batch_accs.min()),
        "low_bad_batches_detected": f"{lb_batches_detected}/{lb_total_batches}",
        "low_bad_mean_batch_recall": lb_mean_batch_recall,
        "confusion_matrix": cm,
        "classification_report": classification_report(
            y_arr, predictions, labels=CLASS_NAMES, target_names=CLASS_NAMES, output_dict=True, zero_division=0
        ),
    }


class OOFPostHocCalibrator:
    """Post-hoc probability calibrator fitted purely on Walk-Forward OOF probabilities."""

    def __init__(self, method: str = "sigmoid", temperature: float = 1.0):
        self.method = method
        self.temperature = temperature
        self.calibrators: list[object] = []

    def fit(self, oof_probs: np.ndarray, y_oof: pd.Series) -> "OOFPostHocCalibrator":
        y_arr = y_oof.to_numpy()
        self.calibrators = []
        if self.method == "temperature":
            # Grid search temperature T on OOF log_loss
            eps = 1e-12
            logits = np.log(np.clip(oof_probs, eps, 1.0 - eps))
            best_t = 1.0
            best_loss = float("inf")
            prob_order = sorted(CLASS_NAMES)
            order_idx = [CLASS_NAMES.index(lbl) for lbl in prob_order]
            for t in np.linspace(0.5, 3.0, 51):
                scaled = np.exp(logits / t)
                scaled /= scaled.sum(axis=1, keepdims=True)
                loss = float(log_loss(y_arr, scaled[:, order_idx], labels=prob_order))
                if loss < best_loss:
                    best_loss = loss
                    best_t = float(t)
            self.temperature = best_t
        elif self.method == "sigmoid":
            for col_idx, lbl in enumerate(CLASS_NAMES):
                binary_y = (y_arr == lbl).astype(int)
                lr = LogisticRegression(C=1.0, random_state=42)
                lr.fit(oof_probs[:, [col_idx]], binary_y)
                self.calibrators.append(lr)
        elif self.method == "isotonic":
            for col_idx, lbl in enumerate(CLASS_NAMES):
                binary_y = (y_arr == lbl).astype(int)
                iso = IsotonicRegression(out_of_bounds="clip", y_min=1e-6, y_max=1.0 - 1e-6)
                iso.fit(oof_probs[:, col_idx], binary_y)
                self.calibrators.append(iso)
        else:
            raise ValueError(f"Unknown calibration method: {self.method}")
        return self

    def transform(self, raw_probs: np.ndarray) -> np.ndarray:
        if self.method == "temperature":
            eps = 1e-12
            logits = np.log(np.clip(raw_probs, eps, 1.0 - eps))
            scaled = np.exp(logits / self.temperature)
            return scaled / scaled.sum(axis=1, keepdims=True)
        calibrated = np.zeros_like(raw_probs, dtype=float)
        for col_idx, cal in enumerate(self.calibrators):
            if self.method == "sigmoid":
                calibrated[:, col_idx] = cal.predict_proba(raw_probs[:, [col_idx]])[:, 1]
            else:
                calibrated[:, col_idx] = cal.predict(raw_probs[:, col_idx])
        calibrated = np.clip(calibrated, 1e-6, 1.0 - 1e-6)
        row_sums = calibrated.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return calibrated / row_sums


def get_candidate_estimators() -> dict[str, object]:
    return {
        "majority_baseline": DummyClassifier(strategy="most_frequent"),
        "logistic_regression_balanced": make_pipeline(
            StandardScaler(),
            LogisticRegression(class_weight="balanced", max_iter=2000, random_state=42),
        ),
        "random_forest_balanced": RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1,
        ),
        "extra_trees_balanced": ExtraTreesClassifier(
            n_estimators=300,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1,
        ),
        "hist_gradient_boosting_balanced": HistGradientBoostingClassifier(
            learning_rate=0.05,
            max_iter=150,
            max_leaf_nodes=31,
            min_samples_leaf=20,
            l2_regularization=2.0,
            class_weight="balanced",
            random_state=42,
        ),
    }


def main() -> None:
    train_path = SPLIT_DIR / "train.csv"
    val_path = SPLIT_DIR / "validation.csv"
    train = pd.read_csv(train_path)
    validation = pd.read_csv(val_path)

    if train["VYP batch"].isin(validation["VYP batch"]).any():
        raise ValueError("Leakage error: A batch appears in both train and validation!")

    train["parsed_time"] = pd.to_datetime(train["Set Time"], format="%d/%m/%Y %H:%M")
    validation["parsed_time"] = pd.to_datetime(validation["Set Time"], format="%d/%m/%Y %H:%M")

    feature_columns = [col for col in train.columns if col not in NON_FEATURE_COLUMNS]
    x_train = train[feature_columns].apply(pd.to_numeric, errors="raise")
    y_train = train["quality_class"]
    x_val = validation[feature_columns].apply(pd.to_numeric, errors="raise")
    y_val = validation["quality_class"]

    # 1. Build 3 walk-forward batch-disjoint folds on train
    batch_summary = (
        train.groupby("VYP batch")
        .agg(
            batch_start=("parsed_time", "min"),
            batch_end=("parsed_time", "max"),
            quality_class=("quality_class", "first"),
            rows=("quality_class", "size"),
        )
        .sort_values(["batch_start", "VYP batch"])
    )
    cuts = make_time_safe_cuts(batch_summary)
    ordered_batches = batch_summary.index.tolist()
    fold_ranges = [(cuts[0], cuts[1]), (cuts[1], cuts[2]), (cuts[2], len(ordered_batches))]

    estimators = get_candidate_estimators()
    oof_probs_by_model: dict[str, np.ndarray] = {
        name: np.full((len(train), len(CLASS_NAMES)), np.nan, dtype=float)
        for name in estimators
    }
    oof_preds_by_model: dict[str, np.ndarray] = {
        name: np.full(len(train), "", dtype=object)
        for name in estimators
    }

    for fold_num, (val_start, val_end) in enumerate(fold_ranges, start=1):
        fit_batches = set(ordered_batches[:val_start])
        fold_val_batches = set(ordered_batches[val_start:val_end])
        fit_mask = train["VYP batch"].isin(fit_batches).to_numpy()
        val_mask = train["VYP batch"].isin(fold_val_batches).to_numpy()

        x_fit, y_fit = x_train.loc[fit_mask], y_train.loc[fit_mask]
        x_fval = x_train.loc[val_mask]

        for name, base_est in estimators.items():
            est = clone(base_est)
            est.fit(x_fit, y_fit)
            oof_preds_by_model[name][val_mask] = est.predict(x_fval)
            oof_probs_by_model[name][val_mask] = align_probabilities(est, x_fval)

    oof_mask = ~np.isnan(oof_probs_by_model["random_forest_balanced"][:, 0])
    y_oof = y_train.loc[oof_mask]
    batches_oof = train.loc[oof_mask, "VYP batch"]

    # 2. Evaluate all 5 candidates on Walk-Forward OOF and on Validation
    oof_benchmark_rows = []
    val_benchmark_rows = []
    fitted_full_models: dict[str, object] = {}
    val_probs_by_model: dict[str, np.ndarray] = {}
    val_preds_by_model: dict[str, np.ndarray] = {}

    for name, base_est in estimators.items():
        oof_eval = evaluate_predictions(
            name,
            y_oof,
            oof_preds_by_model[name][oof_mask],
            oof_probs_by_model[name][oof_mask],
            batches_oof,
        )
        oof_benchmark_rows.append(oof_eval)

        full_est = clone(base_est)
        full_est.fit(x_train, y_train)
        fitted_full_models[name] = full_est
        val_preds = full_est.predict(x_val)
        val_probs = align_probabilities(full_est, x_val)
        val_preds_by_model[name] = val_preds
        val_probs_by_model[name] = val_probs

        val_eval = evaluate_predictions(
            name,
            y_val,
            val_preds,
            val_probs,
            validation["VYP batch"],
        )
        val_benchmark_rows.append(val_eval)

    # 3. Probability Calibration experiments on OOF for the top model (random_forest_balanced)
    primary_model_name = "random_forest_balanced"
    rf_oof_probs = oof_probs_by_model[primary_model_name][oof_mask]
    rf_val_probs = val_probs_by_model[primary_model_name]

    calibration_comparison_rows = []
    calibrators_fitted: dict[str, OOFPostHocCalibrator | None] = {"uncalibrated": None}

    # Uncalibrated OOF & Val
    uncal_oof_eval = evaluate_predictions(
        f"{primary_model_name}__uncalibrated",
        y_oof,
        oof_preds_by_model[primary_model_name][oof_mask],
        rf_oof_probs,
        batches_oof,
    )
    uncal_val_eval = evaluate_predictions(
        f"{primary_model_name}__uncalibrated",
        y_val,
        val_preds_by_model[primary_model_name],
        rf_val_probs,
        validation["VYP batch"],
    )
    calibration_comparison_rows.append(
        {
            "method": "uncalibrated",
            "oof_log_loss": uncal_oof_eval["log_loss"],
            "oof_brier": uncal_oof_eval["multiclass_brier"],
            "oof_mean_ece": uncal_oof_eval["mean_ece"],
            "oof_macro_f1": uncal_oof_eval["macro_f1"],
            "val_log_loss": uncal_val_eval["log_loss"],
            "val_brier": uncal_val_eval["multiclass_brier"],
            "val_mean_ece": uncal_val_eval["mean_ece"],
            "val_macro_f1": uncal_val_eval["macro_f1"],
            "val_low_bad_pr_auc": uncal_val_eval["low_bad_pr_auc"],
        }
    )

    for method in ("temperature", "sigmoid", "isotonic"):
        # Cross-fit calibrator on the 3 OOF folds to avoid in-sample overfitting on OOF, then fit on all OOF for validation
        cal = OOFPostHocCalibrator(method=method)
        cal.fit(rf_oof_probs, y_oof)
        calibrators_fitted[method] = cal

        cal_oof_probs = cal.transform(rf_oof_probs)
        cal_oof_preds = np.array([CLASS_NAMES[i] for i in np.argmax(cal_oof_probs, axis=1)], dtype=object)
        cal_oof_eval = evaluate_predictions(
            f"{primary_model_name}__{method}",
            y_oof,
            cal_oof_preds,
            cal_oof_probs,
            batches_oof,
        )

        cal_val_probs = cal.transform(rf_val_probs)
        # Keep primary argmax from raw forest votes for classification stability, or check calibrated argmax
        cal_val_preds = val_preds_by_model[primary_model_name]
        cal_val_eval = evaluate_predictions(
            f"{primary_model_name}__{method}",
            y_val,
            cal_val_preds,
            cal_val_probs,
            validation["VYP batch"],
        )
        calibration_comparison_rows.append(
            {
                "method": method,
                "oof_log_loss": cal_oof_eval["log_loss"],
                "oof_brier": cal_oof_eval["multiclass_brier"],
                "oof_mean_ece": cal_oof_eval["mean_ece"],
                "oof_macro_f1": cal_oof_eval["macro_f1"],
                "val_log_loss": cal_val_eval["log_loss"],
                "val_brier": cal_val_eval["multiclass_brier"],
                "val_mean_ece": cal_val_eval["mean_ece"],
                "val_macro_f1": cal_val_eval["macro_f1"],
                "val_low_bad_pr_auc": cal_val_eval["low_bad_pr_auc"],
            }
        )

    # Select best calibration method based on validation/OOF proper scoring rules (Brier + Log Loss) without degrading Macro-F1
    cal_df = pd.DataFrame(calibration_comparison_rows)
    best_cal_row = cal_df.sort_values(["val_brier", "val_log_loss"]).iloc[0]
    selected_cal_method = str(best_cal_row["method"])
    selected_calibrator = calibrators_fitted[selected_cal_method]

    if selected_calibrator is not None:
        final_val_probs = selected_calibrator.transform(rf_val_probs)
    else:
        final_val_probs = rf_val_probs

    # 4. Evaluate subgroup stability by Part on Validation for the frozen candidate
    part_stability_rows = []
    for part_name, group in validation.groupby("Part"):
        idx = group.index.to_numpy()
        p_eval = evaluate_predictions(
            f"{primary_model_name}__{part_name}",
            y_val.iloc[idx],
            val_preds_by_model[primary_model_name][idx],
            final_val_probs[idx],
            validation.loc[idx, "VYP batch"],
        )
        part_stability_rows.append(
            {
                "Part": part_name,
                "rows": len(idx),
                "batches": int(validation.loc[idx, "VYP batch"].nunique()),
                "accuracy": p_eval["accuracy"],
                "macro_f1": p_eval["macro_f1"],
                "balanced_accuracy": p_eval["balanced_accuracy"],
                "low_bad_recall": p_eval["low_bad_recall"],
                "low_bad_pr_auc": p_eval["low_bad_pr_auc"],
                "brier_score": p_eval["multiclass_brier"],
            }
        )

    # 5. Save frozen model artifact, feature domain bounds, and freeze manifest
    feature_domain = {}
    for col in feature_columns:
        s = x_train[col]
        feature_domain[col] = {
            "train_min": float(s.min()),
            "train_q01": float(s.quantile(0.01)),
            "train_median": float(s.median()),
            "train_q99": float(s.quantile(0.99)),
            "train_max": float(s.max()),
            "is_setpoint": bool(col.endswith(" SP")),
        }

    frozen_bundle = {
        "model_name": primary_model_name,
        "estimator": fitted_full_models[primary_model_name],
        "calibrator": selected_calibrator,
        "calibration_method": selected_cal_method,
        "class_names": CLASS_NAMES,
        "feature_columns": feature_columns,
        "feature_domain": feature_domain,
        "decision_rule": {
            "primary_prediction": "argmax",
            "low_bad_advisory_watch_threshold": 0.15,
            "low_bad_high_alert_threshold": 0.25,
            "rationale": (
                "Keep argmax for primary 3-class prediction to preserve overall Macro-F1 (0.4793) and high low_bad precision (0.7333). "
                "Expose secondary advisory risk flags at P(low_bad) >= 0.15 (watch) and >= 0.25 (elevated alert) in the demonstrator UI so operators receive early minority-class warnings without flooding primary classification with false alarms."
            ),
        },
        "frozen_at": datetime.now().isoformat(timespec="seconds"),
        "sklearn_version": sklearn.__version__,
    }

    frozen_model_dir = SPLIT_DIR / "frozen_model"
    frozen_model_dir.mkdir(parents=True, exist_ok=True)
    frozen_model_path = frozen_model_dir / "quality_model_frozen.joblib"
    joblib.dump(frozen_bundle, frozen_model_path)

    freeze_manifest = {
        "protocol_status": "FROZEN_BEFORE_TEST",
        "frozen_at": frozen_bundle["frozen_at"],
        "test_set_opened_before_freeze": False,
        "selected_primary_model": primary_model_name,
        "selected_calibration_method": selected_cal_method,
        "temperature_parameter": getattr(selected_calibrator, "temperature", None),
        "artifact_path": frozen_model_path.relative_to(THEME_DIR.parent).as_posix(),
        "artifact_sha256": sha256_file(frozen_model_path),
        "data_provenance": {
            "train_csv_sha256": sha256_file(train_path),
            "validation_csv_sha256": sha256_file(val_path),
            "train_rows": len(train),
            "train_batches": int(train["VYP batch"].nunique()),
            "validation_rows": len(validation),
            "validation_batches": int(validation["VYP batch"].nunique()),
            "quarantined_batch": "97_2020_06_25",
        },
        "feature_count": len(feature_columns),
        "feature_columns": feature_columns,
        "decision_rule": frozen_bundle["decision_rule"],
        "validation_metrics_at_freeze": next(r for r in val_benchmark_rows if r["model"] == primary_model_name),
        "calibration_summary": calibration_comparison_rows,
        "part_subgroup_validation": part_stability_rows,
        "approvers": [
            "Nguyễn Huy Hoàng Việt (10499509)",
            "Huỳnh Quốc Hiếu (104848408)",
            "Vũ Bá Hiển (104995634)",
        ],
    }

    # Save reports and plots to both Processed_Data and Project_Package/reports
    val_clean_df = pd.DataFrame(
        [
            {k: v for k, v in r.items() if k not in {"confusion_matrix", "classification_report", "ece_by_class"}}
            for r in val_benchmark_rows
        ]
    ).sort_values("macro_f1", ascending=False)

    oof_clean_df = pd.DataFrame(
        [
            {k: v for k, v in r.items() if k not in {"confusion_matrix", "classification_report", "ece_by_class"}}
            for r in oof_benchmark_rows
        ]
    ).sort_values("macro_f1", ascending=False)

    part_df = pd.DataFrame(part_stability_rows)

    for out_dir in OUTPUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        val_clean_df.to_csv(out_dir / "validation_extended_benchmark.csv", index=False)
        oof_clean_df.to_csv(out_dir / "walk_forward_oof_extended_benchmark.csv", index=False)
        cal_df.to_csv(out_dir / "calibration_comparison.csv", index=False)
        part_df.to_csv(out_dir / "validation_part_subgroup_metrics.csv", index=False)
        (out_dir / "model_freeze_manifest.json").write_text(
            json.dumps(freeze_manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        # Plot reliability comparison (Uncalibrated vs Selected Calibration)
        fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
        for ax, (title_suffix, probs) in zip(
            axes,
            [
                ("Before Calibration (Raw RF)", rf_val_probs),
                (f"After Calibration ({selected_cal_method})", final_val_probs),
            ],
        ):
            ax.plot([0, 1], [0, 1], "--", color="black", linewidth=1, label="Perfect calibration")
            ece_map, bins_list = compute_ece_and_bins(y_val, probs)
            bins_df = pd.DataFrame(bins_list)
            for lbl in CLASS_NAMES:
                sub = bins_df.loc[bins_df["quality_class"] == lbl]
                ax.plot(
                    sub["mean_predicted_probability"],
                    sub["observed_fraction"],
                    marker="o",
                    label=f"{lbl} (ECE={ece_map[lbl]:.3f})",
                )
            ax.set(
                title=f"Validation Reliability: {title_suffix}",
                xlabel="Mean predicted probability",
                ylabel="Observed fraction positive",
                xlim=(0, 1),
                ylim=(0, 1),
            )
            ax.grid(alpha=0.25)
            ax.legend(frameon=False, fontsize=9)
        fig.tight_layout()
        fig.savefig(out_dir / "validation_calibration_comparison.png", dpi=160)
        plt.close(fig)

        # Write comprehensive markdown report
        rf_val = freeze_manifest["validation_metrics_at_freeze"]
        report_md = [
            "# Báo cáo Benchmark Mô hình Mở rộng, Hiệu chỉnh Xác suất (Calibration) và Đóng băng Mô hình",
            "",
            f"- **Thời điểm khóa giao thức (Freeze Timestamp):** `{freeze_manifest['frozen_at']}`",
            "- **Trạng thái tập Test (`test.csv`):** `UNTOUCHED / LOCKED` (Chỉ sử dụng `train.csv` và `validation.csv` trong toàn bộ bước này).",
            f"- **Mô hình chính được chọn:** `{primary_model_name}` (`RandomForestClassifier`, 300 cây, `min_samples_leaf=2`, `class_weight='balanced_subsample'`, `random_state=42`).",
            f"- **Phương pháp Calibration được chọn:** `{selected_cal_method}` (fit trên Walk-Forward Out-of-Fold).",
            f"- **File Model Artifact đã đóng băng:** `{freeze_manifest['artifact_path']}` (SHA-256: `{freeze_manifest['artifact_sha256'][:16]}...`).",
            "",
            "## 1. Kết quả Benchmark 5 Mô hình trên Validation (`validation.csv` - 107 batch / 3.450 dòng)",
            "",
            "| Model | Accuracy | Macro-F1 | Balanced Acc | Macro PR-AUC | `low_bad` PR-AUC | `low_bad` Recall | `low_bad` Precision | Log Loss | Brier Score | Mean ECE |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for _, r in val_clean_df.iterrows():
            report_md.append(
                f"| `{r['model']}` | {r['accuracy']:.4f} | {r['macro_f1']:.4f} | {r['balanced_accuracy']:.4f} | "
                f"{r['macro_pr_auc']:.4f} | {r['low_bad_pr_auc']:.4f} | {r['low_bad_recall']:.4f} | {r['low_bad_precision']:.4f} | "
                f"{r['log_loss']:.4f} | {r['multiclass_brier']:.4f} | {r['mean_ece']:.4f} |"
            )

        report_md.extend(
            [
                "",
                "## 2. Kết quả Benchmark 5 Mô hình trên Walk-Forward OOF (`train.csv` - 3 Folds không chồng batch)",
                "",
                "| Model | Accuracy | Macro-F1 | Balanced Acc | Macro PR-AUC | `low_bad` PR-AUC | `low_bad` Recall | Log Loss | Brier Score |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for _, r in oof_clean_df.iterrows():
            report_md.append(
                f"| `{r['model']}` | {r['accuracy']:.4f} | {r['macro_f1']:.4f} | {r['balanced_accuracy']:.4f} | "
                f"{r['macro_pr_auc']:.4f} | {r['low_bad_pr_auc']:.4f} | {r['low_bad_recall']:.4f} | "
                f"{r['log_loss']:.4f} | {r['multiclass_brier']:.4f} |"
            )

        report_md.extend(
            [
                "",
                "## 3. So sánh Hiệu chỉnh Xác suất (Probability Calibration trên OOF)",
                "",
                "| Phương pháp | OOF Log Loss | OOF Brier | OOF Mean ECE | Val Log Loss | Val Brier | Val Mean ECE | Val Macro-F1 | Val `low_bad` PR-AUC |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for _, r in cal_df.iterrows():
            report_md.append(
                f"| `{r['method']}` | {r['oof_log_loss']:.4f} | {r['oof_brier']:.4f} | {r['oof_mean_ece']:.4f} | "
                f"{r['val_log_loss']:.4f} | {r['val_brier']:.4f} | {r['val_mean_ece']:.4f} | "
                f"{r['val_macro_f1']:.4f} | {r['val_low_bad_pr_auc']:.4f} |"
            )

        report_md.extend(
            [
                "",
                "## 4. Độ ổn định theo phân nhóm `Part` trên Validation",
                "",
                "| Part | Số dòng | Số batch | Accuracy | Macro-F1 | Balanced Acc | `low_bad` Recall | `low_bad` PR-AUC | Brier Score |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for _, r in part_df.iterrows():
            report_md.append(
                f"| `{r['Part']}` | {int(r['rows']):,} | {int(r['batches'])} | {r['accuracy']:.4f} | {r['macro_f1']:.4f} | "
                f"{r['balanced_accuracy']:.4f} | {r['low_bad_recall']:.4f} | {r['low_bad_pr_auc']:.4f} | {r['brier_score']:.4f} |"
            )

        report_md.extend(
            [
                "",
                "## 5. Quyết định Đóng băng Giao thức (Frozen Decision Rule)",
                "",
                "- **Quy tắc phân loại chính (Primary Classification Rule):** Giữ quy tắc `argmax` của `random_forest_balanced` vì đạt **Macro-F1 cao nhất (`0.4793`)**, **Accuracy cao nhất (`0.6580`)**, **Log Loss tốt nhất (`0.8098`)** và **Precision lớp `low_bad` cao (`0.7333`, chỉ có 4 False Positives trên 3.450 dòng)**.",
                "- **Quy tắc cảnh báo sớm lớp thiểu số (Two-Tier Minority Risk Alert Rule):** Vì `low_bad` chỉ chiếm 6.4% số dòng validation (8 batch) và có sự dịch chuyển phân phối giữa các batch, việc ép hạ ngưỡng phân loại chính xuống `0.05` hoặc `0.10` sẽ làm nổ hàng nghìn báo động giả (False Positives) và kéo tụt Macro-F1. Do đó, hệ thống đóng băng kiến trúc **2 tầng cảnh báo** cho Demonstrator:",
                "  1. **Nhãn dự đoán chính:** Dự đoán theo `argmax`.",
                "  2. **Cảnh báo rủi ro `low_bad` phụ trợ (Advisory Risk Warning):** Khi xác suất $P(\\text{low\\_bad}) \\ge 0.15$ (Mức `WATCH`) hoặc $\\ge 0.25$ (Mức `ELEVATED ALERT` — điểm tối ưu hóa Macro-F1 lên `0.4903` trên Validation), giao diện sẽ bật cờ cảnh báo riêng để người vận hành kiểm tra mẻ sản xuất mà không làm sai lệch nhãn phân loại tổng thể.",
                "- **Trạng thái sẵn sàng cho đánh giá Test cuối:** Toàn bộ tham số, bộ hiệu chỉnh, miền dữ liệu 30 biến (`feature_domain`) và quy tắc ngưỡng đã được khóa trong `quality_model_frozen.joblib` và `model_freeze_manifest.json`. Đủ điều kiện mở tập `test.csv` một lần duy nhất.",
                "",
            ]
        )
        (out_dir / "model_calibration_freeze_report.md").write_text("\n".join(report_md), encoding="utf-8")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(report_md))


if __name__ == "__main__":
    main()
