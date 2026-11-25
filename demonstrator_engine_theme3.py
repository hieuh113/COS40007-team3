"""Core engine and business logic for the COS40007 Theme 3 AI Demonstrator.

Provides:
- Loading of the frozen quality model bundle and freeze/test manifests.
- Domain & out-of-distribution (OOD) guardrails against training feature bounds.
- Quality prediction, calibrated probability, normalized Shannon entropy, and two-tier low_bad risk warnings.
- Gate-controlled Setpoint (SP) readiness & Advisory What-If Candidate SP Ranking (single-SP and historical good combinations).
- Downtime readiness status & exploratory trend outlier screen loaders.
- Persistent Operator Approval / Rejection Audit Logger (`operator_audit_log.csv`).
"""

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
THEME_DIR = PROJECT_DIR.parent / "Theme3" if not (PROJECT_DIR / "Theme3").exists() else PROJECT_DIR / "Theme3"
SPLIT_DIR = THEME_DIR / "Processed_Data"
FROZEN_MODEL_PATH = SPLIT_DIR / "frozen_model" / "quality_model_frozen.joblib"
FREEZE_MANIFEST_PATH = PROJECT_DIR / "reports" / "model_calibration_freeze" / "model_freeze_manifest.json"
TEST_SUMMARY_PATH = PROJECT_DIR / "reports" / "final_test_evaluation" / "test_metrics_summary.json"
SP_READINESS_PATH = PROJECT_DIR / "reports" / "setpoint_readiness" / "setpoint_readiness.json"
DT_READINESS_PATH = PROJECT_DIR / "reports" / "downtime_readiness" / "downtime_readiness.json"
AUTHORIZED_BOUNDS_PATH = PROJECT_DIR / "approved_operating_bounds.json"
AUDIT_LOG_PATH = PROJECT_DIR / "reports" / "operator_audit_log.csv"

SP_COLUMNS = [
    "FFTE Feed solids SP",
    "FFTE Production solids SP",
    "FFTE Steam pressure SP",
    "TFE Out flow SP",
    "TFE Production solids SP",
    "TFE Vacuum pressure SP",
    "TFE Steam pressure SP",
]


def load_frozen_bundle() -> dict[str, object]:
    if not FROZEN_MODEL_PATH.is_file():
        raise FileNotFoundError(f"Frozen model not found at {FROZEN_MODEL_PATH}. Run calibrate_and_freeze_theme3.py first.")
    return joblib.load(FROZEN_MODEL_PATH)


def load_json_report(path: Path) -> dict[str, object]:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def check_feature_domain(
    input_row: dict[str, float],
    feature_domain: dict[str, dict[str, float]],
) -> dict[str, object]:
    missing_features: list[str] = []
    ood_minmax_features: list[dict[str, object]] = []
    outside_q01_q99_features: list[dict[str, object]] = []

    for col, bounds in feature_domain.items():
        val = input_row.get(col, None)
        if val is None or (isinstance(val, float) and np.isnan(val)):
            missing_features.append(col)
            continue
        fval = float(val)
        if fval < bounds["train_min"] or fval > bounds["train_max"]:
            ood_minmax_features.append(
                {
                    "feature": col,
                    "value": fval,
                    "train_min": bounds["train_min"],
                    "train_max": bounds["train_max"],
                    "is_setpoint": bounds.get("is_setpoint", False),
                }
            )
        elif fval < bounds["train_q01"] or fval > bounds["train_q99"]:
            outside_q01_q99_features.append(
                {
                    "feature": col,
                    "value": fval,
                    "train_q01": bounds["train_q01"],
                    "train_q99": bounds["train_q99"],
                    "is_setpoint": bounds.get("is_setpoint", False),
                }
            )

    if missing_features:
        domain_status = "INVALID_MISSING_INPUT"
    elif ood_minmax_features:
        domain_status = "OUT_OF_DOMAIN_EXTRAPOLATION_RISK"
    elif outside_q01_q99_features:
        domain_status = "TAIL_DOMAIN_CAUTION"
    else:
        domain_status = "IN_DOMAIN_SUPPORTED"

    return {
        "domain_status": domain_status,
        "missing_features": missing_features,
        "ood_minmax_features": ood_minmax_features,
        "outside_q01_q99_features": outside_q01_q99_features,
    }


def predict_quality_state(
    bundle: dict[str, object],
    input_row: dict[str, float],
) -> dict[str, object]:
    feature_columns: list[str] = bundle["feature_columns"]
    class_names: list[str] = bundle["class_names"]
    estimator = bundle["estimator"]
    calibrator = bundle["calibrator"]
    decision_rule: dict[str, object] = bundle["decision_rule"]
    feature_domain: dict[str, dict[str, float]] = bundle["feature_domain"]

    domain_check = check_feature_domain(input_row, feature_domain)
    if domain_check["missing_features"]:
        return {
            "success": False,
            "error": f"Missing required features: {domain_check['missing_features']}",
            "domain_check": domain_check,
        }

    x_df = pd.DataFrame([{col: float(input_row[col]) for col in feature_columns}])
    raw_probs = estimator.predict_proba(x_df)
    est_classes = list(estimator.classes_)
    aligned = np.zeros((1, len(class_names)), dtype=float)
    for col_idx, lbl in enumerate(est_classes):
        aligned[0, class_names.index(lbl)] = raw_probs[0, col_idx]

    if calibrator is not None:
        probs = calibrator.transform(aligned)[0]
    else:
        probs = aligned[0]

    pred_class = str(estimator.predict(x_df)[0])
    prob_map = {lbl: float(probs[idx]) for idx, lbl in enumerate(class_names)}

    clipped_p = np.clip(probs, 1e-12, 1.0)
    norm_entropy = float(-np.sum(clipped_p * np.log(clipped_p)) / np.log(len(class_names)))
    sorted_p = np.sort(probs)
    margin = float(sorted_p[-1] - sorted_p[-2])

    p_low_bad = prob_map["low_bad"]
    watch_thresh = float(decision_rule["low_bad_advisory_watch_threshold"])
    alert_thresh = float(decision_rule["low_bad_high_alert_threshold"])
    if p_low_bad >= alert_thresh:
        low_bad_risk_tier = "ELEVATED_ALERT (>= 0.25)"
    elif p_low_bad >= watch_thresh:
        low_bad_risk_tier = "ADVISORY_WATCH (>= 0.15)"
    else:
        low_bad_risk_tier = "NORMAL (< 0.15)"

    high_uncertainty = norm_entropy >= 0.75 or domain_check["domain_status"] == "OUT_OF_DOMAIN_EXTRAPOLATION_RISK"

    return {
        "success": True,
        "predicted_class": pred_class,
        "probabilities": prob_map,
        "normalized_entropy": norm_entropy,
        "confidence_margin": margin,
        "max_probability": float(sorted_p[-1]),
        "low_bad_risk_tier": low_bad_risk_tier,
        "high_uncertainty_flag": bool(high_uncertainty),
        "domain_check": domain_check,
        "prediction_timestamp": datetime.now().isoformat(timespec="seconds"),
        "model_name": bundle["model_name"],
        "calibration_method": bundle["calibration_method"],
    }


def check_authorized_sp_bounds() -> dict[str, object]:
    if not AUTHORIZED_BOUNDS_PATH.is_file():
        return {
            "gate_status": "NOT_APPROVED",
            "operational_ranking_allowed": False,
            "reason": "No authorized `approved_operating_bounds.json` found. Operational SP ranking is blocked by safety gate.",
            "bounds": None,
        }
    try:
        data = json.loads(AUTHORIZED_BOUNDS_PATH.read_text(encoding="utf-8"))
        for sp in SP_COLUMNS:
            item = data.get(sp)
            if (
                not isinstance(item, dict)
                or item.get("authorized") is not True
                or not item.get("source")
                or not isinstance(item.get("min"), (int, float))
                or not isinstance(item.get("max"), (int, float))
                or item["min"] >= item["max"]
            ):
                return {
                    "gate_status": "NOT_APPROVED",
                    "operational_ranking_allowed": False,
                    "reason": f"Bounds file incomplete or unauthorized for `{sp}`.",
                    "bounds": None,
                }
        return {
            "gate_status": "APPROVED",
            "operational_ranking_allowed": True,
            "reason": "All 7 SP bounds verified from authorized file.",
            "bounds": data,
        }
    except Exception as exc:
        return {
            "gate_status": "NOT_APPROVED",
            "operational_ranking_allowed": False,
            "reason": f"Error reading bounds file: {exc}",
            "bounds": None,
        }


def rank_what_if_sp_candidates(
    bundle: dict[str, object],
    current_row: dict[str, float],
    part_name: str,
    train_df: pd.DataFrame | None = None,
    custom_bounds: dict[str, tuple[float, float]] | None = None,
    n_grid_steps: int = 5,
    top_k: int = 10,
) -> dict[str, object]:
    """Rank advisory SP candidates while keeping all 23 PV/sensor features and Part fixed.

    Follows ACADEMIC_EVIDENCE_FOR_SP_APPROVAL.md:
    1. Single-SP sensitivity grid within intersection of envelope and training support (q01-q99).
    2. Historical empirical good-batch SP combinations observed for the same Part in training data.
    """
    feature_columns: list[str] = bundle["feature_columns"]
    class_names: list[str] = bundle["class_names"]
    estimator = bundle["estimator"]
    calibrator = bundle["calibrator"]
    feature_domain: dict[str, dict[str, float]] = bundle["feature_domain"]

    baseline_pred = predict_quality_state(bundle, current_row)
    if not baseline_pred["success"]:
        return {"success": False, "error": baseline_pred["error"]}

    base_p_good = baseline_pred["probabilities"]["good"]
    base_p_low_bad = baseline_pred["probabilities"]["low_bad"]
    base_p_high_bad = baseline_pred["probabilities"]["high_bad"]

    candidate_records: list[dict[str, object]] = []

    # A. One-SP-at-a-time step grid within model support (q01 to q99) or custom_bounds
    for sp_col in SP_COLUMNS:
        dom = feature_domain[sp_col]
        if custom_bounds and sp_col in custom_bounds:
            low_b = max(float(custom_bounds[sp_col][0]), dom["train_min"])
            high_b = min(float(custom_bounds[sp_col][1]), dom["train_max"])
            envelope_source = "Custom Demo Bounds ∩ Train Support"
        else:
            low_b = dom["train_q01"]
            high_b = dom["train_q99"]
            envelope_source = "Train Historical Support (q01–q99)"

        if low_b >= high_b:
            continue

        grid_values = np.unique(np.round(np.linspace(low_b, high_b, n_grid_steps), 3))
        cur_val = float(current_row[sp_col])
        for cand_val in grid_values:
            if abs(float(cand_val) - cur_val) < 1e-6:
                continue
            mod_row = {col: float(current_row[col]) for col in feature_columns}
            mod_row[sp_col] = float(cand_val)
            delta = float(cand_val) - cur_val
            candidate_records.append(
                {
                    "candidate_type": "Single-SP Step (One change at a time)",
                    "changed_setpoints": sp_col,
                    "current_value_summary": f"{sp_col}: {cur_val:.2f}",
                    "candidate_value_summary": f"{sp_col}: {float(cand_val):.2f}",
                    "delta_summary": f"{delta:+.2f}",
                    "envelope_source": envelope_source,
                    "row": mod_row,
                }
            )

    # B. Historical unique SP profiles from training good batches for the same Part
    if train_df is not None and not train_df.empty:
        sub_good = train_df.loc[(train_df["Part"] == part_name) & (train_df["quality_class"] == "good"), SP_COLUMNS]
        if not sub_good.empty:
            unique_profiles = sub_good.drop_duplicates().head(25)
            for idx, (_, sp_series) in enumerate(unique_profiles.iterrows(), start=1):
                mod_row = {col: float(current_row[col]) for col in feature_columns}
                changed_list = []
                delta_list = []
                for sp_col in SP_COLUMNS:
                    c_val = float(sp_series[sp_col])
                    orig_val = float(current_row[sp_col])
                    mod_row[sp_col] = c_val
                    if abs(c_val - orig_val) > 1e-4:
                        short_name = sp_col.replace(" SP", "")
                        changed_list.append(f"{short_name}={c_val:.1f}")
                        delta_list.append(f"{short_name}:{c_val - orig_val:+.1f}")
                if not changed_list:
                    continue
                candidate_records.append(
                    {
                        "candidate_type": f"Historical Good Profile ({part_name})",
                        "changed_setpoints": f"{len(changed_list)} SPs adjusted",
                        "current_value_summary": "Current 7-SP vector",
                        "candidate_value_summary": "; ".join(changed_list[:4]) + ("..." if len(changed_list) > 4 else ""),
                        "delta_summary": "; ".join(delta_list[:4]) + ("..." if len(delta_list) > 4 else ""),
                        "envelope_source": f"Train Verified Good Batch ({part_name})",
                        "row": mod_row,
                    }
                )

    if not candidate_records:
        return {
            "success": True,
            "baseline": baseline_pred,
            "candidates": [],
        }

    cand_df = pd.DataFrame([r["row"] for r in candidate_records])[feature_columns]
    raw_probs = estimator.predict_proba(cand_df)
    est_classes = list(estimator.classes_)
    aligned = np.zeros((len(cand_df), len(class_names)), dtype=float)
    for col_idx, lbl in enumerate(est_classes):
        aligned[:, class_names.index(lbl)] = raw_probs[:, col_idx]
    probs = calibrator.transform(aligned) if calibrator is not None else aligned
    preds = estimator.predict(cand_df)

    good_idx = class_names.index("good")
    lb_idx = class_names.index("low_bad")
    hb_idx = class_names.index("high_bad")

    scored_rows = []
    for i, rec in enumerate(candidate_records):
        p_g = float(probs[i, good_idx])
        p_lb = float(probs[i, lb_idx])
        p_hb = float(probs[i, hb_idx])
        p_row = np.clip(probs[i], 1e-12, 1.0)
        ent = float(-np.sum(p_row * np.log(p_row)) / np.log(len(class_names)))
        scored_rows.append(
            {
                "rank": 0,
                "candidate_type": rec["candidate_type"],
                "changed_setpoints": rec["changed_setpoints"],
                "current_sp": rec["current_value_summary"],
                "candidate_sp": rec["candidate_value_summary"],
                "delta_sp": rec["delta_summary"],
                "predicted_class": str(preds[i]),
                "prob_good": p_g,
                "delta_prob_good": p_g - base_p_good,
                "prob_low_bad": p_lb,
                "prob_high_bad": p_hb,
                "normalized_entropy": ent,
                "envelope_source": rec["envelope_source"],
                "advisory_status": "ADVISORY_SIMULATION_ONLY (NO PLC WRITE)",
                "full_sp_vector": {sp: rec["row"][sp] for sp in SP_COLUMNS},
            }
        )

    scored_rows.sort(key=lambda r: (r["prob_good"], -r["prob_low_bad"], -r["normalized_entropy"]), reverse=True)
    top_candidates = scored_rows[:top_k]
    for rank_idx, item in enumerate(top_candidates, start=1):
        item["rank"] = rank_idx

    return {
        "success": True,
        "baseline": {
            "predicted_class": baseline_pred["predicted_class"],
            "prob_good": base_p_good,
            "prob_low_bad": base_p_low_bad,
            "prob_high_bad": base_p_high_bad,
            "normalized_entropy": baseline_pred["normalized_entropy"],
        },
        "candidates": top_candidates,
        "total_evaluated": len(scored_rows),
    }


def map_feature_to_machine(feature_name: str) -> str:
    if feature_name.startswith("FFTE"):
        return "FFTE (Falling Film Tubular Evaporator)"
    if feature_name.startswith("TFE"):
        return "TFE (Thin Film Evaporator)"
    if "Extract" in feature_name:
        return "Extract Tank / Vat"
    return "General Process"


def diagnose_current_input_anomalies_by_machine(
    input_row: dict[str, float],
    train_df: pd.DataFrame,
    feature_domain: dict[str, dict[str, float]],
    robust_z_threshold: float = 4.5,
) -> dict[str, object]:
    """Compute exploratory sensor/SP anomaly diagnostics grouped by running system (FFTE, TFE, Extract Tank)
    for the current input snapshot using Robust Z-score (Median/MAD) and training domain boundaries.

    Explicitly labeled as Exploratory Sensor Anomaly Screening (not supervised downtime probability).
    """
    historical_dt_events = {
        "FFTE (Falling Film Tubular Evaporator)": 2,
        "TFE (Thin Film Evaporator)": 51,
        "Extract Tank / Vat": 8,
    }
    feature_rows: list[dict[str, object]] = []
    for col, dom in feature_domain.items():
        val = input_row.get(col, float("nan"))
        if val is None or np.isnan(float(val)):
            continue
        fval = float(val)
        s = pd.to_numeric(train_df[col], errors="coerce").dropna()
        med = float(s.median())
        mad = float((s - med).abs().median())
        iqr = float(s.quantile(0.75) - s.quantile(0.25))
        scale = 1.4826 * mad if mad > 1e-9 else (iqr / 1.349 if iqr > 1e-9 else float(s.std() or 1.0))
        robust_z = abs(fval - med) / scale if scale > 1e-9 else 0.0

        is_ood = fval < dom["train_min"] or fval > dom["train_max"]
        is_tail = (not is_ood) and (fval < dom["train_q01"] or fval > dom["train_q99"])
        is_robust_outlier = robust_z > robust_z_threshold

        if is_ood:
            severity = "HIGH_ANOMALY (Outside Train Min-Max)"
        elif is_robust_outlier:
            severity = f"ELEVATED_ANOMALY (Robust Z > {robust_z_threshold})"
        elif is_tail:
            severity = "MINOR_DEVIATION (Outside q01-q99)"
        else:
            severity = "NORMAL"

        feature_rows.append(
            {
                "machine_system": map_feature_to_machine(col),
                "feature": col,
                "role": "Setpoint (SP)" if dom.get("is_setpoint", False) else "Sensor / PV",
                "current_value": fval,
                "train_median": med,
                "train_q01_q99": f"[{dom['train_q01']:.2f}, {dom['train_q99']:.2f}]",
                "train_min_max": f"[{dom['train_min']:.2f}, {dom['train_max']:.2f}]",
                "robust_z_score": float(robust_z),
                "is_ood": bool(is_ood),
                "is_robust_outlier": bool(is_robust_outlier),
                "is_tail": bool(is_tail),
                "anomaly_status": severity,
            }
        )

    feat_df = pd.DataFrame(feature_rows)
    machine_summaries: list[dict[str, object]] = []
    for machine in [
        "FFTE (Falling Film Tubular Evaporator)",
        "TFE (Thin Film Evaporator)",
        "Extract Tank / Vat",
    ]:
        sub = feat_df.loc[feat_df["machine_system"] == machine]
        if sub.empty:
            continue
        ood_cnt = int(sub["is_ood"].sum())
        rob_cnt = int(sub["is_robust_outlier"].sum())
        tail_cnt = int(sub["is_tail"].sum())
        max_z_idx = sub["robust_z_score"].idxmax()
        top_feat = str(sub.loc[max_z_idx, "feature"])
        max_z = float(sub.loc[max_z_idx, "robust_z_score"])

        if ood_cnt > 0 or rob_cnt > 0:
            m_status = "ANOMALY_FLAGGED (Inspect System)"
        elif tail_cnt > 0:
            m_status = "WATCH (Tail Deviation)"
        else:
            m_status = "NORMAL_OPERATING_ENVELOPE"

        machine_summaries.append(
            {
                "machine_system": machine,
                "monitored_tags": len(sub),
                "ood_tags": ood_cnt,
                "robust_outlier_tags_z_gt_4_5": rob_cnt,
                "tail_tags_outside_q01_q99": tail_cnt,
                "max_robust_z_score": round(max_z, 2),
                "most_deviated_tag": f"{top_feat} (Z={max_z:.2f})",
                "system_anomaly_status": m_status,
                "historical_downtime_log_mentions_may_jun_2020": historical_dt_events.get(machine, 0),
            }
        )

    feat_df = feat_df.sort_values(["is_ood", "is_robust_outlier", "robust_z_score"], ascending=[False, False, False])
    return {
        "machine_summaries": machine_summaries,
        "feature_diagnostics": feat_df.to_dict(orient="records"),
        "note": "Exploratory statistical deviation from training distribution by machine system; not a calibrated downtime probability.",
    }


def append_operator_audit_log(
    operator_name: str,
    decision: str,
    batch_id: str,
    part_name: str,
    set_time: str,
    predicted_class: str,
    prob_good: float,
    prob_low_bad: float,
    domain_status: str,
    sp_recommendation_summary: str,
    notes: str,
) -> Path:
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = AUDIT_LOG_PATH.is_file()
    fieldnames = [
        "timestamp",
        "operator_name",
        "decision",
        "VYP_batch",
        "Part",
        "Set_Time",
        "predicted_quality_class",
        "prob_good",
        "prob_low_bad",
        "domain_status",
        "sp_recommendation_summary",
        "control_action_taken",
        "operator_notes",
    ]
    with AUDIT_LOG_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "operator_name": operator_name.strip() or "Operator_On_Duty",
                "decision": decision,
                "VYP_batch": batch_id,
                "Part": part_name,
                "Set_Time": set_time,
                "predicted_quality_class": predicted_class,
                "prob_good": f"{prob_good:.4f}",
                "prob_low_bad": f"{prob_low_bad:.4f}",
                "domain_status": domain_status,
                "sp_recommendation_summary": sp_recommendation_summary,
                "control_action_taken": "NONE_ADVISORY_ONLY_NO_PLC_DCS_WRITE",
                "operator_notes": notes.strip(),
            }
        )
    return AUDIT_LOG_PATH
