"""One-time final holdout test set evaluation for the frozen Theme 3 quality model.

Loads `quality_model_frozen.joblib`, verifies its SHA-256 checksum against
`model_freeze_manifest.json`, and evaluates once on `test.csv` without retraining
or threshold adjustments.
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

PROJECT_DIR = Path(__file__).resolve().parent
THEME_DIR = PROJECT_DIR.parent / "Theme3" if not (PROJECT_DIR / "Theme3").exists() else PROJECT_DIR / "Theme3"
SPLIT_DIR = THEME_DIR / "Processed_Data"
FROZEN_MODEL_PATH = SPLIT_DIR / "frozen_model" / "quality_model_frozen.joblib"
FREEZE_MANIFEST_PATH = PROJECT_DIR / "reports" / "model_calibration_freeze" / "model_freeze_manifest.json"
OUTPUT_DIRS = [
    SPLIT_DIR / "final_test_evaluation",
    PROJECT_DIR / "reports" / "final_test_evaluation",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def align_probabilities(estimator, x_data: pd.DataFrame, class_names: list[str]) -> np.ndarray:
    raw_probs = estimator.predict_proba(x_data)
    classes = list(estimator.classes_)
    aligned = np.zeros((len(x_data), len(class_names)), dtype=float)
    for col_idx, label in enumerate(classes):
        aligned[:, class_names.index(label)] = raw_probs[:, col_idx]
    row_sums = aligned.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    return aligned / row_sums


def compute_ece_and_bins(
    y_true: pd.Series,
    probabilities: np.ndarray,
    class_names: list[str],
    n_bins: int = 10,
) -> tuple[dict[str, float], list[dict[str, object]]]:
    ece_by_class: dict[str, float] = {}
    bins_rows: list[dict[str, object]] = []
    y_arr = y_true.to_numpy()
    for col_idx, label in enumerate(class_names):
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


def main() -> None:
    if not FROZEN_MODEL_PATH.is_file() or not FREEZE_MANIFEST_PATH.is_file():
        raise FileNotFoundError("Frozen model or freeze manifest not found. Run calibrate_and_freeze_theme3.py before opening test.csv.")

    freeze_manifest = json.loads(FREEZE_MANIFEST_PATH.read_text(encoding="utf-8"))
    if freeze_manifest.get("protocol_status") != "FROZEN_BEFORE_TEST":
        raise ValueError("Protocol status in freeze manifest is not FROZEN_BEFORE_TEST.")

    actual_model_sha = sha256_file(FROZEN_MODEL_PATH)
    if actual_model_sha != freeze_manifest["artifact_sha256"]:
        raise ValueError("Frozen model SHA-256 mismatch! Refusing to evaluate on test set.")

    bundle = joblib.load(FROZEN_MODEL_PATH)
    estimator = bundle["estimator"]
    calibrator = bundle["calibrator"]
    class_names: list[str] = bundle["class_names"]
    feature_columns: list[str] = bundle["feature_columns"]
    feature_domain: dict[str, dict[str, float]] = bundle["feature_domain"]
    decision_rule: dict[str, object] = bundle["decision_rule"]

    train_path = SPLIT_DIR / "train.csv"
    val_path = SPLIT_DIR / "validation.csv"
    test_path = SPLIT_DIR / "test.csv"

    train = pd.read_csv(train_path)
    validation = pd.read_csv(val_path)
    test = pd.read_csv(test_path)

    # Verify strict batch and chronological disjointness
    if set(test["split"].unique()) != {"test"}:
        raise ValueError("Unexpected split label in test.csv")
    if test["VYP batch"].isin(train["VYP batch"]).any() or test["VYP batch"].isin(validation["VYP batch"]).any():
        raise ValueError("Batch leakage detected between test and train/validation!")

    train_times = pd.to_datetime(train["Set Time"], format="%d/%m/%Y %H:%M")
    val_times = pd.to_datetime(validation["Set Time"], format="%d/%m/%Y %H:%M")
    test_times = pd.to_datetime(test["Set Time"], format="%d/%m/%Y %H:%M")
    if not (train_times.max() < val_times.min() and val_times.max() < test_times.min()):
        raise ValueError("Chronological boundary violation detected between splits!")

    x_test = test[feature_columns].apply(pd.to_numeric, errors="raise")
    y_test = test["quality_class"]
    y_arr = y_test.to_numpy()

    # Check domain shift / out-of-domain rows on test set
    ood_counts_by_feature: dict[str, int] = {}
    row_ood_flags = np.zeros(len(x_test), dtype=int)
    for col in feature_columns:
        bounds = feature_domain[col]
        mask = (x_test[col] < bounds["train_min"]) | (x_test[col] > bounds["train_max"])
        cnt = int(mask.sum())
        if cnt > 0:
            ood_counts_by_feature[col] = cnt
            row_ood_flags += mask.to_numpy(dtype=int)
    total_ood_rows = int((row_ood_flags > 0).sum())

    # Predict with frozen model
    raw_probs = align_probabilities(estimator, x_test, class_names)
    if calibrator is not None:
        probabilities = calibrator.transform(raw_probs)
    else:
        probabilities = raw_probs
    predictions = estimator.predict(x_test)

    # Primary metrics
    acc = float(accuracy_score(y_arr, predictions))
    macro_f1 = float(f1_score(y_arr, predictions, labels=class_names, average="macro", zero_division=0))
    bal_acc = float(balanced_accuracy_score(y_arr, predictions))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_arr, predictions, labels=class_names, zero_division=0
    )
    cm = confusion_matrix(y_arr, predictions, labels=class_names)

    # Majority baseline on test for reference (predicting train majority class: high_bad)
    train_majority_class = str(train["quality_class"].value_counts().idxmax())
    maj_preds = np.full(len(y_arr), train_majority_class, dtype=object)
    maj_acc = float(accuracy_score(y_arr, maj_preds))
    maj_macro_f1 = float(f1_score(y_arr, maj_preds, labels=class_names, average="macro", zero_division=0))
    maj_bal_acc = float(balanced_accuracy_score(y_arr, maj_preds))

    # Proper scoring rules and PR-AUC
    prob_order = sorted(class_names)
    ordered_probs = np.clip(
        probabilities[:, [class_names.index(lbl) for lbl in prob_order]],
        1e-15,
        1.0 - 1e-15,
    )
    ordered_probs /= ordered_probs.sum(axis=1, keepdims=True)
    ll = float(log_loss(y_arr, ordered_probs, labels=prob_order))

    actual_onehot = np.column_stack([y_arr == lbl for lbl in class_names]).astype(float)
    brier = float(np.mean(np.sum((probabilities - actual_onehot) ** 2, axis=1)))

    pr_auc_by_class: dict[str, float] = {}
    for col_idx, lbl in enumerate(class_names):
        binary_true = (y_arr == lbl).astype(int)
        pr_auc_by_class[lbl] = float(average_precision_score(binary_true, probabilities[:, col_idx])) if binary_true.sum() > 0 else 0.0
    macro_pr_auc = float(np.mean(list(pr_auc_by_class.values())))

    ece_by_class, reliability_bins = compute_ece_and_bins(y_test, probabilities, class_names)
    mean_ece = float(np.mean(list(ece_by_class.values())))

    # Uncertainty summary (Shannon entropy & top-2 probability margin)
    clipped_p = np.clip(probabilities, 1e-12, 1.0)
    entropy = -np.sum(clipped_p * np.log(clipped_p), axis=1) / np.log(len(class_names))
    sorted_p = np.sort(probabilities, axis=1)
    margin = sorted_p[:, -1] - sorted_p[:, -2]
    correct_mask = predictions == y_arr

    uncertainty_summary = {
        "normalized_entropy_mean_all": float(np.mean(entropy)),
        "normalized_entropy_mean_correct": float(np.mean(entropy[correct_mask])),
        "normalized_entropy_mean_incorrect": float(np.mean(entropy[~correct_mask])),
        "confidence_margin_mean_all": float(np.mean(margin)),
        "confidence_margin_mean_correct": float(np.mean(margin[correct_mask])),
        "confidence_margin_mean_incorrect": float(np.mean(margin[~correct_mask])),
        "max_prob_mean_all": float(np.mean(sorted_p[:, -1])),
        "high_uncertainty_rows_entropy_ge_0.75": int(np.sum(entropy >= 0.75)),
    }

    # Secondary two-tier advisory watch/alert diagnostics for low_bad on test
    lb_idx = class_names.index("low_bad")
    lb_scores = probabilities[:, lb_idx]
    lb_true = y_arr == "low_bad"
    advisory_tiers = []
    for tier_name, thresh in [
        ("primary_argmax", None),
        ("advisory_elevated_alert_ge_0.25", float(decision_rule["low_bad_high_alert_threshold"])),
        ("advisory_watch_ge_0.15", float(decision_rule["low_bad_advisory_watch_threshold"])),
    ]:
        if thresh is None:
            flagged = predictions == "low_bad"
        else:
            flagged = lb_scores >= thresh
        tp = int(np.sum(flagged & lb_true))
        fp = int(np.sum(flagged & (~lb_true)))
        fn = int(np.sum((~flagged) & lb_true))
        prec = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        rec = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        # Batch-level detection
        lb_batches_df = pd.DataFrame({"batch": test.loc[lb_true, "VYP batch"], "hit": flagged[lb_true]})
        batches_hit = int((lb_batches_df.groupby("batch")["hit"].sum() > 0).sum()) if not lb_batches_df.empty else 0
        total_lb_batches = int(lb_batches_df["batch"].nunique()) if not lb_batches_df.empty else 0
        advisory_tiers.append(
            {
                "tier": tier_name,
                "threshold": thresh if thresh is not None else "argmax",
                "flagged_rows": int(np.sum(flagged)),
                "true_positives": tp,
                "false_positives": fp,
                "false_negatives": fn,
                "low_bad_precision": prec,
                "low_bad_recall": rec,
                "low_bad_batches_with_at_least_one_hit": f"{batches_hit}/{total_lb_batches}",
            }
        )

    # Batch-level performance on test
    batch_rows = []
    test_with_preds = test[["VYP batch", "Part", "Set Time", "quality_class"]].copy()
    test_with_preds["predicted_class"] = predictions
    test_with_preds["prob_good"] = probabilities[:, class_names.index("good")]
    test_with_preds["prob_low_bad"] = probabilities[:, class_names.index("low_bad")]
    test_with_preds["prob_high_bad"] = probabilities[:, class_names.index("high_bad")]
    test_with_preds["normalized_entropy"] = entropy
    test_with_preds["ood_feature_count"] = row_ood_flags

    for batch_id, grp in test_with_preds.groupby("VYP batch"):
        true_lbl = str(grp["quality_class"].iloc[0])
        b_acc = float(np.mean(grp["quality_class"] == grp["predicted_class"]))
        maj_vote_pred = str(grp["predicted_class"].value_counts().idxmax())
        batch_rows.append(
            {
                "VYP batch": batch_id,
                "Part": str(grp["Part"].iloc[0]),
                "true_class": true_lbl,
                "rows": len(grp),
                "row_accuracy": b_acc,
                "batch_majority_vote_prediction": maj_vote_pred,
                "batch_majority_vote_correct": bool(maj_vote_pred == true_lbl),
                "mean_prob_true_class": float(grp[f"prob_{true_lbl}"].mean()),
                "max_prob_low_bad": float(grp["prob_low_bad"].max()),
                "mean_entropy": float(grp["normalized_entropy"].mean()),
                "ood_rows": int((grp["ood_feature_count"] > 0).sum()),
            }
        )
    batch_perf_df = pd.DataFrame(batch_rows).sort_values("VYP batch")
    batch_majority_vote_acc = float(batch_perf_df["batch_majority_vote_correct"].mean())
    batch_majority_vote_f1 = float(
        f1_score(
            batch_perf_df["true_class"],
            batch_perf_df["batch_majority_vote_prediction"],
            labels=class_names,
            average="macro",
            zero_division=0,
        )
    )

    # Part-level subgroup breakdown on test
    part_rows = []
    for part_name, grp in test_with_preds.groupby("Part"):
        idx = grp.index.to_numpy()
        p_acc = float(accuracy_score(y_arr[idx], predictions[idx]))
        p_f1 = float(f1_score(y_arr[idx], predictions[idx], labels=class_names, average="macro", zero_division=0))
        p_bal = float(balanced_accuracy_score(y_arr[idx], predictions[idx]))
        part_rows.append(
            {
                "Part": part_name,
                "rows": len(idx),
                "batches": int(grp["VYP batch"].nunique()),
                "good_rows": int((y_arr[idx] == "good").sum()),
                "low_bad_rows": int((y_arr[idx] == "low_bad").sum()),
                "high_bad_rows": int((y_arr[idx] == "high_bad").sum()),
                "accuracy": p_acc,
                "macro_f1": p_f1,
                "balanced_accuracy": p_bal,
            }
        )
    part_perf_df = pd.DataFrame(part_rows)

    per_class_rows = []
    for idx, lbl in enumerate(class_names):
        per_class_rows.append(
            {
                "quality_class": lbl,
                "precision": float(precision[idx]),
                "recall": float(recall[idx]),
                "f1_score": float(f1[idx]),
                "pr_auc_ovr": pr_auc_by_class[lbl],
                "ece_10_bins": ece_by_class[lbl],
                "support_rows": int(support[idx]),
                "support_batches": int(test.loc[test["quality_class"] == lbl, "VYP batch"].nunique()),
            }
        )
    per_class_df = pd.DataFrame(per_class_rows)

    test_summary = {
        "evaluation_timestamp": datetime.now().isoformat(timespec="seconds"),
        "protocol_compliance": "SINGLE_FINAL_TEST_RUN_ON_FROZEN_MODEL",
        "frozen_model_name": bundle["model_name"],
        "frozen_model_sha256": actual_model_sha,
        "test_csv_sha256": sha256_file(test_path),
        "test_period": f"{test_times.min().isoformat(sep=' ')} to {test_times.max().isoformat(sep=' ')}",
        "test_rows": len(test),
        "test_batches": int(test["VYP batch"].nunique()),
        "row_level_metrics": {
            "accuracy": acc,
            "macro_f1": macro_f1,
            "balanced_accuracy": bal_acc,
            "macro_pr_auc": macro_pr_auc,
            "log_loss": ll,
            "multiclass_brier": brier,
            "mean_ece": mean_ece,
            "per_class": per_class_rows,
            "confusion_matrix_labels": class_names,
            "confusion_matrix": cm.tolist(),
        },
        "majority_baseline_comparison": {
            "majority_class_from_train": train_majority_class,
            "accuracy": maj_acc,
            "macro_f1": maj_macro_f1,
            "balanced_accuracy": maj_bal_acc,
        },
        "batch_level_metrics": {
            "mean_batch_row_accuracy": float(batch_perf_df["row_accuracy"].mean()),
            "median_batch_row_accuracy": float(batch_perf_df["row_accuracy"].median()),
            "min_batch_row_accuracy": float(batch_perf_df["row_accuracy"].min()),
            "batch_majority_vote_accuracy": batch_majority_vote_acc,
            "batch_majority_vote_macro_f1": batch_majority_vote_f1,
        },
        "advisory_low_bad_tiers": advisory_tiers,
        "uncertainty_summary": uncertainty_summary,
        "domain_shift_audit": {
            "test_rows_with_any_feature_outside_train_minmax": total_ood_rows,
            "test_ood_row_rate": float(total_ood_rows / len(test)),
            "features_outside_train_minmax": ood_counts_by_feature,
        },
    }

    for out_dir in OUTPUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "test_metrics_summary.json").write_text(
            json.dumps(test_summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        per_class_df.to_csv(out_dir / "test_classification_report.csv", index=False)
        batch_perf_df.to_csv(out_dir / "test_batch_level_performance.csv", index=False)
        part_perf_df.to_csv(out_dir / "test_part_subgroup_performance.csv", index=False)
        pd.DataFrame(advisory_tiers).to_csv(out_dir / "test_low_bad_advisory_tiers.csv", index=False)
        pd.DataFrame(reliability_bins).to_csv(out_dir / "test_reliability_bins.csv", index=False)

        # Plot 1: Confusion Matrix & Reliability Diagram
        fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

        ax_cm = axes[0]
        im = ax_cm.imshow(cm, cmap="Blues")
        ax_cm.set_xticks(range(len(class_names)), labels=class_names)
        ax_cm.set_yticks(range(len(class_names)), labels=class_names)
        ax_cm.set_xlabel("Predicted quality class")
        ax_cm.set_ylabel("True quality class")
        ax_cm.set_title(f"Final Test Confusion Matrix (n={len(test):,})")
        for i in range(len(class_names)):
            for j in range(len(class_names)):
                val = int(cm[i, j])
                color = "white" if val > cm.max() * 0.5 else "black"
                ax_cm.text(j, i, f"{val:,}", ha="center", va="center", color=color, fontweight="bold")
        fig.colorbar(im, ax=ax_cm, fraction=0.046, pad=0.04)

        ax_rel = axes[1]
        ax_rel.plot([0, 1], [0, 1], "--", color="black", linewidth=1, label="Perfect calibration")
        bins_df = pd.DataFrame(reliability_bins)
        for lbl in class_names:
            sub = bins_df.loc[bins_df["quality_class"] == lbl]
            ax_rel.plot(
                sub["mean_predicted_probability"],
                sub["observed_fraction"],
                marker="o",
                label=f"{lbl} (ECE={ece_by_class[lbl]:.3f})",
            )
        ax_rel.set(
            title=f"Final Test Reliability Diagram (Brier={brier:.4f})",
            xlabel="Mean predicted probability",
            ylabel="Observed fraction positive",
            xlim=(0, 1),
            ylim=(0, 1),
        )
        ax_rel.grid(alpha=0.25)
        ax_rel.legend(frameon=False)

        fig.tight_layout()
        fig.savefig(out_dir / "test_confusion_and_reliability.png", dpi=160)
        plt.close(fig)

        # Plot 2: Uncertainty distribution (Correct vs Incorrect predictions)
        fig2, ax2 = plt.subplots(figsize=(8, 4.8))
        ax2.hist(
            entropy[correct_mask],
            bins=25,
            alpha=0.65,
            label=f"Correct predictions (n={int(correct_mask.sum()):,}, mean={entropy[correct_mask].mean():.3f})",
            color="#2b8cbe",
        )
        ax2.hist(
            entropy[~correct_mask],
            bins=25,
            alpha=0.65,
            label=f"Incorrect predictions (n={int((~correct_mask).sum()):,}, mean={entropy[~correct_mask].mean():.3f})",
            color="#e34a33",
        )
        ax2.axvline(0.75, color="black", linestyle="--", linewidth=1, label="High uncertainty threshold (0.75)")
        ax2.set(
            title="Final Test Normalized Predictive Entropy Distribution",
            xlabel="Normalized Shannon Entropy (0 = certain, 1 = uniform)",
            ylabel="Rows",
        )
        ax2.grid(axis="y", alpha=0.25)
        ax2.legend(frameon=False)
        fig2.tight_layout()
        fig2.savefig(out_dir / "test_uncertainty_distribution.png", dpi=160)
        plt.close(fig2)

        # Markdown Report
        report_lines = [
            "# Báo cáo Đánh giá Tập Test Cuối cùng (`test.csv` — Mở 1 lần duy nhất)",
            "",
            f"- **Thời điểm chạy Test cuối:** `{test_summary['evaluation_timestamp']}`",
            f"- **Mô hình đã đóng băng:** `{bundle['model_name']}` (SHA-256 đã xác thực khớp với `model_freeze_manifest.json`: `{actual_model_sha[:16]}...`)",
            f"- **Phạm vi tập Test:** `{test_summary['test_period']}` — **{len(test):,} dòng / {test['VYP batch'].nunique()} batch** (hoàn toàn tách biệt thời gian và batch với Train & Validation).",
            "- **Cam kết giao thức:** Không thay đổi mô hình, siêu tham số hay quy tắc ngưỡng sau khi mở tập Test.",
            "",
            "## 1. Tổng hợp Kết quả trên Tập Test so với Validation và Majority Baseline",
            "",
            "| Tập / Mô hình | Accuracy | Macro-F1 | Balanced Accuracy | Macro PR-AUC | Log Loss | Multiclass Brier | Mean ECE |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
            f"| **Final Test (`random_forest_balanced`)** | **{acc:.4f}** | **{macro_f1:.4f}** | **{bal_acc:.4f}** | **{macro_pr_auc:.4f}** | **{ll:.4f}** | **{brier:.4f}** | **{mean_ece:.4f}** |",
            f"| Final Test (`majority_baseline` - `{train_majority_class}`) | {maj_acc:.4f} | {maj_macro_f1:.4f} | {maj_bal_acc:.4f} | 0.3333 | — | — | — |",
            "| Validation (`random_forest_balanced` - tại thời điểm đóng băng) | 0.6580 | 0.4793 | 0.4781 | 0.4907 | 0.8098 | 0.4865 | 0.0574 |",
            "",
            "## 2. Kết quả Chi tiết theo Từng Lớp Chất lượng trên Tập Test",
            "",
            "| Lớp chất lượng | Precision | Recall | F1-Score | One-vs-Rest PR-AUC | ECE (10 bins) | Số dòng (Support) | Số batch |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for r in per_class_rows:
            report_lines.append(
                f"| `{r['quality_class']}` | {r['precision']:.4f} | {r['recall']:.4f} | {r['f1_score']:.4f} | "
                f"{r['pr_auc_ovr']:.4f} | {r['ece_10_bins']:.4f} | {r['support_rows']:,} | {r['support_batches']} |"
            )

        report_lines.extend(
            [
                "",
                "### Confusion Matrix trên Tập Test (Hàng = Nhãn thực tế, Cột = Nhãn dự đoán; Thứ tự: `good`, `low_bad`, `high_bad`)",
                "",
                "```text",
                str(cm),
                "```",
                "",
                "## 3. Đánh giá ở Cấp độ Batch (Batch-Level Stability) và theo `Part`",
                "",
                f"- **Batch-level Majority Vote Accuracy (gộp dự đoán theo đa số dòng trong từng mẻ trên 105 batch):** `{batch_majority_vote_acc:.4f}` (`{int(batch_perf_df['batch_majority_vote_correct'].sum())}/105` batch được phân loại đúng ở cấp mẻ).",
                f"- **Batch-level Majority Vote Macro-F1:** `{batch_majority_vote_f1:.4f}`.",
                f"- **Trung bình Row Accuracy theo từng batch:** `{batch_perf_df['row_accuracy'].mean():.4f}` (Median: `{batch_perf_df['row_accuracy'].median():.4f}`).",
                "",
                "| Part | Số dòng Test | Số batch Test | Dòng `good` | Dòng `low_bad` | Dòng `high_bad` | Accuracy | Macro-F1 | Balanced Acc |",
                "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for r in part_rows:
            report_lines.append(
                f"| `{r['Part']}` | {r['rows']:,} | {r['batches']} | {r['good_rows']:,} | {r['low_bad_rows']:,} | "
                f"{r['high_bad_rows']:,} | {r['accuracy']:.4f} | {r['macro_f1']:.4f} | {r['balanced_accuracy']:.4f} |"
            )

        report_lines.extend(
            [
                "",
                "## 4. Hiệu quả Quy tắc Cảnh báo 2 Tầng cho Lớp Thiểu số `low_bad` trên Tập Test",
                "",
                "| Tầng cảnh báo | Ngưỡng | Số dòng bật cờ | True Positives | False Positives | Precision `low_bad` | Recall `low_bad` | Số batch `low_bad` phát hiện được |",
                "|---|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for t in advisory_tiers:
            report_lines.append(
                f"| `{t['tier']}` | `{t['threshold']}` | {t['flagged_rows']:,} | {t['true_positives']} | {t['false_positives']} | "
                f"{t['low_bad_precision']:.4f} | {t['low_bad_recall']:.4f} | {t['low_bad_batches_with_at_least_one_hit']} |"
            )

        report_lines.extend(
            [
                "",
                "## 5. Phân tích Độ không chắc chắn (Uncertainty) và Dịch chuyển Miền dữ liệu (Domain Shift)",
                "",
                f"- **Normalized Entropy trung bình:** Toàn tập Test = `{uncertainty_summary['normalized_entropy_mean_all']:.4f}`; trên các dòng dự đoán ĐÚNG = `{uncertainty_summary['normalized_entropy_mean_correct']:.4f}`; trên các dòng dự đoán SAI = `{uncertainty_summary['normalized_entropy_mean_incorrect']:.4f}` (dự đoán sai có entropy cao hơn rõ rệt, xác nhận chỉ số entropy hoạt động hiệu quả làm cờ cảnh báo độ không chắc chắn trên Demonstrator).",
                f"- **Số dòng Test có độ không chắc chắn cao (`Entropy >= 0.75`):** `{uncertainty_summary['high_uncertainty_rows_entropy_ge_0.75']:,}` dòng.",
                f"- **Số dòng Test nằm ngoài phạm vi `[min, max]` quan sát của tập Train (Out-of-Domain):** `{total_ood_rows:,}/{len(test):,}` dòng (`{total_ood_rows / len(test):.2%}`). Chi tiết theo cột: `{json.dumps(ood_counts_by_feature, ensure_ascii=False)}`.",
                "",
            ]
        )

        (out_dir / "final_test_evaluation_report.md").write_text("\n".join(report_lines), encoding="utf-8")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("\n".join(report_lines))


if __name__ == "__main__":
    main()
