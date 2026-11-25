# COS40007 — Theme 3: AI-Assisted Quality Monitoring & Setpoint Advisory System for Vegemite Production

**Unit:** COS40007 Artificial Intelligence Engineering  
**Theme:** Theme 3 — Product Manufacturing / Mechanical Engineering  
**Repository:** https://github.com/hieuh113/COS40007-team3

## Team Members

| Member Name | Student ID | Role |
|---|---|---|
| Nguyễn Huy Hoàng Việt | 10499509 | Data / ML Engineer |
| Huỳnh Quốc Hiếu | 104848408 | ML / Evaluation & Project Coordinator |
| Vũ Bá Hiển | 104995634 | Technical Lead / Software & Deployment Design |

---

## 1. Project Overview

This repository contains the complete data audit, batch-disjoint chronological preprocessing pipeline, model benchmarking, out-of-fold (OOF) probability calibration, final holdout test evaluation, and interactive Streamlit Demonstrator for **COS40007 Theme 3** (Vegemite manufacturing process across `FFTE`, `TFE`, and `Extract Tank` systems).

The system addresses two core operational questions:
1. **Quality Prediction & Setpoint Advisory:** Predict product solid consistency (`good`, `low_bad`, `high_bad`) from 30 machine parameters (7 controllable Setpoints `SP` + 23 sensor/process variables `PV`) and rank candidate SP adjustments within supported envelopes while enforcing strict human-in-the-loop safety gates.
2. **Process Anomaly & Downtime Screening:** Diagnose current sensor deviations per machine system (`FFTE`, `TFE`, `Extract Tank`) via Robust Z-Score (Median/MAD) and domain boundaries, alongside data-readiness auditing of historical downtime logs and high-frequency trend streams.

> **Safety & Governance Design:** All outputs are strictly **advisory-only** (`NO AUTONOMOUS PLC/DCS WRITE`). Empirical min/max values in historical CSVs are never treated as plant-approved hardware limits, and statistical outlier flags are explicitly separated from supervised downtime probabilities.

---

## 2. Repository Structure

```text
.
├── .github/workflows/
│   └── train.yml                         # GitHub Actions CI workflow (Group Task 2 infrastructure)
├── audit_theme3_data.py                  # Read-only schema, duplicate, and label-conflict audit
├── preprocess_theme3_data.py             # Exact deduplication, conflict quarantine, batch/time split
├── eda_baseline_theme3.py                # Exploratory data analysis & 4-model validation baseline
├── tune_low_bad_theme3.py                # Class-weight & decision-threshold trade-off analysis for low_bad
├── robust_low_bad_theme3.py              # 3-fold walk-forward OOF & batch-equal weighting experiments
├── calibrate_and_freeze_theme3.py        # 5-model extended benchmark, OOF calibration, PR-AUC & model freeze
├── evaluate_test_theme3.py               # Single-run final evaluation on locked holdout test.csv
├── setpoint_readiness_theme3.py          # Setpoint recommendation safety gate & observed SP range audit
├── downtime_readiness_theme3.py          # Downtime log readiness & high-frequency trend Robust-Z screen
├── demonstrator_engine_theme3.py         # Core inference, OOD guardrails, SP ranking & audit logging engine
├── app_demonstrator_theme3.py            # Interactive 4-tab Streamlit Demonstrator Web Application
├── verify_demonstrator_theme3.py         # Automated 6-scenario regression check for the Demonstrator
├── approved_operating_bounds.template.json # Template for plant-authorized SP bounds sign-off
├── requirements-theme3.txt               # Python dependencies for the Theme 3 pipeline & Streamlit UI
├── docs/                                 # Project specification, data dictionary, audit & governance records
│   ├── PROJECT_SPECIFICATION_DEFINITION_THEME3_VI.md
│   ├── RESEARCH_BACKGROUND_THEME3_UAV_VI.md
│   ├── ACADEMIC_EVIDENCE_FOR_SP_APPROVAL.md
│   ├── data_dictionary_theme3.md
│   ├── data_audit_theme3.md
│   ├── field_confirmation_register.csv
│   ├── QUALITY_LABEL_CONFIRMATION_REQUEST.md
│   ├── QUALITY_LABEL_WORK_COMPLETION_STATUS.md
│   └── SP_BOUNDS_CONFIRMATION_REQUEST.md
├── reports/                              # Reproducible evaluation tables, JSON manifests, and PNG figures
│   ├── preprocessing_manifest.json
│   ├── eda_baseline/
│   ├── low_bad_tuning/
│   ├── robust_low_bad/
│   ├── model_calibration_freeze/
│   ├── final_test_evaluation/
│   ├── setpoint_readiness/
│   ├── downtime_readiness/
│   ├── demonstrator_verification/
│   └── operator_audit_log.csv
└── course_submissions/                   # Archived Week 6 (Blueprint) & Week 8 (CI Pipeline) deliverables
    ├── Week6/
    └── Week8/
```

---

## 3. Data Governance & Directory Placement

Raw manufacturing CSVs and row-level derived splits are excluded from version control via `.gitignore` in compliance with project data-handling rules.

To reproduce the full pipeline locally from scratch, place the supplied **Theme 3** dataset folder at `./Theme3/` (or `../Theme3/` relative to the scripts) with the following structure:

```text
Theme3/
├── data_02_07_2019-26-06-2020/
│   ├── good.csv
│   ├── low bad.csv
│   ├── high bad.csv
│   └── output_log.csv
├── Downtime/
│   └── Yeast Prep DT 04_05_20 - 01_07_20.csv
├── Weekly Data 18_05_20 - 22_05_20/
│   ├── Evaporator Trends 18_05 - 22_05.csv
│   └── FFTE Trend 22_06 - 26_06.csv
└── Processed_Data/                       # Automatically populated by preprocess_theme3_data.py
```

---

## 4. Environment Setup & Installation

**Prerequisites:** Python `3.11+` (tested on Python `3.11` and `3.13`).

1. Clone the repository:
   ```bash
   git clone https://github.com/hieuh113/COS40007-team3.git
   cd COS40007-team3
   ```

2. (Recommended) Create and activate a virtual environment:
   ```powershell
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   ```bash
   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the Theme 3 dependencies:
   ```bash
   python -m pip install -r requirements-theme3.txt
   ```

---

## 5. Step-by-Step Pipeline Execution Guide

Run the scripts in the exact sequence below from the repository root:

### Step 1 — Data Audit & Chronological Batch-Disjoint Preprocessing
```bash
python audit_theme3_data.py
python preprocess_theme3_data.py
```
- Verifies 30,375 raw rows across 33 columns (0 missing cells), removes 4,230 exact intra-class duplicates, quarantines conflicting batch `97_2020_06_25` (72 deduplicated rows), and generates strictly non-overlapping chronological splits in `Theme3/Processed_Data/`:
  - **Train:** 490 batches / 19,809 rows (`01/07/2019` – `27/03/2020`)
  - **Validation:** 107 batches / 3,450 rows (`27/03/2020` – `04/05/2020`)
  - **Test:** 105 batches / 2,814 rows (`04/05/2020` – `26/06/2020`)

### Step 2 — EDA, Minority-Class (`low_bad`) Tuning & Walk-Forward Analysis
```bash
python eda_baseline_theme3.py
python tune_low_bad_theme3.py
python robust_low_bad_theme3.py
```
- Evaluates baseline models and minority-class cost/threshold trade-offs using `train.csv` and `validation.csv` only.

### Step 3 — Extended Benchmark, OOF Probability Calibration & Model Freeze
```bash
python calibrate_and_freeze_theme3.py
```
- Benchmarks 5 candidate models (`DummyClassifier`, `LogisticRegression`, `RandomForest`, `ExtraTrees`, `HistGradientBoosting`), evaluates OOF probability calibration (`uncalibrated`, `temperature`, `sigmoid`, `isotonic`), records One-vs-Rest PR-AUC, and exports the frozen model bundle to `Theme3/Processed_Data/frozen_model/quality_model_frozen.joblib` with SHA-256 verification in `reports/model_calibration_freeze/model_freeze_manifest.json`.

### Step 4 — Setpoint & Downtime Readiness Gates
```bash
python setpoint_readiness_theme3.py
python downtime_readiness_theme3.py
```
- Audits operational SP bounds gate (`approved_operating_bounds.json`) and executes Robust Z-Score (`Median/MAD > 4.5`) outlier screening across 491,547 high-frequency trend rows (`Evaporator` & `FFTE`).

### Step 5 — One-Time Final Holdout Test Evaluation
```bash
python evaluate_test_theme3.py
```
- Verifies the frozen model's SHA-256 checksum against `model_freeze_manifest.json` and runs a single evaluation on `test.csv`, outputting confusion matrices, reliability diagrams, batch-level accuracy, subgroup metrics by `Part`, and covariate domain-shift diagnostics to `reports/final_test_evaluation/`.

---

## 6. Running the Interactive Web Demonstrator (Streamlit UI)

Ensure `preprocess_theme3_data.py` and `calibrate_and_freeze_theme3.py` have been executed once locally so `Theme3/Processed_Data/` and `quality_model_frozen.joblib` exist, then launch the web application:

```bash
python -m streamlit run app_demonstrator_theme3.py
```

Open your browser at **http://localhost:8501**.

### Key Features of the Demonstrator:
- **Sidebar Scenario Selector & What-If Controls:** Includes 6 preset scenarios (in-domain `good`, minority `low_bad` alert batch `7_2020_04_08`, `high_bad` batch, out-of-domain SP=98.0 extrapolation warning, test-period `TFE` density sensor shift, and missing-sensor input rejection) plus interactive controls for all 7 Setpoints.
- **Tab 1 — Quality Prediction & Domain Guardrails:** Displays predicted class (`argmax`), 3-class probability bar chart, Normalized Shannon Entropy uncertainty warning, two-tier `low_bad` advisory risk flag (`>= 0.15` Watch, `>= 0.25` Elevated Alert), and 30-feature domain audit.
- **Tab 2 — Setpoint Readiness Gate & Advisory Candidate Ranking:** Enforces the operational safety gate (`NOT_APPROVED` without plant P&ID bounds) and provides an **Academic What-If Candidate SP Ranking** engine within historical support (`q01–q99` single-SP steps and verified `good` profiles for the active `Part`), complete with an **Operator Approve / Reject** form persisted to `reports/operator_audit_log.csv`.
- **Tab 3 — Machine-Level Anomaly Diagnosis (`FFTE` / `TFE` / `Extract Tank`) & Downtime Screen:** Diagnoses current sensor deviations grouped by running machine system alongside historical trend outlier screens.
- **Tab 4 — Validation/Test Evaluation Evidence & Operator Audit Log:** Renders benchmark tables, final test metrics, reliability/uncertainty plots, and live operator audit logs.

To run automated headless verification across all 6 demonstrator scenarios:
```bash
python verify_demonstrator_theme3.py
```

---

## 7. Summary of Key Experimental Findings

| Evaluation Split / Metric | Accuracy | Macro-F1 | Balanced Acc | Macro PR-AUC | Log Loss | Brier Score | Mean ECE |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Validation (`random_forest_balanced`)** | `0.6580` | `0.4793` | `0.4781` | `0.4907` | `0.8098` | `0.4865` | `0.0574` |
| Validation (`majority_baseline`) | `0.4264` | `0.1993` | `0.3333` | `0.3333` | `19.8122` | `1.1472` | `0.3824` |
| **Final Test — Row Level (`random_forest_balanced`)** | `0.3586` | `0.2684` | `0.3355` | `0.3717` | `1.2800` | `0.7528` | `0.1946` |
| **Final Test — Batch Majority Vote (105 batches)** | `0.4476` | `0.3285` | — | — | — | — | — |
| Final Test (`majority_baseline`) | `0.2456` | `0.1314` | `0.3333` | `0.3333` | — | — | — |

- **Minority-Class Two-Tier Alerting on Test:** Secondary advisory thresholds frozen from validation (`P(low_bad) >= 0.25` Elevated Alert and `>= 0.15` Watch) achieved `66.04%` precision on test alerts (`low_bad` One-vs-Rest PR-AUC = `0.3184`) without inflating false positives in primary 3-class predictions.
- **Covariate & Prior Shift in May–June 2020 Test Period:** Domain auditing revealed that `21.39%` (`602/2,814`) of test rows fall outside training `[min, max]` boundaries (predominantly `TFE Production solids density` with 599 out-of-domain rows), coinciding with the May–June 2020 downtime log period and substantial label prior shift (`low_bad` rising from `6.8%` in train to `22.3%` in test). This empirically validates the necessity of the Demonstrator's Out-of-Domain guardrails and human-in-the-loop governance.

---

## 8. Note on GitHub Actions CI (`model.py` & `.github/workflows/train.yml`)

The root files `.github/workflows/train.yml`, `model.py`, and `requirements.txt` are preserved for backward compatibility with **Applied Project Group Task 2 (Week 8 GitHub Actions Pipeline)**. All **Theme 3 Vegemite** source code, documentation, and evaluation artifacts are maintained in the `*_theme3*.py` scripts, `docs/`, and `reports/`.
