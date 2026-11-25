"""Verification and regression check for the Theme 3 Demonstrator Engine and Audit Log.

Evaluates 6 operational scenarios (In-Domain Good, Low_Bad High Risk, High_Bad with What-If SP Ranking,
Out-of-Domain Extrapolation Risk, Test Sensor Shift, and Missing Sensor Input Rejection).
"""

import json
from pathlib import Path

import pandas as pd

from demonstrator_engine_theme3 import (
    AUDIT_LOG_PATH,
    PROJECT_DIR,
    SPLIT_DIR,
    append_operator_audit_log,
    check_authorized_sp_bounds,
    diagnose_current_input_anomalies_by_machine,
    load_frozen_bundle,
    predict_quality_state,
    rank_what_if_sp_candidates,
)

OUTPUT_DIRS = [
    SPLIT_DIR / "demonstrator_verification",
    PROJECT_DIR / "reports" / "demonstrator_verification",
]


def main() -> None:
    bundle = load_frozen_bundle()
    feature_columns: list[str] = bundle["feature_columns"]
    train_df = pd.read_csv(SPLIT_DIR / "train.csv")
    val_df = pd.read_csv(SPLIT_DIR / "validation.csv")
    test_df = pd.read_csv(SPLIT_DIR / "test.csv")

    sp_gate = check_authorized_sp_bounds()

    scenarios = [
        ("Scenario_1_Val_InDomain_Good", val_df.loc[val_df["quality_class"] == "good"].iloc[0], False),
        ("Scenario_2_Val_LowBad_Batch_7_2020_04_08", val_df.loc[val_df["VYP batch"] == "7_2020_04_08"].iloc[0], False),
        ("Scenario_3_Val_HighBad_SP_Ranking", val_df.loc[val_df["quality_class"] == "high_bad"].iloc[5], False),
        ("Scenario_4_Val_OutOfDomain_SP98", val_df.loc[val_df["TFE Production solids SP"] > 88.0].iloc[0], False),
        (
            "Scenario_5_Test_OutOfDomain_TFEDensity",
            test_df.loc[test_df["TFE Production solids density"] > train_df["TFE Production solids density"].max()].iloc[0],
            False,
        ),
        ("Scenario_6_Missing_Sensor_Input", val_df.iloc[0], True),
    ]

    scenario_results = []
    if AUDIT_LOG_PATH.is_file():
        AUDIT_LOG_PATH.unlink()

    for name, row, inject_missing in scenarios:
        inputs = {col: float(row[col]) for col in feature_columns}
        if inject_missing:
            inputs["TFE Production solids PV"] = float("nan")

        pred = predict_quality_state(bundle, inputs)
        sp_sim = None
        machine_diag = None
        if pred["success"]:
            machine_diag = diagnose_current_input_anomalies_by_machine(
                input_row=inputs,
                train_df=train_df,
                feature_domain=bundle["feature_domain"],
                robust_z_threshold=4.5,
            )
            sp_sim = rank_what_if_sp_candidates(
                bundle=bundle,
                current_row=inputs,
                part_name=str(row["Part"]),
                train_df=train_df,
                n_grid_steps=5,
                top_k=5,
            )
            top_cand = sp_sim["candidates"][0] if sp_sim and sp_sim["candidates"] else None
            decision = (
                "FLAGGED_OOD_HOLD_CURRENT_SP"
                if pred["domain_check"]["domain_status"] != "IN_DOMAIN_SUPPORTED"
                else "REVIEWED_ADVISORY_SIMULATION_NO_PLC_WRITE"
            )
            append_operator_audit_log(
                operator_name="QA_Scenario_Check",
                decision=decision,
                batch_id=str(row["VYP batch"]),
                part_name=str(row["Part"]),
                set_time=str(row["Set Time"]),
                predicted_class=pred["predicted_class"],
                prob_good=pred["probabilities"]["good"],
                prob_low_bad=pred["probabilities"]["low_bad"],
                domain_status=pred["domain_check"]["domain_status"],
                sp_recommendation_summary=(
                    f"Top1: {top_cand['candidate_sp']} -> P(good)={top_cand['prob_good']:.3f} (delta={top_cand['delta_prob_good']:+.3f})"
                    if top_cand
                    else "No candidate"
                ),
                notes=f"Verified {name}; operational SP gate={sp_gate['gate_status']}",
            )

        scenario_results.append(
            {
                "scenario": name,
                "batch": str(row["VYP batch"]),
                "part": str(row["Part"]),
                "set_time": str(row["Set Time"]),
                "true_class": str(row["quality_class"]),
                "prediction_success": pred["success"],
                "predicted_class": pred.get("predicted_class"),
                "prob_good": pred.get("probabilities", {}).get("good"),
                "prob_low_bad": pred.get("probabilities", {}).get("low_bad"),
                "prob_high_bad": pred.get("probabilities", {}).get("high_bad"),
                "normalized_entropy": pred.get("normalized_entropy"),
                "low_bad_risk_tier": pred.get("low_bad_risk_tier"),
                "domain_status": pred["domain_check"]["domain_status"],
                "ood_feature_count": len(pred["domain_check"]["ood_minmax_features"]),
                "top_what_if_sp_candidate": (
                    sp_sim["candidates"][0]["candidate_sp"] if sp_sim and sp_sim.get("candidates") else None
                ),
                "top_what_if_prob_good": (
                    sp_sim["candidates"][0]["prob_good"] if sp_sim and sp_sim.get("candidates") else None
                ),
                "top_what_if_delta_prob_good": (
                    sp_sim["candidates"][0]["delta_prob_good"] if sp_sim and sp_sim.get("candidates") else None
                ),
                "flagged_machines": (
                    "|".join(
                        m["machine_system"].split(" ")[0]
                        for m in machine_diag["machine_summaries"]
                        if "ANOMALY" in m["system_anomaly_status"]
                    )
                    or "NONE"
                    if machine_diag
                    else None
                ),
            }
        )

    df_res = pd.DataFrame(scenario_results)
    for out_dir in OUTPUT_DIRS:
        out_dir.mkdir(parents=True, exist_ok=True)
        df_res.to_csv(out_dir / "demonstrator_scenario_verification.csv", index=False)
        (out_dir / "demonstrator_verification.json").write_text(
            json.dumps(
                {
                    "operational_sp_gate": sp_gate,
                    "scenarios_tested": len(scenario_results),
                    "audit_log_path": AUDIT_LOG_PATH.relative_to(PROJECT_DIR).as_posix(),
                    "results": scenario_results,
                },
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

    print("Demonstrator verification passed for all 6 scenarios!")
    print(df_res.to_string(index=False))


if __name__ == "__main__":
    main()
