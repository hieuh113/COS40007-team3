"""Stage 4 of MLOps Retraining & Monitoring Pipeline: Post-Retraining Model Evaluation.

Evaluates the newly retrained Vegemite quality model on held-out evaluation data (`X_test.npy`),
compares baseline vs retrained performance, updates `artifacts/metrics/evaluation_metrics.json`,
and generates `reports/performance_report.html`.
"""

import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
LOGS_DIR = ROOT_DIR / "logs"
REPORTS_DIR = ROOT_DIR / "reports"


def score_estimator(estimator, x_eval: pd.DataFrame, y_eval: np.ndarray, class_names: list[str]) -> dict[str, object]:
    preds = estimator.predict(x_eval)
    probs = estimator.predict_proba(x_eval)
    acc = float(accuracy_score(y_eval, preds))
    macro_f1 = float(f1_score(y_eval, preds, average="macro", zero_division=0))
    bal_acc = float(balanced_accuracy_score(y_eval, preds))
    ll = float(log_loss(y_eval, probs, labels=list(range(len(class_names)))))
    actual_oh = np.column_stack([y_eval == i for i in range(len(class_names))]).astype(float)
    brier = float(np.mean(np.sum((probs - actual_oh) ** 2, axis=1)))

    pr_auc_map = {}
    for idx, cname in enumerate(class_names):
        bin_y = (y_eval == idx).astype(int)
        pr_auc_map[cname] = round(float(average_precision_score(bin_y, probs[:, idx])), 4) if bin_y.sum() > 0 else 0.0

    cm = confusion_matrix(y_eval, preds, labels=list(range(len(class_names)))).tolist()
    rep = classification_report(
        y_eval,
        preds,
        labels=list(range(len(class_names))),
        target_names=class_names,
        output_dict=True,
        zero_division=0,
    )
    return {
        "accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "balanced_accuracy": round(bal_acc, 4),
        "log_loss": round(ll, 4),
        "multiclass_brier": round(brier, 4),
        "pr_auc_by_class": pr_auc_map,
        "confusion_matrix": cm,
        "per_class_report": rep,
    }


def main() -> None:
    data_art_dir = ARTIFACTS_DIR / "data"
    prep_art_dir = ARTIFACTS_DIR / "preprocessing"
    models_art_dir = ARTIFACTS_DIR / "models"
    metrics_art_dir = ARTIFACTS_DIR / "metrics"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    x_train = np.load(data_art_dir / "X_train.npy")
    y_train = np.load(data_art_dir / "y_train.npy")
    x_test = np.load(data_art_dir / "X_test.npy")
    y_test = np.load(data_art_dir / "y_test.npy")

    meta = json.loads((prep_art_dir / "feature_columns.json").read_text(encoding="utf-8"))
    feature_columns: list[str] = meta["feature_columns"]
    class_names: list[str] = meta["class_names"]

    x_train_df = pd.DataFrame(x_train, columns=feature_columns)
    x_test_df = pd.DataFrame(x_test, columns=feature_columns)

    # Fit reference baseline (without new_data.csv) for A/B comparison
    baseline_est = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
    )
    baseline_est.fit(x_train_df, y_train)
    baseline_metrics = score_estimator(baseline_est, x_test_df, y_test, class_names)

    # Evaluate retrained model
    retrained_bundle = joblib.load(models_art_dir / "model.joblib")
    retrained_est = retrained_bundle["estimator"]
    retrained_metrics = score_estimator(retrained_est, x_test_df, y_test, class_names)

    ts_now = datetime.now().isoformat(timespec="seconds")
    delta_f1 = round(retrained_metrics["macro_f1"] - baseline_metrics["macro_f1"], 4)
    delta_acc = round(retrained_metrics["accuracy"] - baseline_metrics["accuracy"], 4)

    eval_summary = {
        "timestamp": ts_now,
        "model_version": retrained_bundle["model_version"],
        "evaluation_rows": int(len(x_test)),
        "baseline_before_retrain": baseline_metrics,
        "retrained_model_metrics": retrained_metrics,
        "comparison_delta": {
            "delta_accuracy": delta_acc,
            "delta_macro_f1": delta_f1,
            "delta_brier": round(retrained_metrics["multiclass_brier"] - baseline_metrics["multiclass_brier"], 4),
            "promotion_status": "PROMOTED_TO_CANDIDATE_REGISTRY" if delta_f1 >= -0.02 else "REQUIRES_HUMAN_REVIEW",
        },
    }

    (metrics_art_dir / "evaluation_metrics.json").write_text(
        json.dumps(eval_summary, indent=2) + "\n", encoding="utf-8"
    )

    with (LOGS_DIR / "training.log").open("a", encoding="utf-8") as lf:
        lf.write(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [EVALUATE] "
            f"Evaluated {retrained_bundle['model_version']} on {len(x_test)} holdout rows: "
            f"Macro-F1={retrained_metrics['macro_f1']:.4f} (Baseline={baseline_metrics['macro_f1']:.4f}, "
            f"Delta={delta_f1:+.4f}), Accuracy={retrained_metrics['accuracy']:.4f}.\n"
        )

    # Generate HTML Performance Report
    class_rows_html = []
    for cname in class_names:
        b_rep = baseline_metrics["per_class_report"][cname]
        r_rep = retrained_metrics["per_class_report"][cname]
        class_rows_html.append(
            f"<tr>"
            f"<td><strong>{cname}</strong></td>"
            f"<td>{int(r_rep['support'])}</td>"
            f"<td>{b_rep['precision']:.4f} &rarr; <strong>{r_rep['precision']:.4f}</strong></td>"
            f"<td>{b_rep['recall']:.4f} &rarr; <strong>{r_rep['recall']:.4f}</strong></td>"
            f"<td>{b_rep['f1-score']:.4f} &rarr; <strong>{r_rep['f1-score']:.4f}</strong></td>"
            f"<td>{baseline_metrics['pr_auc_by_class'][cname]:.4f} &rarr; <strong>{retrained_metrics['pr_auc_by_class'][cname]:.4f}</strong></td>"
            f"</tr>"
        )

    perf_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>COS40007 Theme 3 — MLOps Retraining Performance Report</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 24px; background: #f8fafc; color: #0f172a; }}
  .header {{ background: #0f172a; color: white; padding: 20px 24px; border-radius: 8px; margin-bottom: 20px; }}
  .cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }}
  .card {{ background: white; padding: 16px 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); border-left: 4px solid #16a34a; }}
  .card h3 {{ margin: 0 0 8px 0; font-size: 13px; color: #64748b; text-transform: uppercase; }}
  .card .val {{ font-size: 22px; font-weight: 700; color: #0f172a; }}
  table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 20px; }}
  th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid #e2e8f0; font-size: 14px; }}
  th {{ background: #f1f5f9; font-weight: 600; color: #334155; }}
</style>
</head>
<body>
  <div class="header">
    <h1 style="margin:0 0 6px 0;font-size:22px;">COS40007 Theme 3 — Post-Retraining Performance Report</h1>
    <div style="font-size:13px;color:#cbd5e1;">Model Version: {retrained_bundle["model_version"]} | Evaluated at: {ts_now} | Holdout Rows: {len(x_test):,}</div>
  </div>
  <div class="cards">
    <div class="card"><h3>Holdout Accuracy</h3><div class="val">{retrained_metrics["accuracy"]:.4f} ({delta_acc:+.4f})</div></div>
    <div class="card"><h3>Holdout Macro-F1</h3><div class="val">{retrained_metrics["macro_f1"]:.4f} ({delta_f1:+.4f})</div></div>
    <div class="card"><h3>Balanced Accuracy</h3><div class="val">{retrained_metrics["balanced_accuracy"]:.4f}</div></div>
    <div class="card"><h3>Multiclass Brier / LogLoss</h3><div class="val">{retrained_metrics["multiclass_brier"]:.4f} / {retrained_metrics["log_loss"]:.4f}</div></div>
  </div>
  <h3>Per-Class Comparison (Baseline Before Retrain &rarr; Retrained Model)</h3>
  <table>
    <thead>
      <tr><th>Quality Class</th><th>Support</th><th>Precision (Base &rarr; New)</th><th>Recall (Base &rarr; New)</th><th>F1-Score (Base &rarr; New)</th><th>PR-AUC (Base &rarr; New)</th></tr>
    </thead>
    <tbody>
      {"".join(class_rows_html)}
    </tbody>
  </table>
</body>
</html>
"""
    (REPORTS_DIR / "performance_report.html").write_text(perf_html, encoding="utf-8")
    print(f"[EVALUATE] Saved reports/performance_report.html and artifacts/metrics/evaluation_metrics.json")


if __name__ == "__main__":
    main()
