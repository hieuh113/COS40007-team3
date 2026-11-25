"""Audit downtime-event readiness and screen supplied trends for unusual values."""

import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
THEME_DIR = PROJECT_DIR / "Theme3" if (PROJECT_DIR / "Theme3" / "Downtime").exists() else PROJECT_DIR.parent / "Theme3"
OUTPUT_DIR = THEME_DIR / "Processed_Data" / "downtime_readiness"
EVENT_FILE = THEME_DIR / "Downtime" / "Yeast Prep DT 04_05_20 - 01_07_20.csv"
TREND_FILES = {
    "evaporator": THEME_DIR / "Weekly Data 18_05_20 - 22_05_20" / "Evaporator Trends 18_05 - 22_05.csv",
    "ffte": THEME_DIR / "Weekly Data 18_05_20 - 22_05_20" / "FFTE Trend 22_06 - 26_06.csv",
}
ROBUST_Z_THRESHOLD = 4.5


def load_trend(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, encoding="utf-16", low_memory=False)
    frame["parsed_time"] = pd.to_datetime(
        frame["Time"],
        format="%d/%m/%Y %I:%M:%S.%f %p",
        errors="coerce",
    )
    if frame["parsed_time"].isna().any():
        raise ValueError(f"Could not parse all trend timestamps in {path}")
    return frame


def numeric_measurements(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    candidates = [
        column
        for column in frame.columns
        if column not in {"Time", "parsed_time"}
        and not any(token in column.lower() for token in (".sp", "setpoint"))
    ]
    measurements = pd.DataFrame(index=frame.index)
    for column in candidates:
        values = frame[column]
        if values.dtype == object:
            values = values.astype(str).str.replace(",", "", regex=False).str.strip()
        numeric = pd.to_numeric(values, errors="coerce")
        if numeric.notna().any():
            measurements[column] = numeric
    return measurements, list(measurements.columns)


def screen_trend(name: str, path: Path, event_times: pd.Series) -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    frame = load_trend(path)
    measurements, columns = numeric_measurements(frame)
    if not columns:
        raise ValueError(f"No numeric measurements found in {path}")

    measurement_rows = []
    row_outlier_counts = pd.Series(0, index=frame.index, dtype="int64")
    for column in columns:
        values = measurements[column]
        median = float(values.median())
        mad = float((values - median).abs().median())
        if mad > 0:
            robust_z = (values - median).abs() / (1.4826 * mad)
            is_outlier = robust_z > ROBUST_Z_THRESHOLD
            row_outlier_counts += is_outlier.fillna(False).astype("int64")
            outlier_count = int(is_outlier.sum())
        else:
            outlier_count = 0
        measurement_rows.append(
            {
                "trend": name,
                "measurement": column,
                "rows": len(frame),
                "missing": int(values.isna().sum()),
                "missing_rate": float(values.isna().mean()),
                "median": median,
                "mad": mad,
                "exploratory_outlier_count": outlier_count,
                "exploratory_outlier_rate": outlier_count / len(frame),
            }
        )

    flagged = row_outlier_counts > 0
    day_counts = pd.DataFrame(
        {
            "date": frame["parsed_time"].dt.date.astype(str),
            "flagged": flagged.astype(int),
        }
    ).groupby("date").agg(rows=("flagged", "size"), exploratory_outlier_rows=("flagged", "sum"))
    daily_rows = [
        {
            "trend": name,
            "date": date,
            "rows": int(row["rows"]),
            "exploratory_outlier_rows": int(row["exploratory_outlier_rows"]),
            "exploratory_outlier_rate": float(row["exploratory_outlier_rows"] / row["rows"]),
        }
        for date, row in day_counts.iterrows()
    ]

    trend_start = frame["parsed_time"].min()
    trend_end = frame["parsed_time"].max()
    overlap_events = int(event_times.between(trend_start, trend_end, inclusive="both").sum())
    ordered_times = frame["parsed_time"].sort_values()
    median_interval = ordered_times.diff().dt.total_seconds().median()
    trend_summary = {
        "trend": name,
        "file": path.relative_to(PROJECT_DIR).as_posix(),
        "rows": len(frame),
        "measurement_columns": columns,
        "start": trend_start.isoformat(sep=" "),
        "end": trend_end.isoformat(sep=" "),
        "median_sample_interval_seconds": float(median_interval),
        "rows_with_any_exploratory_outlier": int(flagged.sum()),
        "rows_with_any_exploratory_outlier_rate": float(flagged.mean()),
        "event_timestamps_inside_time_window": overlap_events,
        "event_time_overlap_is_not_device_matching": True,
    }
    return trend_summary, measurement_rows, daily_rows


def main() -> None:
    events = pd.read_csv(EVENT_FILE)
    events["event_time"] = pd.to_datetime(
        events["Production Date"].astype(str) + " " + events["Time"].astype(str),
        format="%d/%m/%Y %H:%M",
        errors="coerce",
    )
    if events["event_time"].isna().any():
        raise ValueError("Invalid event timestamps found")

    trend_summaries = []
    measurement_rows = []
    daily_rows = []
    for name, path in TREND_FILES.items():
        summary, measurements, days = screen_trend(name, path, events["event_time"])
        trend_summaries.append(summary)
        measurement_rows.extend(measurements)
        daily_rows.extend(days)

    cause_category_counts = events["Cause Category"].value_counts(dropna=False).to_dict()
    cause_counts = events["Cause"].value_counts(dropna=False).to_dict()
    lines = {
        "Dept": sorted(events["Dept"].dropna().astype(str).unique()),
        "Line": sorted(events["Line"].dropna().astype(str).unique()),
        "Sub Line": sorted(events["Sub Line"].dropna().astype(str).unique()),
    }
    event_summary = {
        "file": EVENT_FILE.relative_to(PROJECT_DIR).as_posix(),
        "rows": len(events),
        "timestamp_start": events["event_time"].min().isoformat(sep=" "),
        "timestamp_end": events["event_time"].max().isoformat(sep=" "),
        "invalid_timestamps": int(events["event_time"].isna().sum()),
        "duplicate_rows": int(events.duplicated().sum()),
        "equipment_fields_observed": lines,
        "cause_category_counts": cause_category_counts,
        "cause_counts": cause_counts,
        "frequency_counts": {str(key): int(value) for key, value in events["Freq"].value_counts(dropna=False).items()},
        "duration_minutes": {
            "min": float(events["Total Time Mins"].min()),
            "median": float(events["Total Time Mins"].median()),
            "max": float(events["Total Time Mins"].max()),
        },
        "missing_counts": {key: int(value) for key, value in events.isna().sum().items() if value},
        "time_column_semantics_verified_as_event_start": False,
        "event_end_timestamps_present": False,
        "complete_non_event_coverage_verified": False,
    }
    readiness = {
        "supervised_downtime_prediction_ready": False,
        "prediction_horizon_defined": False,
        "event_label_rule_defined": False,
        "equipment_mapping_verified": False,
        "complete_non_event_periods_verified": False,
        "event_start_semantics_verified": False,
        "supervised_model_trained": False,
        "anomaly_output_is_downtime_probability": False,
        "event_log": event_summary,
        "trend_sources": trend_summaries,
        "limitations": [
            "The event log contains planned or routine categories such as Startup, Shutdown and Sanitation as well as process causes; not all rows are confirmed unplanned failures.",
            "The log has event date/time and duration but no explicit event end timestamp; the meaning of Time as event start has not been independently confirmed.",
            "Dept, Line and Sub Line are constant in this log. A validated mapping from these fields and trend tags to the relevant equipment is not supplied.",
            "The log does not establish intervals with no events, so unlogged times cannot safely be labeled normal.",
            "Trend files cover only short windows and timestamp overlap does not establish equipment/tag alignment.",
            "The exploratory robust-MAD screen has no verified anomaly labels or operational threshold and must not be interpreted as downtime risk.",
        ],
        "exploratory_screen": {
            "method": "Per-measurement median/MAD robust-z screen; flag absolute robust-z > 4.5",
            "is_validated_anomaly_detector": False,
            "is_downtime_prediction": False,
            "note": "Statistical outliers are exploratory only; startup, shutdown, product changes and sensor/data-quality effects may be normal process modes.",
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(measurement_rows).to_csv(OUTPUT_DIR / "trend_outlier_screen.csv", index=False)
    pd.DataFrame(daily_rows).to_csv(OUTPUT_DIR / "trend_outlier_screen_by_day.csv", index=False)
    (OUTPUT_DIR / "downtime_readiness.json").write_text(
        json.dumps(readiness, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report_lines = [
        "# Downtime data readiness and exploratory trend screen",
        "",
        "## Decision",
        "",
        "**Không đủ căn cứ cho supervised downtime prediction.** Không huấn luyện classifier, không đặt prediction horizon/nhãn giả định, và không xuất downtime probability.",
        "",
        f"Event log có {len(events)} dòng, từ {event_summary['timestamp_start']} đến {event_summary['timestamp_end']}; không có timestamp lỗi hoặc dòng lặp chính xác. `Time` và `Total Time Mins` có thể gợi ý thời điểm/thời lượng, nhưng chưa xác nhận `Time` chính là thời điểm bắt đầu và không có event end timestamp riêng.",
        f"Các category thường gặp: {', '.join(f'{key}={value}' for key, value in list(cause_category_counts.items())[:8])}. Vì log gồm cả startup/shutdown/sanitation và process causes, không thể gán tất cả dòng thành cùng một loại hỏng hóc ngoài kế hoạch.",
        f"Equipment fields trong log chỉ có Dept={', '.join(lines['Dept'])}, Line={', '.join(lines['Line'])}, Sub Line={', '.join(lines['Sub Line'])}; mapping tag/thiết bị chưa được xác minh. Thiếu `Comments` ở {int(events['Comments'].isna().sum())}/218 dòng và `To Product` ở {int(events['To Product'].isna().sum())}/218 dòng.",
        "Không có lịch vận hành hoặc khoảng non-event đã xác nhận; vì vậy không thể coi thời điểm không xuất hiện trong log là normal.",
        "",
        "## Trend coverage and exploratory outlier screen",
        "",
        "| Trend source | Rows | Coverage | Median interval (s) | Events in time window* | Rows with >=1 robust outlier |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for summary in trend_summaries:
        report_lines.append(
            f"| `{summary['trend']}` | {summary['rows']:,} | {summary['start']} to {summary['end']} | {summary['median_sample_interval_seconds']:.2f} | {summary['event_timestamps_inside_time_window']} | {summary['rows_with_any_exploratory_outlier']:,} ({summary['rows_with_any_exploratory_outlier_rate']:.2%}) |"
        )
    for trend_name in sorted({row["trend"] for row in measurement_rows}):
        trend_measurements = [row for row in measurement_rows if row["trend"] == trend_name]
        missing_rates = [row["missing_rate"] for row in trend_measurements]
        report_lines.append(
            f"{trend_name}: {len(trend_measurements)} measurement tags; missing-value rate ranges from {min(missing_rates):.1%} to {max(missing_rates):.1%}."
        )
    report_lines.extend(
        [
            "",
            "*Thời điểm event nằm trong dải ngày/giờ của file trend chỉ là overlap theo đồng hồ; không chứng minh event cùng equipment/tag với trend.",
            "",
            "Sàng lọc dùng robust z-score theo từng measurement (median/MAD, ngưỡng 4,5), không có nhãn để xác thực và không phải detector đã kiểm định. Các điểm khác thường có thể là startup/shutdown, product/operating mode change, hoặc lỗi chất lượng sensor. Không diễn giải chúng thành downtime risk.",
            "",
            "## Next evidence required",
            "",
            "1. Người phụ trách quy trình xác nhận event taxonomy: planned stop, startup/shutdown, sanitation, unplanned fault; xác nhận `Time` là start time và duration/end semantics.",
            "2. Cung cấp lịch sản xuất/uptime để xây dựng các khoảng non-event đã xác nhận, không mặc định log absence là normal.",
            "3. Xác nhận Dept/Line/Sub Line tới FFTE/TFE/Extract Tank và trend tags; thống nhất timezone, clock offset và cách ghép thời gian.",
            "4. Chỉ khi đủ coverage mới chốt horizon/label rule, chia theo thời gian/batch và đánh giá event recall, false alarms, missed events, lead time.",
            "5. Nếu chỉ dùng anomaly screening, giữ riêng nhãn exploratory và không gọi là downtime prediction/probability.",
            "",
            "Inputs used: downtime log, two supplied weekly trend CSVs. No quality-model test split was opened; no supervised downtime model was trained.",
            "",
        ]
    )
    (OUTPUT_DIR / "downtime_readiness_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    print("\n".join(report_lines))


if __name__ == "__main__":
    main()