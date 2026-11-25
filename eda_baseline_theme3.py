"""EDA and validation-only model comparison for the Theme 3 quality task."""

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


PROJECT_DIR = Path(__file__).resolve().parent
THEME_DIR = PROJECT_DIR / "Theme3" if (PROJECT_DIR / "Theme3" / "Processed_Data").exists() else PROJECT_DIR.parent / "Theme3"
SPLIT_DIR = THEME_DIR / "Processed_Data"
OUTPUT_DIR = SPLIT_DIR / "eda_baseline"
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


def load_split(name: str) -> pd.DataFrame:
    path = SPLIT_DIR / f"{name}.csv"
    frame = pd.read_csv(path)
    if set(frame["split"].unique()) != {name}:
        raise ValueError(f"Unexpected split label in {path}")
    return frame


def class_distribution(frame: pd.DataFrame, split_name: str) -> pd.DataFrame:
    counts = frame["quality_class"].value_counts().reindex(CLASS_NAMES, fill_value=0)
    return pd.DataFrame(
        {
            "split": split_name,
            "quality_class": CLASS_NAMES,
            "rows": [int(counts[label]) for label in CLASS_NAMES],
            "proportion": [float(counts[label] / len(frame)) for label in CLASS_NAMES],
            "batches": [
                int(frame.loc[frame["quality_class"] == label, "VYP batch"].nunique())
                for label in CLASS_NAMES
            ],
        }
    )


def evaluate(name: str, estimator, x_train, y_train, x_validation, y_validation) -> dict[str, object]:
    estimator.fit(x_train, y_train)
    predictions = estimator.predict(x_validation)
    probabilities = None
    probability_loss = None
    brier_score = None
    if hasattr(estimator, "predict_proba"):
        raw_probabilities = estimator.predict_proba(x_validation)
        classes = list(estimator.classes_)
        aligned_probabilities = np.zeros((len(y_validation), len(CLASS_NAMES)))
        for column_index, label in enumerate(classes):
            aligned_probabilities[:, CLASS_NAMES.index(label)] = raw_probabilities[:, column_index]
        probabilities = aligned_probabilities
        probability_order = sorted(CLASS_NAMES)
        ordered_probabilities = probabilities[:, [CLASS_NAMES.index(label) for label in probability_order]]
        probability_loss = float(log_loss(y_validation, ordered_probabilities, labels=probability_order))
        actual = np.column_stack([y_validation.to_numpy() == label for label in CLASS_NAMES]).astype(float)
        brier_score = float(np.mean(np.sum((probabilities - actual) ** 2, axis=1)))
    return {
        "model": name,
        "accuracy": float(accuracy_score(y_validation, predictions)),
        "macro_f1": float(f1_score(y_validation, predictions, labels=CLASS_NAMES, average="macro", zero_division=0)),
        "balanced_accuracy": float(balanced_accuracy_score(y_validation, predictions)),
        "confusion_matrix": confusion_matrix(y_validation, predictions, labels=CLASS_NAMES).tolist(),
        "log_loss": probability_loss,
        "multiclass_brier": brier_score,
        "probabilities": probabilities,
        "classification_report": classification_report(
            y_validation,
            predictions,
            labels=CLASS_NAMES,
            target_names=CLASS_NAMES,
            output_dict=True,
            zero_division=0,
        ),
    }


def main() -> None:
    train = load_split("train")
    validation = load_split("validation")
    if train["VYP batch"].isin(validation["VYP batch"]).any():
        raise ValueError("A batch appears in both train and validation")

    feature_columns = [column for column in train.columns if column not in NON_FEATURE_COLUMNS]
    if not feature_columns:
        raise ValueError("No numeric model features found")
    x_train = train[feature_columns].apply(pd.to_numeric, errors="raise")
    x_validation = validation[feature_columns].apply(pd.to_numeric, errors="raise")
    if x_train.isna().any().any() or x_validation.isna().any().any():
        raise ValueError("Missing feature values found; review preprocessing before modeling")

    y_train = train["quality_class"]
    y_validation = validation["quality_class"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    distribution = pd.concat(
        [class_distribution(train, "train"), class_distribution(validation, "validation")],
        ignore_index=True,
    )
    distribution.to_csv(OUTPUT_DIR / "class_distribution.csv", index=False)

    part_distribution = (
        pd.crosstab([train["Part"], train["quality_class"]], columns="rows")
        .reset_index()
        .rename(columns={"Part": "Part", "quality_class": "quality_class"})
    )
    part_distribution.to_csv(OUTPUT_DIR / "train_part_class_counts.csv", index=False)

    monthly = train[["Set Time", "quality_class"]].copy()
    monthly["month"] = pd.to_datetime(monthly["Set Time"], format="%d/%m/%Y %H:%M").dt.to_period("M").astype(str)
    monthly_counts = pd.crosstab(monthly["month"], monthly["quality_class"]).reindex(columns=CLASS_NAMES, fill_value=0)
    monthly_counts.to_csv(OUTPUT_DIR / "train_monthly_class_counts.csv")

    summary_rows = []
    for label in CLASS_NAMES:
        class_features = x_train.loc[y_train == label]
        description = class_features.describe(percentiles=[0.25, 0.5, 0.75]).T
        for feature, values in description.iterrows():
            summary_rows.append(
                {
                    "quality_class": label,
                    "feature": feature,
                    "count": int(values["count"]),
                    "mean": float(values["mean"]),
                    "std": float(values["std"]),
                    "min": float(values["min"]),
                    "q25": float(values["25%"]),
                    "median": float(values["50%"]),
                    "q75": float(values["75%"]),
                    "max": float(values["max"]),
                }
            )
    pd.DataFrame(summary_rows).to_csv(OUTPUT_DIR / "train_feature_summary_by_class.csv", index=False)

    missingness = pd.DataFrame(
        {
            "feature": feature_columns,
            "train_missing": [int(x_train[column].isna().sum()) for column in feature_columns],
            "validation_missing": [int(x_validation[column].isna().sum()) for column in feature_columns],
        }
    )
    missingness.to_csv(OUTPUT_DIR / "feature_missingness.csv", index=False)

    figure, axis = plt.subplots(figsize=(8, 5))
    for split_name in ("train", "validation"):
        counts = distribution.loc[distribution["split"] == split_name].set_index("quality_class")["rows"]
        axis.plot(CLASS_NAMES, counts.reindex(CLASS_NAMES), marker="o", label=split_name)
    axis.set(title="Quality class counts", xlabel="Quality class", ylabel="Rows")
    axis.grid(axis="y", alpha=0.25)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "class_distribution.png", dpi=160)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(11, 5))
    monthly_counts.plot(kind="line", marker="o", ax=axis)
    axis.set(title="Training rows by month and quality class", xlabel="Month", ylabel="Rows")
    axis.tick_params(axis="x", rotation=45)
    axis.grid(axis="y", alpha=0.25)
    axis.legend(title="Quality class", frameon=False)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "train_monthly_class_counts.png", dpi=160)
    plt.close(figure)

    sp_columns = [column for column in feature_columns if column.endswith(" SP")]
    figure, axes = plt.subplots(2, 4, figsize=(16, 8))
    for axis, feature in zip(axes.flat, sp_columns):
        values = [x_train.loc[y_train == label, feature].dropna().to_numpy() for label in CLASS_NAMES]
        axis.boxplot(values, tick_labels=CLASS_NAMES, showfliers=False)
        axis.set_title(feature, fontsize=9)
        axis.tick_params(axis="x", labelrotation=25, labelsize=8)
        axis.grid(axis="y", alpha=0.2)
    axes.flat[-1].set_visible(False)
    figure.suptitle("Training setpoint distributions by quality class", fontsize=14)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "train_setpoint_distributions.png", dpi=160)
    plt.close(figure)

    estimators = {
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
        "hist_gradient_boosting": HistGradientBoostingClassifier(
            learning_rate=0.08,
            max_iter=150,
            l2_regularization=1.0,
            random_state=42,
        ),
    }
    results = [
        evaluate(name, estimator, x_train, y_train, x_validation, y_validation)
        for name, estimator in estimators.items()
    ]
    results.sort(key=lambda result: (result["macro_f1"], result["balanced_accuracy"]), reverse=True)
    best_candidate = next(result for result in results if result["model"] != "majority_baseline")
    majority_result = next(result for result in results if result["model"] == "majority_baseline")
    selected_report = best_candidate["classification_report"]
    low_bad_report = selected_report["low_bad"]
    low_bad_correct = round(low_bad_report["recall"] * low_bad_report["support"])

    comparison = pd.DataFrame(
        [
            {
                "model": result["model"],
                "accuracy": result["accuracy"],
                "macro_f1": result["macro_f1"],
                "balanced_accuracy": result["balanced_accuracy"],
                "log_loss": result["log_loss"],
                "multiclass_brier": result["multiclass_brier"],
            }
            for result in results
        ]
    )
    comparison.to_csv(OUTPUT_DIR / "validation_model_comparison.csv", index=False)
    (OUTPUT_DIR / "validation_classification_reports.json").write_text(
        json.dumps({result["model"]: result["classification_report"] for result in results}, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUTPUT_DIR / "validation_confusion_matrices.json").write_text(
        json.dumps(
            {
                result["model"]: {
                    "labels_order": CLASS_NAMES,
                    "rows_actual_columns_predicted": result["confusion_matrix"],
                }
                for result in results
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    calibration_rows = []
    selected_probabilities = best_candidate["probabilities"]
    calibration_errors = {}
    figure, axis = plt.subplots(figsize=(7, 7))
    axis.plot([0, 1], [0, 1], linestyle="--", color="black", linewidth=1, label="Perfect calibration")
    for column_index, label in enumerate(CLASS_NAMES):
        positive = (y_validation.to_numpy() == label).astype(int)
        scores = selected_probabilities[:, column_index]
        bin_edges = np.unique(np.quantile(scores, np.linspace(0, 1, 11)))
        bin_index = np.digitize(scores, bin_edges[1:-1], right=True) if len(bin_edges) > 1 else np.zeros(len(scores), dtype=int)
        weighted_error = 0.0
        plot_scores = []
        plot_rates = []
        for index in range(max(1, len(bin_edges) - 1)):
            members = bin_index == index
            count = int(members.sum())
            if count == 0:
                continue
            mean_score = float(scores[members].mean())
            observed_rate = float(positive[members].mean())
            weighted_error += count / len(scores) * abs(float(mean_score) - float(observed_rate))
            plot_scores.append(mean_score)
            plot_rates.append(observed_rate)
            calibration_rows.append(
                {
                    "quality_class": label,
                    "bin": index + 1,
                    "count": count,
                    "mean_predicted_probability": float(mean_score),
                    "observed_fraction": float(observed_rate),
                }
            )
        calibration_errors[label] = weighted_error
        axis.plot(plot_scores, plot_rates, marker="o", label=label)
    axis.set(
        title=f"One-vs-rest reliability: {best_candidate['model']}",
        xlabel="Mean predicted probability",
        ylabel="Observed fraction positive",
        xlim=(0, 1),
        ylim=(0, 1),
    )
    axis.grid(alpha=0.25)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "validation_reliability.png", dpi=160)
    plt.close(figure)
    pd.DataFrame(calibration_rows).to_csv(OUTPUT_DIR / "validation_reliability_bins.csv", index=False)
    (OUTPUT_DIR / "validation_probability_metrics.json").write_text(
        json.dumps(
            {
                "model": best_candidate["model"],
                "validation_multiclass_brier_score": best_candidate["multiclass_brier"],
                "validation_log_loss": best_candidate["log_loss"],
                "one_vs_rest_expected_calibration_error_10_quantile_bins": calibration_errors,
                "note": "Validation reliability assessment only; not a calibration transform. Do not display probabilities as calibrated without further evidence.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report_lines = [
        "# EDA và baseline - Theme 3",
        "",
        "Lần chạy này chỉ đọc `train.csv` và `validation.csv`; không mở và không đánh giá `test.csv`.",
        "",
        f"- Số feature numeric: {len(feature_columns)}",
        f"- Train: {len(train):,} dòng / {train['VYP batch'].nunique():,} batch",
        f"- Validation: {len(validation):,} dòng / {validation['VYP batch'].nunique():,} batch",
        f"- Số ô feature bị thiếu: train {int(x_train.isna().sum().sum())}, validation {int(x_validation.isna().sum().sum())}",
        f"- Lớp nhiều nhất trong train: `{y_train.value_counts().idxmax()}`",
        f"- Ứng viên không-baseline tốt nhất theo macro-F1 validation, rồi balanced accuracy: `{best_candidate['model']}`",
        f"- Macro-F1 validation: {best_candidate['macro_f1']:.4f}; majority baseline: {majority_result['macro_f1']:.4f}",
        f"- scikit-learn: {sklearn.__version__}",
        "",
        "## Phân bố lớp",
        "",
        "| Split | Lop | So dong | Ti le | So batch |",
        "|---|---|---:|---:|---:|",
    ]
    for row in distribution.to_dict(orient="records"):
        report_lines.append(
            f"| {row['split']} | `{row['quality_class']}` | {row['rows']:,} | {row['proportion']:.1%} | {row['batches']} |"
        )
    report_lines.extend(
        [
            "",
            "## Phân bố theo `Part` trong train",
            "",
            "| Part | Lop | So dong |",
            "|---|---|---:|",
        ]
    )
    for row in part_distribution.to_dict(orient="records"):
        report_lines.append(f"| {row['Part']} | `{row['quality_class']}` | {row['rows']:,} |")
    report_lines.extend(
        [
            "",
            "## So sánh trên validation",
            "",
            "| Model | Accuracy | Macro-F1 | Balanced accuracy | Log loss | Multiclass Brier |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for result in results:
        report_lines.append(
            f"| `{result['model']}` | {result['accuracy']:.4f} | {result['macro_f1']:.4f} | {result['balanced_accuracy']:.4f} | {result['log_loss']:.4f} | {result['multiclass_brier']:.4f} |"
        )
    report_lines.extend(
        [
            "",
            f"Ứng viên tốt nhất: `{best_candidate['model']}`. Metric theo lớp trên validation:",
            "",
            "| Lop | Precision | Recall | F1 | Support |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for label in CLASS_NAMES:
        values = selected_report[label]
        report_lines.append(
            f"| `{label}` | {values['precision']:.4f} | {values['recall']:.4f} | {values['f1-score']:.4f} | {int(values['support']):,} |"
        )
    report_lines.extend(
        [
            "",
            f"Log loss của ứng viên tốt nhất trên validation: {best_candidate['log_loss']:.4f} (lower is better). Đây là proper scoring rule, không thay thế kiểm tra reliability/calibration riêng.",
            f"Multiclass Brier score trên validation: {best_candidate['multiclass_brier']:.4f} (mean squared probability error, lower is better). ECE one-vs-rest theo 10 quantile bins: `{json.dumps(calibration_errors, ensure_ascii=False)}`.",
            "Reliability plot và bin counts là kiểm tra ngoài mẫu trên validation, không phải phép hiệu chỉnh xác suất. Chưa bật hiển thị xác suất trong demonstrator.",
            "",
            "Confusion matrix của ứng viên tốt nhất (hàng = nhãn thật, cột = nhãn dự đoán; thứ tự `good`, `low_bad`, `high_bad`):",
            "",
            "```text",
            str(np.asarray(best_candidate["confusion_matrix"], dtype=int)),
            "```",
        ]
    )
    report_lines.extend(
        [
            "",
            f"**Cảnh báo:** recall `low_bad` của `{best_candidate['model']}` là {low_bad_report['recall']:.4f} ({low_bad_correct}/{int(low_bad_report['support'])} mẫu validation được nhận đúng). Macro-F1 cao hơn majority baseline nhưng model chưa đủ tin cậy cho lớp này; cần phân tích lỗi/tuning trên train và validation trước khi xem test.",
            "",
            "Ứng viên được chọn tạm thời chỉ dựa trên validation, không phải kết quả cuối cùng. Class weights được tính trong `fit` trên train. `StandardScaler` của Logistic Regression nằm trong pipeline và chỉ fit trên train. Không dùng validation/test để fit preprocessing; chưa hiệu chỉnh xác suất.",
            "",
            "## Tệp EDA được tạo",
            "",
            "`class_distribution.csv`, `train_part_class_counts.csv`, `train_monthly_class_counts.csv`, `train_feature_summary_by_class.csv`, `feature_missingness.csv`, `validation_model_comparison.csv`, `validation_classification_reports.json`, `validation_confusion_matrices.json`, `validation_probability_metrics.json`, `validation_reliability_bins.csv` và bốn biểu đồ PNG.",
            "",
        ]
    )
    (OUTPUT_DIR / "eda_baseline_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(report_lines))


if __name__ == "__main__":
    main()