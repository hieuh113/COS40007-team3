"""Explore low_bad class-weight and decision-score trade-offs on validation."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score, precision_recall_fscore_support


PROJECT_DIR = Path(__file__).resolve().parent
THEME_DIR = PROJECT_DIR / "Theme3" if (PROJECT_DIR / "Theme3" / "Processed_Data").exists() else PROJECT_DIR.parent / "Theme3"
SPLIT_DIR = THEME_DIR / "Processed_Data"
OUTPUT_DIR = SPLIT_DIR / "low_bad_tuning"
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
WEIGHT_FACTORS = (1, 2, 4, 8, 16, 32)
LOW_BAD_THRESHOLDS = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50)


def metrics_for(y_true: pd.Series, predictions: np.ndarray) -> dict[str, object]:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        predictions,
        labels=CLASS_NAMES,
        zero_division=0,
    )
    matrix = confusion_matrix(y_true, predictions, labels=CLASS_NAMES)
    return {
        "accuracy": float(np.mean(y_true.to_numpy() == predictions)),
        "macro_f1": float(f1_score(y_true, predictions, labels=CLASS_NAMES, average="macro", zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, predictions)),
        "low_bad_precision": float(precision[1]),
        "low_bad_recall": float(recall[1]),
        "low_bad_f1": float(f1[1]),
        "low_bad_support": int(support[1]),
        "predicted_low_bad": int(np.count_nonzero(predictions == "low_bad")),
        "low_bad_true_positive": int(matrix[1, 1]),
        "low_bad_false_positive": int(matrix[0, 1] + matrix[2, 1]),
        "confusion_matrix": matrix.tolist(),
    }


def apply_low_bad_threshold(
    probabilities: np.ndarray,
    model_classes: list[str],
    threshold: float,
) -> np.ndarray:
    aligned = np.zeros((len(probabilities), len(CLASS_NAMES)))
    for source_index, label in enumerate(model_classes):
        aligned[:, CLASS_NAMES.index(label)] = probabilities[:, source_index]
    low_bad_index = CLASS_NAMES.index("low_bad")
    other_indices = [index for index, label in enumerate(CLASS_NAMES) if label != "low_bad"]
    other_predictions = np.asarray(CLASS_NAMES)[
        np.asarray(other_indices)[np.argmax(aligned[:, other_indices], axis=1)]
    ]
    predictions = other_predictions
    predictions[aligned[:, low_bad_index] >= threshold] = "low_bad"
    return predictions


def main() -> None:
    train = pd.read_csv(SPLIT_DIR / "train.csv")
    validation = pd.read_csv(SPLIT_DIR / "validation.csv")
    if train["VYP batch"].isin(validation["VYP batch"]).any():
        raise ValueError("A batch appears in both train and validation")

    feature_columns = [column for column in train.columns if column not in NON_FEATURE_COLUMNS]
    x_train = train[feature_columns].apply(pd.to_numeric, errors="raise")
    x_validation = validation[feature_columns].apply(pd.to_numeric, errors="raise")
    y_train = train["quality_class"]
    y_validation = validation["quality_class"]
    low_bad_batches = sorted(validation.loc[y_validation == "low_bad", "VYP batch"].unique())
    if len(low_bad_batches) == 0:
        raise ValueError("Validation contains no low_bad batches")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    experiment_specs: list[tuple[str, str | dict[str, float]]] = [
        ("balanced_subsample", "balanced_subsample"),
        *[
            (
                f"low_bad_weight_x{factor}",
                {"good": 1.0, "low_bad": float(factor), "high_bad": 1.0},
            )
            for factor in WEIGHT_FACTORS
        ],
    ]
    summary_rows = []
    batch_rows = []
    confusion_matrices = {}

    for experiment_name, class_weight in experiment_specs:
        model = RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=2,
            class_weight=class_weight,
            random_state=42,
            n_jobs=-1,
        )
        model.fit(x_train, y_train)
        probabilities = model.predict_proba(x_validation)
        candidates: list[tuple[str, np.ndarray]] = [
            ("argmax", model.predict(x_validation)),
            *[
                (
                    f"raw_score_ge_{threshold:.2f}",
                    apply_low_bad_threshold(probabilities, list(model.classes_), threshold),
                )
                for threshold in LOW_BAD_THRESHOLDS
            ],
        ]

        for decision_rule, predictions in candidates:
            metrics = metrics_for(y_validation, predictions)
            candidate_name = f"{experiment_name}__{decision_rule}"
            summary_rows.append(
                {
                    "candidate": candidate_name,
                    "weighting": experiment_name,
                    "decision_rule": decision_rule,
                    **{key: value for key, value in metrics.items() if key != "confusion_matrix"},
                }
            )
            confusion_matrices[candidate_name] = {
                "labels_order": CLASS_NAMES,
                "rows_actual_columns_predicted": metrics["confusion_matrix"],
            }
            for batch in low_bad_batches:
                mask = validation["VYP batch"].eq(batch).to_numpy() & y_validation.eq("low_bad").to_numpy()
                support = int(mask.sum())
                hits = int(np.count_nonzero(predictions[mask] == "low_bad"))
                batch_rows.append(
                    {
                        "candidate": candidate_name,
                        "weighting": experiment_name,
                        "decision_rule": decision_rule,
                        "VYP batch": batch,
                        "low_bad_support": support,
                        "low_bad_hits": hits,
                        "low_bad_recall": hits / support if support else 0.0,
                    }
                )

    summary = pd.DataFrame(summary_rows).sort_values(
        ["low_bad_recall", "low_bad_precision", "macro_f1"], ascending=False
    )
    batch_detail = pd.DataFrame(batch_rows)
    summary.to_csv(OUTPUT_DIR / "validation_low_bad_tradeoffs.csv", index=False)
    batch_detail.to_csv(OUTPUT_DIR / "validation_low_bad_batch_recall.csv", index=False)
    (OUTPUT_DIR / "validation_low_bad_confusion_matrices.json").write_text(
        json.dumps(confusion_matrices, indent=2) + "\n",
        encoding="utf-8",
    )

    baseline = summary.loc[summary["candidate"] == "balanced_subsample__argmax"].iloc[0]
    argmax_candidates = summary.loc[summary["decision_rule"] == "argmax"].sort_values(
        ["low_bad_recall", "macro_f1"], ascending=False
    )
    top_recall = summary.head(8)
    top_macro_f1 = summary.sort_values(
        ["macro_f1", "balanced_accuracy"], ascending=False
    ).head(8)
    best_macro_f1 = top_macro_f1.iloc[0]
    batch_baseline = batch_detail.loc[batch_detail["candidate"] == "balanced_subsample__argmax"]
    per_batch_lines = [
        "| Batch | low_bad rows | Correct low_bad predictions | Recall |",
        "|---|---:|---:|---:|",
    ]
    for row in batch_baseline.itertuples(index=False):
        per_batch_lines.append(
            f"| `{getattr(row, '_3')}` | {row.low_bad_support} | {row.low_bad_hits} | {row.low_bad_recall:.3f} |"
        )

    report_lines = [
        "# Phân tích lỗi và tuning `low_bad`",
        "",
        "Thí nghiệm chỉ fit trên `train.csv` và đánh giá/chọn trade-off trên `validation.csv`; không đọc `test.csv`. Các kết quả validation dưới đây dùng để khảo sát và chọn ứng viên, không phải ước lượng cuối cùng sau tuning.",
        "",
        f"Validation có {len(low_bad_batches)} batch chứa `low_bad` với tổng {int((y_validation == 'low_bad').sum())} dòng. Baseline Random Forest `balanced_subsample` giữ quy tắc argmax có recall {baseline.low_bad_recall:.4f}, precision {baseline.low_bad_precision:.4f}, macro-F1 {baseline.macro_f1:.4f}, và dự đoán `low_bad` {int(baseline.predicted_low_bad)} lần.",
        f"Tăng class weight mà vẫn dùng argmax không nâng recall `low_bad` vượt baseline (cao nhất {argmax_candidates.iloc[0].low_bad_recall:.4f}). Ứng viên macro-F1 cao nhất khi quét ngưỡng là `{best_macro_f1.candidate}`: macro-F1 {best_macro_f1.macro_f1:.4f}, precision/recall `low_bad` {best_macro_f1.low_bad_precision:.4f}/{best_macro_f1.low_bad_recall:.4f}, {int(best_macro_f1.low_bad_false_positive)} false positives.",
        "",
        "## Baseline recall theo batch",
        "",
        *per_batch_lines,
        "",
        "## Class weighting với argmax",
        "",
        "| Candidate | low_bad precision | low_bad recall | low_bad F1 | Macro-F1 | Balanced accuracy | FP low_bad |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in argmax_candidates.itertuples(index=False):
        report_lines.append(
            f"| `{row.candidate}` | {row.low_bad_precision:.3f} | {row.low_bad_recall:.3f} | {row.low_bad_f1:.3f} | {row.macro_f1:.3f} | {row.balanced_accuracy:.3f} | {int(row.low_bad_false_positive)} |"
        )
    report_lines.extend(
        [
            "",
            "## Phương án ưu tiên recall",
            "",
            "| Candidate | Rule | low_bad precision | low_bad recall | Dự đoán low_bad | Macro-F1 | FP low_bad |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in top_recall.itertuples(index=False):
        report_lines.append(
            f"| `{row.candidate}` | `{row.decision_rule}` | {row.low_bad_precision:.3f} | {row.low_bad_recall:.3f} | {int(row.predicted_low_bad)} | {row.macro_f1:.3f} | {int(row.low_bad_false_positive)} |"
        )
    report_lines.extend(
        [
            "",
            "## Phương án ưu tiên macro-F1",
            "",
            "| Candidate | Rule | low_bad precision | low_bad recall | Dự đoán low_bad | Macro-F1 | Balanced accuracy | FP low_bad |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in top_macro_f1.itertuples(index=False):
        report_lines.append(
            f"| `{row.candidate}` | `{row.decision_rule}` | {row.low_bad_precision:.3f} | {row.low_bad_recall:.3f} | {int(row.predicted_low_bad)} | {row.macro_f1:.3f} | {row.balanced_accuracy:.3f} | {int(row.low_bad_false_positive)} |"
        )
    report_lines.extend(
        [
            "",
            "`raw_score_ge_*` là ngưỡng trên điểm `predict_proba` chưa được hiệu chỉnh, không được diễn giải là xác suất tin cậy. Thí nghiệm không tự chọn ngưỡng triển khai: cần nhóm/chuyên gia xác định đánh đổi giữa bỏ sót `low_bad` và false alarms.",
            "",
            "Kết quả phải được xem ở cấp batch: nếu recall tập trung vào một vài batch, cải thiện trên dòng không đồng nghĩa tổng quát hóa qua batch. Chốt mô hình/quy tắc dự đoán sau phân tích train-validation; chỉ sau đó mới chạy test một lần để báo cáo cuối.",
            "",
            "Artifacts: `validation_low_bad_tradeoffs.csv`, `validation_low_bad_batch_recall.csv`, `validation_low_bad_confusion_matrices.json`.",
            "",
        ]
    )
    (OUTPUT_DIR / "low_bad_tuning_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    print("\n".join(report_lines))


if __name__ == "__main__":
    main()