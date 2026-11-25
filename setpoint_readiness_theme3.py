"""Assess readiness for SP recommendation without inferring safe limits."""

import json
from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
THEME_DIR = PROJECT_DIR / "Theme3" if (PROJECT_DIR / "Theme3" / "Processed_Data").exists() else PROJECT_DIR.parent / "Theme3"
SPLIT_DIR = THEME_DIR / "Processed_Data"
OUTPUT_DIR = SPLIT_DIR / "setpoint_readiness"
SP_COLUMNS = [
    "FFTE Feed solids SP",
    "FFTE Production solids SP",
    "FFTE Steam pressure SP",
    "TFE Out flow SP",
    "TFE Production solids SP",
    "TFE Vacuum pressure SP",
    "TFE Steam pressure SP",
]
AUTHORIZED_BOUNDS_FILE = PROJECT_DIR / "approved_operating_bounds.json"


def load_split(name: str) -> pd.DataFrame:
    frame = pd.read_csv(SPLIT_DIR / f"{name}.csv")
    if set(frame["split"].unique()) != {name}:
        raise ValueError(f"Unexpected split label in {name}.csv")
    return frame


def main() -> None:
    train = load_split("train")
    validation = load_split("validation")
    rows = []
    for column in SP_COLUMNS:
        train_values = pd.to_numeric(train[column], errors="raise")
        validation_values = pd.to_numeric(validation[column], errors="raise")
        combined = pd.concat([train_values, validation_values], ignore_index=True)
        rows.append(
            {
                "setpoint": column,
                "train_rows": int(train_values.notna().sum()),
                "train_unique_values": int(train_values.nunique()),
                "train_observed_min": float(train_values.min()),
                "train_observed_max": float(train_values.max()),
                "train_q01": float(train_values.quantile(0.01)),
                "train_q99": float(train_values.quantile(0.99)),
                "validation_observed_min": float(validation_values.min()),
                "validation_observed_max": float(validation_values.max()),
                "validation_outside_train_observed_range": int(
                    ((validation_values < train_values.min()) | (validation_values > train_values.max())).sum()
                ),
                "train_validation_observed_min": float(combined.min()),
                "train_validation_observed_max": float(combined.max()),
            }
        )

    summary = pd.DataFrame(rows)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(OUTPUT_DIR / "observed_sp_ranges.csv", index=False)

    bounds_present = AUTHORIZED_BOUNDS_FILE.is_file()
    approved_bounds = None
    bounds_error = None
    if bounds_present:
        try:
            approved_bounds = json.loads(AUTHORIZED_BOUNDS_FILE.read_text(encoding="utf-8"))
            expected = set(SP_COLUMNS)
            if set(approved_bounds) != expected or any(
                not isinstance(item, dict)
                or not item.get("source")
                or item.get("authorized") is not True
                or not isinstance(item.get("min"), (int, float))
                or not isinstance(item.get("max"), (int, float))
                or item["min"] >= item["max"]
                for item in approved_bounds.values()
            ):
                bounds_error = "Bounds file exists but lacks a complete, explicitly authorized range for every SP."
        except (json.JSONDecodeError, OSError) as error:
            bounds_error = f"Bounds file could not be read as valid JSON: {error}"

    can_rank_operationally = bounds_present and not bounds_error
    report = {
        "decision": "operational ranking blocked" if not can_rank_operationally else "bounds gate passed; model gate still required",
        "operational_ranking_generated": False,
        "approved_bounds_file": AUTHORIZED_BOUNDS_FILE.name,
        "approved_bounds_file_present": bounds_present,
        "bounds_validation_error": bounds_error,
        "sp_columns": SP_COLUMNS,
        "evaluation_data_used": ["train.csv", "validation.csv"],
        "test_opened": False,
        "reason": (
            "No authorized bounds are available in the supplied project files. Empirical extrema and quantiles are descriptive only, not safe operating limits."
            if not bounds_present
            else "Only verified expert-approved bounds can open candidate generation; the quality-model/probability gate must also pass before ranking."
        ),
        "model_gate": {
            "current_candidate": "Random Forest",
            "validation_macro_f1": 0.4793,
            "low_bad_recall": 0.0495,
            "probability_calibration_approved_for_ranking": False,
            "note": "Current quality-model results do not support operational recommendations; candidate ranking is not produced even if bounds are later supplied until model validity is reviewed.",
        },
        "observed_sp_summary_file": "observed_sp_ranges.csv",
    }
    (OUTPUT_DIR / "setpoint_readiness.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report_lines = [
        "# Setpoint recommendation readiness",
        "",
        "## Decision",
        "",
        "**Chưa đủ căn cứ đưa ra khuyến nghị vận hành hoặc xếp hạng SP ứng viên.** Không tìm thấy operating bounds được chuyên gia/tài liệu có thẩm quyền phê duyệt trong tài liệu project. Script không tạo candidate ranking.",
        "",
        "Các min/max và quantile trong `observed_sp_ranges.csv` chỉ mô tả giá trị đã quan sát ở train/validation. Chúng không phải giới hạn an toàn/được phê duyệt và không được dùng để tạo candidate bounds.",
        "",
        "## SP fields inspected",
        "",
        "| SP field | Train min-max | Train q01-q99 | Validation min-max | Validation outside train range |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        report_lines.append(
            f"| `{row['setpoint']}` | {row['train_observed_min']:g} to {row['train_observed_max']:g} | {row['train_q01']:g} to {row['train_q99']:g} | {row['validation_observed_min']:g} to {row['validation_observed_max']:g} | {row['validation_outside_train_observed_range']} |"
        )
    report_lines.extend(
        [
            "",
            "## Additional blocking conditions",
            "",
            "- Don vi, y nghia chi tiet cua tag, co the dieu khien, va thoi diem SP/PV co san chua duoc xac nhan trong data dictionary.",
            "- Mo hinh chat luong hien tai chi dat validation macro-F1 0,4793; recall `low_bad` 0,0495. Xac suat chua duoc phe duyet de dung xep hang SP.",
            "- Khuyen nghi tu du lieu quan sat khong chung minh tinh nhan qua. Can co process state hien tai hop le, muc tieu duoc chot, va review/validation boi chuyen gia.",
            "",
            "## Conditions to reopen ranking",
            "",
            "1. Them bounds duoc phe duyet cho ca 7 SP vao `approved_operating_bounds.json`, moi muc co min, max va citation/source; khong dien bang train min/max.",
            "2. Xac nhan don vi, tag semantics, control authority, snapshot timing va input operating domain.",
            "3. Duyet lai quality model tren batch/time holdout; neu dung probability score thi hoan tat calibration/uncertainty review.",
            "4. Chi khi cac gate nay qua moi sinh candidate, giu nguyen `Part` va process state, ghi muc thay doi va trinh nguoi van hanh review. Khong tu dong dieu khien may.",
            "",
            "This run used only train/validation summaries; the final test split was not opened.",
            "",
        ]
    )
    (OUTPUT_DIR / "setpoint_readiness_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    print("\n".join(report_lines))


if __name__ == "__main__":
    main()