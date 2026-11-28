# Applied Project Task 3: Scaling & Monitoring AI Systems

---

## 1. Cover Page (0 Pts — Required)

- **Title:** Applied Project Task 3: Scaling & Monitoring AI Systems (Automated Retraining, Drift Detection & DVC Pipeline for Vegemite Quality Monitoring)
- **Task Number:** Applied Project Group Task 3 (Studio Activity 9)
- **Unit Code & Title:** COS40007 — Artificial Intelligence Engineering
- **Theme & Group:** Theme 3 — Product Manufacturing / Mechanical Engineering (`Team 3`)
- **Submission Date:** 28 November 2026
- **GitHub Repository Link:** https://github.com/hieuh113/COS40007-team3

**Team Members:**
1. **Nguyễn Huy Hoàng Việt** — Student ID: `10499509` (Data / ML & MLOps Pipeline Engineer)
2. **Huỳnh Quốc Hiếu** — Student ID: `104848408` (ML Evaluation, Drift Monitoring & Project Coordinator)
3. **Vũ Bá Hiển** — Student ID: `104995634` (Technical Lead, DVC & CI/CD Architecture)

---

## 2. Acknowledgement of Country (0 Pts — Required)

We respectfully acknowledge the Wurundjeri Woi Wurrung people of the Kulin Nation as the Traditional Owners of the land on which Swinburne University of Technology’s Australian campuses are located, and we pay our respects to their Elders past, present, and emerging. As students studying within the Swinburne Vietnam Alliance Program, we also recognize and honor the cultural heritage, traditions, and contributions of local communities where our academic collaboration takes place.

---

## 3. Automated Retraining Trigger (8 Pts)

### Rubric Requirement (Excellent — 8 Pts)
> *Fully automated on data push, scheduled, and manual.*

### Implementation Details
The automated retraining and drift-monitoring workflow is defined in `.github/workflows/retrain-on-push.yml` with all three required trigger modes configured under the `on:` block:

1. **Automated on Data Push (`push`):** Automatically triggers whenever new production batch observations (`data/new_data.csv`), pipeline scripts (`src/**`), or DVC pipeline definitions (`dvc.yaml`) are pushed to the `main` branch.
2. **Scheduled Trigger (`schedule`):** Automatically executes every Sunday at `00:00 UTC` via cron expression `0 0 * * 0` to perform periodic drift audits and scheduled retraining.
3. **Manual Trigger (`workflow_dispatch`):** Allows engineers to trigger the pipeline on-demand from the GitHub Actions UI with a configurable `force_retrain` parameter.

```yaml
name: Automated Retraining & Drift Monitoring Pipeline

on:
  push:
    branches: [main]
    paths:
      - "data/**"
      - "src/**"
      - "dvc.yaml"
      - ".github/workflows/retrain-on-push.yml"
  schedule:
    - cron: "0 0 * * 0"
  workflow_dispatch:
    inputs:
      force_retrain:
        description: "Force model retraining even if drift is below threshold"
        required: false
        default: "true"
```

> **[INSERT SCREENSHOT 1 HERE]:** *Screenshot of `.github/workflows/retrain-on-push.yml` on GitHub showing the browser address bar (`github.com/hieuh113/COS40007-team3/blob/main/.github/workflows/retrain-on-push.yml`) and the `on: push`, `schedule`, and `workflow_dispatch` triggers.*

---

## 4. Commit Structure (4 Pts)

### Rubric Requirement (Excellent — 4 Pts)
> *Semantic commits with detailed messages.*

### Implementation Details
All repository updates for Applied Project Task 3 follow the **Conventional / Semantic Commits** standard (`feat(mlops):`, `chore(dvc):`, `ci(workflow):`, `docs(task3):`) with structured multi-line commit descriptions detailing the technical scope and affected artifacts:

- `feat(mlops): add automated preprocessing, KS/PSI drift monitoring, and incremental RF retraining pipeline`
- `chore(dvc): configure 4-stage DVC pipeline (dvc.yaml, dvc.lock) and DagsHub remote storage`
- `ci(workflow): add retrain-on-push GitHub Actions workflow with push, cron schedule, and manual dispatch triggers`
- `docs(task3): add Studio 9 MLOps documentation, architecture guide, and Group Task 3 report`

> **[INSERT SCREENSHOT 2 HERE]:** *Screenshot of `https://github.com/hieuh113/COS40007-team3/commits/main` showing the browser address bar and the semantic commit history.*

---

## 5. DVC Usage (8 Pts)

### Rubric Requirement (Excellent — 8 Pts)
> *Full DVC pipeline with remote storage.*

### Implementation Details
We configured a 4-stage **Data Version Control (DVC)** DAG in `dvc.yaml` (locked via `dvc.lock`) coupled with remote storage configuration in `.dvc/config` (`https://dagshub.com/hieuh113/COS40007-team3.dvc`):

1. **Stage 1 — `preprocess` (`python src/preprocess_new_data.py`):** Validates schema of `data/new_data.csv`, deduplicates records, scales/encodes features against reference training data, updates `artifacts/metadata/data_version.txt`, and outputs numpy arrays (`X_train.npy`, `y_train.npy`, `X_test.npy`, `y_test.npy`, `X_new.npy`).
2. **Stage 2 — `monitor_drift` (`python src/monitor.py`):** Computes Kolmogorov-Smirnov (KS) statistics, Population Stability Index (PSI), and Out-of-Domain (OOD) boundary checks across all 30 Vegemite process parameters (7 Setpoints + 23 PVs), outputting `reports/drift_report.json`, `reports/monitoring_dashboard.html`, and `artifacts/metrics/monitoring_metrics.json`.
3. **Stage 3 — `retrain_model` (`python src/model.py`):** Merges validated incoming batch data (`X_new.npy`) with reference training data (`X_train.npy`), retrains the 300-tree balanced Random Forest classifier, logs `artifacts/metadata/model_version.txt` & `last_retrain.txt`, and saves `artifacts/models/model.joblib` (`model.keras`).
4. **Stage 4 — `evaluate_model` (`python src/evaluate.py`):** Compares baseline vs. retrained model performance on held-out evaluation batches (`X_test.npy`), outputting `artifacts/metrics/evaluation_metrics.json` and `reports/performance_report.html`.

> **[INSERT SCREENSHOT 3 HERE]:** *Screenshot of `dvc.yaml` and `.dvc/config` in the GitHub repository showing the browser address bar (`github.com/hieuh113/COS40007-team3/blob/main/dvc.yaml`).*

---

## 6. Final GitHub Actions Setup (12 Pts)

### Rubric Requirement (Excellent — 12 Pts)
> *Complete workflow with all triggers.*

### Implementation Details
The `retrain_and_monitor` job in `.github/workflows/retrain-on-push.yml` runs on `ubuntu-latest` with Python 3.11 and executes a 10-step end-to-end MLOps pipeline:
1. Checkout repository (`actions/checkout@v4`)
2. Set up Python 3.11 (`actions/setup-python@v5`)
3. Cache pip dependencies (`actions/cache@v4`)
4. Install MLOps & DVC packages (`pip install -r requirements-theme3.txt scipy dvc`)
5. Detect incoming data (`data/new_data.csv`) & check DVC pipeline status
6. Execute Stage 1 Preprocessing (`python src/preprocess_new_data.py`)
7. Execute Stage 2 Drift & Data Quality Monitoring (`python src/monitor.py`)
8. Execute Stage 3 Automated Model Retraining (`python src/model.py`)
9. Execute Stage 4 Post-Retraining Evaluation & HTML Dashboard Generation (`python src/evaluate.py`)
10. Upload centralized MLOps artifacts (`actions/upload-artifact@v4` -> `mlops-retraining-and-monitoring-artifacts`), including JSON metrics, metadata version files, execution logs (`training.log`, `monitoring.log`, `drift_detection.log`), and HTML dashboards (`monitoring_dashboard.html`, `performance_report.html`).

### Summary of Automated Retraining & Monitoring Results on Theme 3 Data
- **Drift Detection Result:** Across 30 Vegemite process parameters on incoming batch data (`387 rows / 12 batches`), `monitor.py` detected statistically significant distribution drift (`KS p < 0.01`, `PSI >= 0.25`) on **26/30 features (`86.7%`)**, automatically triggering incremental retraining (`retrain_triggered = True`).
- **Post-Retraining Holdout Performance (`3,450 validation rows`):**
  - **Holdout Accuracy:** Improved from `0.6580` (Baseline) to **`0.6617`** (`+0.0037`)
  - **Balanced Accuracy:** Improved from `0.4781` to **`0.4791`**
  - **Multiclass Brier Score:** Improved (decreased) from `0.4865` to **`0.4720`** (`-0.0145`)
  - **Log Loss:** Improved (decreased) from `0.8098` to **`0.7839`**
  - **Minority Class (`low_bad`) PR-AUC:** Improved from `0.1248` to **`0.1863`** (`+49.3%` relative gain)

> **[INSERT SCREENSHOT 4 HERE]:** *Screenshot of the GitHub Actions run (`https://github.com/hieuh113/COS40007-team3/actions`) showing all 10 steps with green checkmarks and the uploaded `mlops-retraining-and-monitoring-artifacts` bundle.*

> **[INSERT SCREENSHOT 5 HERE]:** *Screenshot of the generated HTML dashboards (`reports/monitoring_dashboard.html` and `reports/performance_report.html`).*

---

## 7. Use of Project Management Tool (8 Pts)

### Rubric Requirement (Excellent — 8 Pts)
> *Backlogs are being cleared, tasks are being broken down and completed by team members, and the tool (Jira/Trello) is being used effectively.*

### Implementation Details
Our team manages sprints, user stories, and MLOps tasks on **Jira** (`https://cos4007.atlassian.net/jira/software/projects/SCRUM/boards/1`). For Applied Project Task 3 (Sprint 3–4), the MLOps epic was broken down into granular tasks assigned across all three members and tracked from *To Do* $\rightarrow$ *In Progress* $\rightarrow$ *Done*:
- **Task 3.1 (Nguyễn Huy Hoàng Việt):** Implement `src/preprocess_new_data.py` & `src/model.py` incremental Random Forest retraining with centralized `artifacts/` storage. (*Status: Done*)
- **Task 3.2 (Huỳnh Quốc Hiếu):** Implement `src/monitor.py` (30-feature KS/PSI drift detection & alert logging) and `src/evaluate.py` HTML dashboards (`monitoring_dashboard.html`, `performance_report.html`). (*Status: Done*)
- **Task 3.3 (Vũ Bá Hiển):** Configure 4-stage `dvc.yaml`, `.dvc/config` remote storage, and `.github/workflows/retrain-on-push.yml` with push, cron schedule, and manual triggers. (*Status: Done*)

> **[INSERT SCREENSHOT 6 HERE]:** *Screenshot of the group Jira board showing the browser address bar, completed Sprint backlog items, and task assignments across the three team members.*

---

## 8. Report Completeness & Professionalism (4 Pts)

All Studio Activity 9 requirements, directory structures (`src/`, `data/`, `artifacts/`, `monitoring/`, `logs/`, `reports/`, `dvc.yaml`, `.github/workflows/retrain-on-push.yml`), automated drift-triggered retraining evidence, and live demonstration instructions have been integrated into the group repository:
- **GitHub Repository URL:** https://github.com/hieuh113/COS40007-team3

---

## 9. Individual Contribution Statement (6 Pts)

### Rubric Requirement (Excellent — 6 Pts)
> *A contribution statement for an individual indicates sufficient contribution to the submission and indicates a balanced share of work.*

| Team Member | Student ID | Primary Responsibilities & Deliverables in Group Task 3 | Workload Share |
|---|---|---|---|
| **Nguyễn Huy Hoàng Việt** | `10499509` | Designed and implemented `src/preprocess_new_data.py` and `src/model.py` for incremental Vegemite quality model retraining; prepared stratified batch datasets in `data/`; executed semantic commits and verified GitHub Actions artifact generation. | **33.3%** |
| **Huỳnh Quốc Hiếu** | `104848408` | Designed and implemented `src/monitor.py` (KS-test, PSI, and Out-of-Domain drift detection across 30 SP/PV features) and `src/evaluate.py`; generated `monitoring_dashboard.html` and `performance_report.html`; updated Jira board and compiled submission report. | **33.3%** |
| **Vũ Bá Hiển** | `104995634` | Designed the 4-stage DVC pipeline (`dvc.yaml`, `dvc.lock`, `.dvc/config` remote storage) and `.github/workflows/retrain-on-push.yml` multi-trigger workflow (`push`, `schedule`, `workflow_dispatch`); conducted end-to-end integration review. | **33.4%** |

### Individual Statement (Nguyễn Huy Hoàng Việt — 10499509)
In Applied Project Task 3, I was responsible for building the automated data ingestion/preprocessing stage (`src/preprocess_new_data.py`) and the incremental Random Forest retraining engine (`src/model.py`), preparing the Theme 3 batch datasets (`data/new_data.csv`, `data/reference_train.csv`, `data/holdout_eval.csv`), and integrating the centralized `artifacts/` storage structure (`X_train.npy`, `X_new.npy`, `scaler.pkl`, `encoder.pkl`, `data_version.txt`, `model_version.txt`). I also co-verified the multi-trigger GitHub Actions pipeline (`.github/workflows/retrain-on-push.yml`) and DVC stage outputs with my teammates Huỳnh Quốc Hiếu and Vũ Bá Hiển, contributing an equal one-third (**33.3%**) share of the overall team effort.
