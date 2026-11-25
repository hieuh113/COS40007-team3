"""Walk-forward experiments for low_bad with batch-equal training weights."""

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support


PROJECT_DIR = Path(__file__).resolve().parent
THEME_DIR = PROJECT_DIR / "Theme3" if (PROJECT_DIR / "Theme3" / "Processed_Data").exists() else PROJECT_DIR.parent / "Theme3"
SPLIT_DIR = THEME_DIR / "Processed_Data"
OUTPUT_DIR = SPLIT_DIR / "robust_low_bad"
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
}
TARGET_CUT_PROPORTIONS = (0.55, 0.70, 0.85)
LOW_BAD_THRESHOLDS = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50)


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
        cut = min((value for value in safe_cuts if value not in selected), key=lambda value: abs(value - target))
        selected.append(cut)
    return sorted(selected)


def equal_batch_weights(frame: pd.DataFrame) -> np.ndarray:
    row_counts = frame.groupby("VYP batch")["VYP batch"].transform("size").to_numpy(dtype=float)
    batch_count = frame["VYP batch"].nunique()
    return len(frame) / batch_count / row_counts


def make_classifier() -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )


def probability_for(model: RandomForestClassifier, features: pd.DataFrame, label: str) -> np.ndarray:
    probabilities = model.predict_proba(features)
    return probabilities[:, list(model.classes_).index(label)]


def predictions_for_threshold(
    low_bad_scores: np.ndarray,
    non_low_bad_predictions: np.ndarray,
    threshold: float,
) -> np.ndarray:
    predictions = non_low_bad_predictions.copy()
    predictions[low_bad_scores >= threshold] = "low_bad"
    return predictions


def summarize_predictions(
    candidate: str,
    y_true: pd.Series,
    predictions: np.ndarray,
    rows: pd.DataFrame,
    evaluation: str,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        predictions,
        labels=CLASS_NAMES,
        zero_division=0,
    )
    matrix = confusion_matrix(y_true, predictions, labels=CLASS_NAMES)
    summary = {
        "evaluation": evaluation,
        "candidate": candidate,
        "rows": len(y_true),
        "batches": rows["VYP batch"].nunique(),
        "accuracy": float(np.mean(y_true.to_numpy() == predictions)),
        "macro_f1": float(f1_score(y_true, predictions, labels=CLASS_NAMES, average="macro", zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, predictions)),
        "low_bad_precision": float(precision[1]),
        "low_bad_recall": float(recall[1]),
        "low_bad_f1": float(f1[1]),
        "low_bad_support": int(support[1]),
        "predicted_low_bad": int(np.count_nonzero(predictions == "low_bad")),
        "low_bad_false_positive": int(matrix[0, 1] + matrix[2, 1]),
    }
    per_batch = []
    low_bad_rows = rows.loc[y_true.to_numpy() == "low_bad"].copy()
    low_bad_rows["prediction"] = predictions[y_true.to_numpy() == "low_bad"]
    for batch, group in low_bad_rows.groupby("VYP batch"):
        hits = int(group["prediction"].eq("low_bad").sum())
        per_batch.append(
            {
                "evaluation": evaluation,
                "candidate": candidate,
                "VYP batch": batch,
                "Part": "|".join(sorted(group["Part"].unique())),
                "low_bad_support": len(group),
                "low_bad_hits": hits,
                "low_bad_recall": hits / len(group),
            }
        )
    return summary, per_batch


def main() -> None:
    train = pd.read_csv(SPLIT_DIR / "train.csv")
    validation = pd.read_csv(SPLIT_DIR / "validation.csv")
    if train["VYP batch"].isin(validation["VYP batch"]).any():
        raise ValueError("A batch appears in both train and validation")

    train["parsed_time"] = pd.to_datetime(train["Set Time"], format="%d/%m/%Y %H:%M")
    validation["parsed_time"] = pd.to_datetime(validation["Set Time"], format="%d/%m/%Y %H:%M")
    feature_columns = [column for column in train.columns if column not in NON_FEATURE_COLUMNS | {"parsed_time"}]
    train[feature_columns] = train[feature_columns].apply(pd.to_numeric, errors="raise")
    validation[feature_columns] = validation[feature_columns].apply(pd.to_numeric, errors="raise")

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

    oof_predictions: dict[str, np.ndarray] = {
        "multiclass_equal_row": np.full(len(train), "", dtype=object),
        "multiclass_equal_batch": np.full(len(train), "", dtype=object),
        "two_stage_non_low_bad": np.full(len(train), "", dtype=object),
    }
    oof_low_bad_scores = np.full(len(train), np.nan)
    fold_rows = []
    oof_batch_metrics = []

    for fold_number, (validation_start, validation_end) in enumerate(fold_ranges, start=1):
        fit_batches = set(ordered_batches[:validation_start])
        fold_validation_batches = set(ordered_batches[validation_start:validation_end])
        fit_mask = train["VYP batch"].isin(fit_batches).to_numpy()
        validation_mask = train["VYP batch"].isin(fold_validation_batches).to_numpy()
        fold_train = train.loc[fit_mask]
        fold_validation = train.loc[validation_mask]
        if fold_train["quality_class"].nunique() != len(CLASS_NAMES):
            raise ValueError(f"Fold {fold_number} training partition lacks a class")

        x_fit = fold_train[feature_columns]
        y_fit = fold_train["quality_class"]
        x_fold_validation = fold_validation[feature_columns]

        equal_row_model = make_classifier()
        equal_row_model.fit(x_fit, y_fit)
        oof_predictions["multiclass_equal_row"][validation_mask] = equal_row_model.predict(x_fold_validation)

        batch_weighted_model = make_classifier()
        batch_weighted_model.fit(x_fit, y_fit, sample_weight=equal_batch_weights(fold_train))
        oof_predictions["multiclass_equal_batch"][validation_mask] = batch_weighted_model.predict(x_fold_validation)

        binary_y = y_fit.eq("low_bad").astype(int)
        detector = make_classifier()
        detector.fit(x_fit, binary_y, sample_weight=equal_batch_weights(fold_train))
        fold_scores = probability_for(detector, x_fold_validation, 1)
        oof_low_bad_scores[validation_mask] = fold_scores

        non_low_fit = fold_train.loc[fold_train["quality_class"] != "low_bad"]
        rest_model = make_classifier()
        rest_model.fit(
            non_low_fit[feature_columns],
            non_low_fit["quality_class"],
            sample_weight=equal_batch_weights(non_low_fit),
        )
        oof_predictions["two_stage_non_low_bad"][validation_mask] = rest_model.predict(x_fold_validation)

        fold_labels = fold_validation["quality_class"]
        fold_rows.append(
            {
                "fold": fold_number,
                "fit_batches": len(fit_batches),
                "validation_batches": len(fold_validation_batches),
                "fit_low_bad_batches": int((fold_train.groupby("VYP batch")["quality_class"].first() == "low_bad").sum()),
                "validation_low_bad_batches": int((fold_validation.groupby("VYP batch")["quality_class"].first() == "low_bad").sum()),
                "validation_low_bad_rows": int(fold_labels.eq("low_bad").sum()),
                "fit_end": fold_train["parsed_time"].max().isoformat(sep=" "),
                "validation_start": fold_validation["parsed_time"].min().isoformat(sep=" "),
                "validation_end": fold_validation["parsed_time"].max().isoformat(sep=" "),
            }
        )

    oof_mask = ~np.isnan(oof_low_bad_scores)
    oof_rows = train.loc[oof_mask].copy()
    y_oof = oof_rows["quality_class"]
    result_rows = []
    per_batch_rows = []
    prediction_sets: dict[str, np.ndarray] = {}

    for name in ("multiclass_equal_row", "multiclass_equal_batch", "two_stage_non_low_bad"):
        predictions = oof_predictions[name][oof_mask]
        candidate = f"{name}__argmax_or_rest"
        summary, batch_results = summarize_predictions(candidate, y_oof, predictions, oof_rows, "train_walk_forward_oof")
        result_rows.append(summary)
        per_batch_rows.extend(batch_results)
        prediction_sets[candidate] = predictions

    threshold_candidates = []
    for threshold in LOW_BAD_THRESHOLDS:
        predictions = oof_predictions["two_stage_non_low_bad"][oof_mask].copy()
        predictions[oof_low_bad_scores[oof_mask] >= threshold] = "low_bad"
        candidate = f"two_stage_batch_equal__raw_score_ge_{threshold:.2f}"
        summary, batch_results = summarize_predictions(candidate, y_oof, predictions, oof_rows, "train_walk_forward_oof")
        result_rows.append(summary)
        per_batch_rows.extend(batch_results)
        threshold_candidates.append((threshold, candidate, summary))
        prediction_sets[candidate] = predictions

    fold_frame = pd.DataFrame(fold_rows)
    results_frame = pd.DataFrame(result_rows)
    batch_frame = pd.DataFrame(per_batch_rows)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fold_frame.to_csv(OUTPUT_DIR / "walk_forward_folds.csv", index=False)
    results_frame.to_csv(OUTPUT_DIR / "walk_forward_oof_metrics.csv", index=False)
    batch_frame.to_csv(OUTPUT_DIR / "walk_forward_oof_low_bad_batch_recall.csv", index=False)

    # Apply the OOF-specified threshold grid to the untouched-in-this-experiment validation period.
    validation_results = []
    validation_batch_results = []
    validation_prediction_vectors: dict[str, np.ndarray] = {}
    x_train = train[feature_columns]
    y_train = train["quality_class"]
    x_validation = validation[feature_columns]
    y_validation = validation["quality_class"]
    for name, weighted in (("multiclass_equal_row", False), ("multiclass_equal_batch", True)):
        model = make_classifier()
        if weighted:
            model.fit(x_train, y_train, sample_weight=equal_batch_weights(train))
        else:
            model.fit(x_train, y_train)
        predictions = model.predict(x_validation)
        validation_prediction_vectors[name] = predictions
        summary, batch_results = summarize_predictions(name, y_validation, predictions, validation, "validation")
        validation_results.append(summary)
        validation_batch_results.extend(batch_results)

    detector = make_classifier()
    detector.fit(
        x_train,
        y_train.eq("low_bad").astype(int),
        sample_weight=equal_batch_weights(train),
    )
    low_bad_scores = probability_for(detector, x_validation, 1)
    non_low_train = train.loc[y_train != "low_bad"]
    rest_model = make_classifier()
    rest_model.fit(
        non_low_train[feature_columns],
        non_low_train["quality_class"],
        sample_weight=equal_batch_weights(non_low_train),
    )
    non_low_predictions = rest_model.predict(x_validation)

    thresholds = [
        (None, "two_stage_batch_equal__argmax_or_rest", non_low_predictions),
        *[
            (
                threshold,
                f"two_stage_batch_equal__raw_score_ge_{threshold:.2f}",
                predictions_for_threshold(low_bad_scores, non_low_predictions, threshold),
            )
            for threshold in LOW_BAD_THRESHOLDS
        ],
    ]
    for threshold, candidate, predictions in thresholds:
        validation_prediction_vectors[candidate] = predictions
        summary, batch_results = summarize_predictions(candidate, y_validation, predictions, validation, "validation")
        summary["oof_threshold"] = threshold
        validation_results.append(summary)
        validation_batch_results.extend(batch_results)
    validation_frame = pd.DataFrame(validation_results)
    validation_batch_frame = pd.DataFrame(validation_batch_results)
    validation_frame.to_csv(OUTPUT_DIR / "validation_metrics_after_oof_thresholds.csv", index=False)
    validation_batch_frame.to_csv(OUTPUT_DIR / "validation_low_bad_batch_recall.csv", index=False)

    low_bad_validation = validation.loc[y_validation.eq("low_bad")].copy()
    low_bad_validation["baseline_prediction"] = validation_prediction_vectors["multiclass_equal_row"][
        y_validation.eq("low_bad").to_numpy()
    ]
    low_bad_validation["Set Time parsed"] = pd.to_datetime(
        low_bad_validation["Set Time"], format="%d/%m/%Y %H:%M"
    )
    batch_profile_rows = []
    for batch, group in low_bad_validation.groupby("VYP batch"):
        batch_profile = {
            "VYP batch": batch,
            "Part": "|".join(sorted(group["Part"].unique())),
            "low_bad_rows": len(group),
            "baseline_hits": int(group["baseline_prediction"].eq("low_bad").sum()),
            "baseline_recall": float(group["baseline_prediction"].eq("low_bad").mean()),
            "Set Time min": group["Set Time parsed"].min().isoformat(sep=" "),
            "Set Time max": group["Set Time parsed"].max().isoformat(sep=" "),
        }
        for feature in feature_columns:
            batch_profile[f"median::{feature}"] = float(group[feature].median())
        batch_profile_rows.append(batch_profile)
    batch_profiles = pd.DataFrame(batch_profile_rows).sort_values(["Set Time min", "VYP batch"])
    batch_profiles.to_csv(OUTPUT_DIR / "validation_low_bad_batch_profiles.csv", index=False)

    hit_profiles = batch_profiles.loc[batch_profiles["baseline_hits"] > 0]
    missed_profiles = batch_profiles.loc[batch_profiles["baseline_hits"] == 0]
    profile_comparisons = []
    for feature in feature_columns:
        hit_median = float(hit_profiles[f"median::{feature}"].median()) if not hit_profiles.empty else np.nan
        missed_median = float(missed_profiles[f"median::{feature}"].median()) if not missed_profiles.empty else np.nan
        scale = float(train[feature].std())
        profile_comparisons.append(
            {
                "feature": feature,
                "hit_batch_median": hit_median,
                "missed_batch_median": missed_median,
                "difference_in_train_stds": (hit_median - missed_median) / scale if scale else np.nan,
                "hit_batches": len(hit_profiles),
                "missed_batches": len(missed_profiles),
            }
        )
    profile_comparison = pd.DataFrame(profile_comparisons)
    profile_comparison["abs_difference_in_train_stds"] = profile_comparison["difference_in_train_stds"].abs()
    profile_comparison = profile_comparison.sort_values("abs_difference_in_train_stds", ascending=False)
    profile_comparison.to_csv(OUTPUT_DIR / "validation_low_bad_hit_missed_feature_profiles.csv", index=False)

    baseline_hits = batch_profiles.loc[batch_profiles["baseline_hits"] > 0]
    hit_batch_summary = "; ".join(
        f"`{row['VYP batch']}` ({row['Part']}, {row['baseline_hits']}/{row['low_bad_rows']} hits, {row['Set Time min']} to {row['Set Time max']})"
        for row in baseline_hits.to_dict(orient="records")
    ) or "none"
    top_profile_differences = profile_comparison.head(5).to_dict(orient="records")
    profile_lines = [
        f"- `{row['feature']}`: hit-batch median {row['hit_batch_median']:.3f}, missed-batch median {row['missed_batch_median']:.3f}, difference {row['difference_in_train_stds']:.2f} train standard deviations"
        for row in top_profile_differences
    ]

    report_lines = [
        "# Walk-forward `low_bad` experiments",
        "",
        "Chỉ đọc train/validation; không mở test. Các fold walk-forward không chồng batch validation, mỗi batch được dự đoán OOF tối đa một lần. Threshold grid được đánh giá trên OOF của train trước khi áp dụng nguyên trạng lên validation.",
        "",
        "## Folds",
        "",
        "| Fold | Train batches | Validation batches | Train `low_bad` batches | Validation `low_bad` batches/rows | Validation period |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in fold_rows:
        report_lines.append(
            f"| {row['fold']} | {row['fit_batches']} | {row['validation_batches']} | {row['fit_low_bad_batches']} | {row['validation_low_bad_batches']}/{row['validation_low_bad_rows']} | {row['validation_start']} to {row['validation_end']} |"
        )
    report_lines.extend(
        [
            "",
            "## Phân tích batch `low_bad` trong validation",
            "",
            f"RF baseline nhận đúng `low_bad` ở {len(baseline_hits)}/{len(batch_profiles)} batch: {hit_batch_summary}.",
            f"So sánh trung vị feature của batch được nhận diện với các batch bị bỏ sót (một batch hit so với {len(missed_profiles)} batch missed; chỉ mô tả, không suy luận nguyên nhân):",
            *profile_lines,
            "",
            "Các chênh lệch SP/PV có thể phản ánh khác biệt batch/Part/thời gian; một batch hit không đủ để kết luận về quy luật tổng quát.",
        ]
    )

    oof_order = results_frame.sort_values(["macro_f1", "balanced_accuracy"], ascending=False)
    report_lines.extend(
        [
            "",
            "## Train walk-forward OOF",
            "",
            "| Candidate | Macro-F1 | Balanced accuracy | `low_bad` precision | `low_bad` recall | `low_bad` FP |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in oof_order.to_dict(orient="records"):
        report_lines.append(
            f"| `{row['candidate']}` | {row['macro_f1']:.3f} | {row['balanced_accuracy']:.3f} | {row['low_bad_precision']:.3f} | {row['low_bad_recall']:.3f} | {int(row['low_bad_false_positive'])} |"
        )

    report_lines.extend(
        [
            "",
            "## Validation check",
            "",
            "| Candidate | Macro-F1 | Balanced accuracy | `low_bad` precision | `low_bad` recall | `low_bad` FP |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in validation_frame.sort_values(["macro_f1", "balanced_accuracy"], ascending=False).to_dict(orient="records"):
        report_lines.append(
            f"| `{row['candidate']}` | {row['macro_f1']:.3f} | {row['balanced_accuracy']:.3f} | {row['low_bad_precision']:.3f} | {row['low_bad_recall']:.3f} | {int(row['low_bad_false_positive'])} |"
        )
    report_lines.extend(
        [
            "",
            "Sample weighting makes each batch's total training weight equal; this does not create independent information or new `low_bad` batches. `low_bad` scores are uncalibrated; threshold rows are trade-off diagnostics only, not probabilities or deployment recommendations.",
            "The validation period has already been used in prior model/threshold exploration. Treat its results as a final diagnostic for these experiments, not as an untouched estimate. A decision threshold still requires an agreed false-alarm/miss cost. Keep the final test set untouched until model and operating rule are frozen.",
            "",
            "See `walk_forward_folds.csv`, `walk_forward_oof_metrics.csv`, `walk_forward_oof_low_bad_batch_recall.csv`, `validation_metrics_after_oof_thresholds.csv`, `validation_low_bad_batch_recall.csv`, `validation_low_bad_batch_profiles.csv`, and `validation_low_bad_hit_missed_feature_profiles.csv` for details.",
            "",
        ]
    )
    (OUTPUT_DIR / "robust_low_bad_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(report_lines))


if __name__ == "__main__":
    main()