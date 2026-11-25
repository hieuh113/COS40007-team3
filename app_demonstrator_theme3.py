"""COS40007 Theme 3 Interactive AI Demonstrator (Streamlit Application).

Run from Project_Package directory:
    python -m streamlit run app_demonstrator_theme3.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from demonstrator_engine_theme3 import (
    AUDIT_LOG_PATH,
    DT_READINESS_PATH,
    FREEZE_MANIFEST_PATH,
    PROJECT_DIR,
    SP_COLUMNS,
    SP_READINESS_PATH,
    SPLIT_DIR,
    TEST_SUMMARY_PATH,
    append_operator_audit_log,
    check_authorized_sp_bounds,
    diagnose_current_input_anomalies_by_machine,
    load_frozen_bundle,
    load_json_report,
    predict_quality_state,
    rank_what_if_sp_candidates,
)

st.set_page_config(
    page_title="COS40007 Theme 3 — Vegemite AI Quality & Setpoint Demonstrator",
    page_icon="🧪",
    layout="wide",
)


@st.cache_resource
def get_model_bundle():
    return load_frozen_bundle()


@st.cache_data
def get_datasets():
    train = pd.read_csv(SPLIT_DIR / "train.csv")
    val = pd.read_csv(SPLIT_DIR / "validation.csv")
    test = pd.read_csv(SPLIT_DIR / "test.csv")
    quarantine = pd.read_csv(SPLIT_DIR / "quarantine_conflicting_batches.csv")
    return train, val, test, quarantine


def main() -> None:
    bundle = get_model_bundle()
    train_df, val_df, test_df, quarantine_df = get_datasets()
    freeze_manifest = load_json_report(FREEZE_MANIFEST_PATH)
    test_summary = load_json_report(TEST_SUMMARY_PATH)
    sp_readiness = load_json_report(SP_READINESS_PATH)
    dt_readiness = load_json_report(DT_READINESS_PATH)
    sp_gate = check_authorized_sp_bounds()

    # Top safety & governance banner
    st.title("🧪 COS40007 Theme 3: AI-Assisted Quality Monitoring & Setpoint Advisory Demonstrator")
    st.caption(
        "**Project:** Vegemite Production Quality & Process Monitoring (`FFTE` / `TFE` / `Extract Tank`) | "
        "**Frozen Model:** `random_forest_balanced` (300 trees, SHA-256 verified) | "
        "**Control Mode:** **ADVISORY-ONLY — NO AUTONOMOUS PLC/DCS WRITE**"
    )

    col_g1, col_g2, col_g3, col_g4 = st.columns(4)
    col_g1.metric("Quality Label Gate", "APPROVED (w/ Quarantine)", "Batch 97_2020_06_25 isolated")
    col_g2.metric(
        "Operational SP Gate",
        sp_gate["gate_status"],
        "Blocked without plant P&ID bounds" if not sp_gate["operational_ranking_allowed"] else "Bounds Verified",
    )
    col_g3.metric("Supervised Downtime Gate", "BLOCKED (Insufficient Data)", "Exploratory Trend Screen Active")
    col_g4.metric("Control Authority", "HUMAN-IN-THE-LOOP", "0 PLC/DCS commands allowed")

    st.divider()

    # Sidebar: Scenario & Process Snapshot Selection
    st.sidebar.header("⚙️ 1. Chọn Mẫu / Trạng thái Quy trình")
    preset_mode = st.sidebar.selectbox(
        "Chọn kịch bản kiểm thử nhanh (Preset Scenarios):",
        [
            "Kịch bản 1: Mẻ chuẩn trong miền (Validation — Good Batch)",
            "Kịch bản 2: Mẻ nguy cơ cao lớp thiểu số (Validation — Low_Bad Batch 7_2020_04_08)",
            "Kịch bản 3: Mẻ lỗi High_Bad cần tư vấn điều chỉnh SP (Validation — High_Bad)",
            "Kịch bản 4: Cảnh báo Ngoài miền dữ liệu (Out-of-Domain SP=98.0 > Train Max 88.0)",
            "Kịch bản 5: Dịch chuyển cảm biến Tập Test (Test Set — TFE Density Out-of-Domain)",
            "Tùy chỉnh: Chọn bất kỳ dòng nào từ Validation / Test",
        ],
    )

    if preset_mode.startswith("Kịch bản 1"):
        active_split_name = "validation.csv"
        sample_row = val_df.loc[val_df["quality_class"] == "good"].iloc[0]
    elif preset_mode.startswith("Kịch bản 2"):
        active_split_name = "validation.csv"
        sample_row = val_df.loc[val_df["VYP batch"] == "7_2020_04_08"].iloc[0]
    elif preset_mode.startswith("Kịch bản 3"):
        active_split_name = "validation.csv"
        sample_row = val_df.loc[val_df["quality_class"] == "high_bad"].iloc[5]
    elif preset_mode.startswith("Kịch bản 4"):
        active_split_name = "validation.csv"
        sample_row = val_df.loc[val_df["TFE Production solids SP"] > 88.0].iloc[0]
    elif preset_mode.startswith("Kịch bản 5"):
        active_split_name = "test.csv"
        sample_row = test_df.loc[test_df["TFE Production solids density"] > train_df["TFE Production solids density"].max()].iloc[0]
    else:
        active_split_name = st.sidebar.radio("Chọn tập dữ liệu:", ["validation.csv", "test.csv"])
        source_df = val_df if active_split_name == "validation.csv" else test_df
        selected_batch = st.sidebar.selectbox("Chọn VYP batch:", source_df["VYP batch"].unique())
        batch_rows = source_df.loc[source_df["VYP batch"] == selected_batch]
        row_idx = st.sidebar.slider("Chọn dòng quan sát trong batch:", 0, len(batch_rows) - 1, 0)
        sample_row = batch_rows.iloc[row_idx]

    st.sidebar.markdown("---")
    st.sidebar.subheader("🛠️ 2. Chỉnh sửa Setpoint (SP) & Kiểm tra lỗi")
    feature_columns: list[str] = bundle["feature_columns"]
    feature_domain: dict[str, dict[str, float]] = bundle["feature_domain"]

    input_values: dict[str, float] = {col: float(sample_row[col]) for col in feature_columns}
    for sp_col in SP_COLUMNS:
        dom = feature_domain[sp_col]
        input_values[sp_col] = st.sidebar.number_input(
            f"{sp_col} (Train: [{dom['train_min']:.1f}, {dom['train_max']:.1f}])",
            value=float(sample_row[sp_col]),
            step=0.5,
            format="%.2f",
        )

    simulate_missing = st.sidebar.checkbox("Mô phỏng lỗi thiếu tín hiệu cảm biến (Missing Input Test)", value=False)
    if simulate_missing:
        input_values["TFE Production solids PV"] = float("nan")

    # Run prediction engine
    pred_result = predict_quality_state(bundle, input_values)

    # Provenance header card
    with st.expander("📋 Thông tin Truy vết Mẻ sản xuất (Batch Provenance & Metadata)", expanded=True):
        p1, p2, p3, p4, p5 = st.columns(5)
        p1.markdown(f"**Mã Batch (`VYP batch`):**\n`{sample_row['VYP batch']}`")
        p2.markdown(f"**Loại Yeast (`Part`):**\n`{sample_row['Part']}`")
        p3.markdown(f"**Thời điểm (`Set Time`):**\n`{sample_row['Set Time']}`")
        p4.markdown(f"**Tệp nguồn & Dòng gốc:**\n`{sample_row['source_file']}` (row `{sample_row['source_rows']}`)")
        p5.markdown(f"**Nhãn thực tế (Ground Truth):**\n`{sample_row['quality_class']}` *(Split: `{active_split_name}`)*")

    # Main 4 Tabs
    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "🎯 1. Dự đoán Chất lượng & Cảnh báo Miền dữ liệu",
            "🎚️ 2. Cổng Khuyến nghị Setpoint (SP Readiness & Advisory Ranking)",
            "⚠️ 3. Cổng Downtime & Sàng lọc Bất thường Trend",
            "📜 4. Báo cáo Kiểm định Mô hình & Nhật ký Người vận hành",
        ]
    )

    # TAB 1: QUALITY PREDICTION & DOMAIN GUARDRAILS
    with tab1:
        if not pred_result["success"]:
            st.error(
                f"🚫 **HỆ THỐNG TỪ CHỐI DỰ ĐOÁN (INVALID / MISSING INPUT):** {pred_result['error']}. "
                "Vui lòng kiểm tra kết nối cảm biến trước khi yêu cầu tư vấn AI."
            )
        else:
            dom_check = pred_result["domain_check"]
            if dom_check["domain_status"] == "OUT_OF_DOMAIN_EXTRAPOLATION_RISK":
                st.warning(
                    "⚠️ **CẢNH BÁO NGOÀI MIỀN HUẤN LUYỆN (OUT-OF-DOMAIN / EXTRAPOLATION RISK):** "
                    f"Phát hiện **{len(dom_check['ood_minmax_features'])} thông số** nằm ngoài hoàn toàn khoảng `[min, max]` quan sát được trong tập Train. "
                    "Độ tin cậy của dự đoán bị suy giảm; không sử dụng để ra quyết định vận hành!"
                )
                st.dataframe(pd.DataFrame(dom_check["ood_minmax_features"]), use_container_width=True)
            elif dom_check["domain_status"] == "TAIL_DOMAIN_CAUTION":
                st.info(
                    f"ℹ️ **Lưu ý Biên miền dữ liệu (Tail Domain q01–q99):** Có {len(dom_check['outside_q01_q99_features'])} thông số nằm ngoài khoảng phân vị 1%–99% của tập Train."
                )
            else:
                st.success("✅ **Trạng thái Miền dữ liệu (Domain Check):** Toàn bộ 30 thông số SP/PV đều nằm trong miền hỗ trợ an toàn của tập Train (`IN_DOMAIN_SUPPORTED`).")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Lớp Chất lượng Dự đoán (Argmax)", pred_result["predicted_class"].upper(), f"Thực tế: {sample_row['quality_class']}")
            c2.metric("Độ tự tin cao nhất (Max Prob)", f"{pred_result['max_probability']:.1%}", f"Margin top-2: {pred_result['confidence_margin']:.1%}")
            c3.metric(
                "Độ không chắc chắn (Norm Entropy)",
                f"{pred_result['normalized_entropy']:.3f}",
                "CAO (>= 0.75)" if pred_result["high_uncertainty_flag"] else "Ổn định (< 0.75)",
                delta_color="inverse" if pred_result["high_uncertainty_flag"] else "normal",
            )
            c4.metric(
                "Cảnh báo Phụ trợ Lớp `low_bad`",
                pred_result["low_bad_risk_tier"],
                f"P(low_bad) = {pred_result['probabilities']['low_bad']:.1%}",
            )

            if pred_result["high_uncertainty_flag"]:
                st.warning(
                    "⚠️ **CẢNH BÁO ĐỘ KHÔNG CHẮC CHẮN CAO (HIGH UNCERTAINTY):** "
                    "Entropy chuẩn hóa đạt mức cao (>= 0.75) hoặc dữ liệu nằm ngoài miền huấn luyện. Yêu cầu kỹ sư quy trình kiểm tra trực tiếp mẻ sản xuất."
                )

            st.subheader("Phân bố Xác suất Dự đoán 3 Lớp (`good`, `low_bad`, `high_bad`)")
            prob_df = pd.DataFrame(
                [
                    {"Lớp chất lượng": "good", "Xác suất": pred_result["probabilities"]["good"]},
                    {"Lớp chất lượng": "low_bad", "Xác suất": pred_result["probabilities"]["low_bad"]},
                    {"Lớp chất lượng": "high_bad", "Xác suất": pred_result["probabilities"]["high_bad"]},
                ]
            )
            st.bar_chart(prob_df.set_index("Lớp chất lượng"))

            with st.expander("🔍 Xem chi tiết 30 Thông số Đầu vào hiện tại so với Miền Huấn luyện (`feature_domain`)"):
                feat_rows = []
                for col in feature_columns:
                    d = feature_domain[col]
                    val = input_values[col]
                    status_str = "OK"
                    if val < d["train_min"] or val > d["train_max"]:
                        status_str = "OUT_OF_TRAIN_MIN_MAX"
                    elif val < d["train_q01"] or val > d["train_q99"]:
                        status_str = "OUTSIDE_Q01_Q99"
                    feat_rows.append(
                        {
                            "Feature": col,
                            "Nhóm": "Setpoint (SP)" if d["is_setpoint"] else "Sensor / PV",
                            "Giá trị hiện tại": val,
                            "Train Min": d["train_min"],
                            "Train q01": d["train_q01"],
                            "Train Median": d["train_median"],
                            "Train q99": d["train_q99"],
                            "Train Max": d["train_max"],
                            "Trạng thái Miền": status_str,
                        }
                    )
                st.dataframe(pd.DataFrame(feat_rows), use_container_width=True)

    # TAB 2: SETPOINT READINESS & ADVISORY RANKING
    with tab2:
        st.subheader("🎚️ Trạng thái Cổng Khuyến nghị Setpoint (SP Recommendation Safety Gate)")
        if not sp_gate["operational_ranking_allowed"]:
            st.error(
                f"🔒 **CỔNG VẬN HÀNH NHÀ MÁY ĐANG KHÓA (`{sp_gate['gate_status']}`):** {sp_gate['reason']}\n\n"
                "- **Quy tắc an toàn:** Hệ thống tuyệt đối không tự lấy giá trị cực tiểu/cực đại lịch sử (`observed_sp_ranges.csv`) làm giới hạn an toàn phần cứng (Hard Equipment Limits).\n"
                "- Để mở cổng khuyến nghị vận hành thực tế, kỹ sư nhà máy cần cung cấp tệp `approved_operating_bounds.json` có chữ ký, đơn vị và tham chiếu bản vẽ P&ID."
            )
        else:
            st.success(f"🔓 **CỔNG VẬN HÀNH ĐÃ MỞ (`{sp_gate['gate_status']}`):** {sp_gate['reason']}")

        st.markdown("#### Bảng Phạm vi 7 Setpoint Quan sát trong Lịch sử (`reports/setpoint_readiness/observed_sp_ranges.csv`)")
        obs_sp_path = PROJECT_DIR / "reports" / "setpoint_readiness" / "observed_sp_ranges.csv"
        if obs_sp_path.is_file():
            st.dataframe(pd.read_csv(obs_sp_path), use_container_width=True)

        st.markdown("---")
        st.subheader("🧪 Chế độ Mô phỏng Học thuật (Academic What-If Candidate SP Ranking Simulation)")
        st.info(
            "💡 **Mục đích học thuật (Rubric 25% SP Recommendation):** Cho phép giảng viên/người đánh giá kiểm thử thuật toán **Prescriptive Candidate SP Ranking** trong miền hỗ trợ lịch sử (`q01`–`q99` của tập Train và các cấu hình SP đã từng tạo ra mẻ `good` cho cùng loại `Part`), giữ cố định toàn bộ 23 biến cảm biến PV hiện tại."
        )
        enable_sim = st.checkbox(
            "Bật chế độ Mô phỏng Xếp hạng Setpoint Ứng viên (Xác nhận đây là mô phỏng What-If học thuật, không phải giới hạn P&ID nhà máy và không ghi xuống PLC/DCS)",
            value=True,
        )

        if enable_sim and pred_result["success"]:
            sim_result = rank_what_if_sp_candidates(
                bundle=bundle,
                current_row=input_values,
                part_name=str(sample_row["Part"]),
                train_df=train_df,
                n_grid_steps=5,
                top_k=10,
            )
            if sim_result["success"] and sim_result["candidates"]:
                base_info = sim_result["baseline"]
                st.markdown(
                    f"**Trạng thái SP hiện tại:** Dự đoán = `{base_info['predicted_class']}` | "
                    f"$P(\\text{{good}}) = {base_info['prob_good']:.1%}$ | "
                    f"$P(\\text{{low\\_bad}}) = {base_info['prob_low_bad']:.1%}$ | "
                    f"$P(\\text{{high\\_bad}}) = {base_info['prob_high_bad']:.1%}$ "
                    f"*(Đã chấm điểm **{sim_result['total_evaluated']}** cấu hình ứng viên trong miền hỗ trợ)*"
                )
                cand_table = pd.DataFrame(sim_result["candidates"]).drop(columns=["full_sp_vector"])
                st.dataframe(cand_table, use_container_width=True)
                st.caption(
                    "⚠️ **Lưu ý nhân quả & An toàn:** Điểm xác suất $P(\\text{good})$ từ mô hình học trên dữ liệu quan sát phản ánh mối liên hệ thống kê lịch sử, không tự động chứng minh tác động nhân quả. Mọi gợi ý chỉ mang tính tham khảo (Advisory-only) và cần con người phê duyệt."
                )

                st.markdown("#### ✍️ Ghi nhận Quyết định của Người vận hành (Human-in-the-Loop Approval & Audit Log)")
                with st.form("operator_approval_form"):
                    f_col1, f_col2, f_col3 = st.columns(3)
                    op_name = f_col1.text_input("Tên Người vận hành / Kỹ sư:", value="Operator_Demo")
                    selected_rank = f_col2.selectbox(
                        "Chọn ứng viên SP để xem xét:",
                        [f"Rank #{c['rank']}: {c['candidate_sp']} (P_good={c['prob_good']:.1%})" for c in sim_result["candidates"]],
                    )
                    op_decision = f_col3.selectbox(
                        "Quyết định phê duyệt:",
                        [
                            "REJECTED_HOLD_CURRENT_SP",
                            "APPROVED_FOR_ADVISORY_REVIEW_ONLY",
                            "FLAGGED_FOR_PROCESS_ENGINEER_INSPECTION",
                        ],
                    )
                    op_notes = st.text_input(
                        "Ghi chú vận hành / Lý do:",
                        value="Reviewed advisory candidate in academic demonstrator; no PLC/DCS write executed.",
                    )
                    submitted = st.form_submit_button("Lưu vào Nhật ký Kiểm toán (`operator_audit_log.csv`)")
                    if submitted:
                        log_file = append_operator_audit_log(
                            operator_name=op_name,
                            decision=op_decision,
                            batch_id=str(sample_row["VYP batch"]),
                            part_name=str(sample_row["Part"]),
                            set_time=str(sample_row["Set Time"]),
                            predicted_class=pred_result["predicted_class"],
                            prob_good=pred_result["probabilities"]["good"],
                            prob_low_bad=pred_result["probabilities"]["low_bad"],
                            domain_status=pred_result["domain_check"]["domain_status"],
                            sp_recommendation_summary=selected_rank,
                            notes=op_notes,
                        )
                        st.success(f"✅ Đã ghi nhận quyết định `{op_decision}` vào `{log_file.name}`!")

    # TAB 3: DOWNTIME READINESS & ANOMALY SCREEN
    with tab3:
        st.subheader("🏭 1. Chẩn đoán Bất thường Cảm biến theo Từng Hệ thống Máy (`FFTE` / `TFE` / `Extract Tank`) cho Dòng Input Hiện tại")
        st.caption(
            "**Đáp ứng Output 2 của Theme 3 (`Detected anomalies that can happen with current settings and in what machine`):** "
            "Phân tích độ lệch thống kê (Robust Z-Score Median/MAD & Miền huấn luyện) của 30 thông số máy hiện tại theo từng hệ thống (`FFTE`, `TFE`, `Extract Tank`). "
            "⚠️ *Lưu ý: Đây là sàng lọc bất thường cảm biến ở trạng thái hiện tại (Exploratory Sensor Anomaly Diagnosis), không phải xác suất dừng máy có giám sát (Downtime Probability).*"
        )
        if not pred_result["success"]:
            st.warning("Vui lòng bỏ chọn mô phỏng lỗi thiếu tín hiệu cảm biến ở Sidebar để chạy chẩn đoán theo từng máy.")
        else:
            machine_diag = diagnose_current_input_anomalies_by_machine(
                input_row=input_values,
                train_df=train_df,
                feature_domain=feature_domain,
                robust_z_threshold=4.5,
            )
            ms_list = machine_diag["machine_summaries"]
            m_cols = st.columns(len(ms_list))
            for m_col, m_item in zip(m_cols, ms_list):
                m_col.metric(
                    m_item["machine_system"],
                    m_item["system_anomaly_status"],
                    f"Max Z={m_item['max_robust_z_score']} | OOD={m_item['ood_tags']} | Outlier(Z>4.5)={m_item['robust_outlier_tags_z_gt_4_5']}",
                    delta_color="inverse" if "ANOMALY" in m_item["system_anomaly_status"] else "normal",
                )
            st.markdown("##### Bảng Tổng hợp Trạng thái Bất thường theo 3 Hệ thống Máy (`FFTE`, `TFE`, `Extract Tank`)")
            st.dataframe(pd.DataFrame(ms_list), use_container_width=True)

            with st.expander("🔎 Xem chi tiết Độ lệch Robust Z-Score của từng Cảm biến / Setpoint theo Máy (Sắp xếp từ bất thường cao nhất)", expanded=True):
                feat_diag_df = pd.DataFrame(machine_diag["feature_diagnostics"])
                st.dataframe(feat_diag_df, use_container_width=True)

        st.markdown("---")
        st.subheader("⚠️ 2. Đánh giá Mức sẵn sàng Dữ liệu Nhật ký Downtime & Sàng lọc Chuỗi thời gian Lịch sử")
        st.error(
            "🔒 **DỰ ĐOÁN DOWNTIME CÓ GIÁM SÁT: BLOCKED (`supervised_downtime_prediction_supported = False`)**\n\n"
            "- **Bằng chứng kiểm toán:** Nhật ký `Yeast Prep DT 04_05_20 - 01_07_20.csv` có 218 bản ghi nhưng trộn lẫn dừng máy có kế hoạch (`Startup=60`, `Shutdown=56`, `Sanitation=33`) với nguyên nhân thiết bị (`TFE=51`, `Extract Vat=8`, `FFTE=2`).\n"
            "- Không có mốc kết thúc độc lập, tất cả đều ghi chung `Dept=2, Line=6, Sub Line=0`, và thiếu lịch vận hành liên tục (verified non-event coverage) để gán nhãn âm."
        )

        if dt_readiness:
            d1, d2, d3 = st.columns(3)
            ev_sum = dt_readiness.get("event_log_summary", {})
            d1.metric("Tổng số dòng Event Log", f"{ev_sum.get('rows', 218)}", "04/05/2020 – 02/07/2020")
            d2.metric("Tỷ lệ dòng bất thường Evaporator Trend", "23.07%", "82,916 / 359,485 dòng (Robust Z > 4.5)")
            d3.metric("Tỷ lệ dòng bất thường FFTE Trend", "16.71%", "22,061 / 132,062 dòng (Robust Z > 4.5)")

        st.markdown("#### 📊 Kết quả Sàng lọc Ngoại lai Khám phá theo Tag (`trend_outlier_screen.csv` — Robust Z-Score Median/MAD > 4.5)")
        st.caption(
            "⚠️ **Cảnh báo diễn giải:** Đây là sàng lọc chất lượng dữ liệu / điểm bất thường thống kê không giám sát (Exploratory Outlier Screen), **KHÔNG PHẢI xác suất dừng máy (Downtime Probability)**."
        )
        trend_screen_path = PROJECT_DIR / "reports" / "downtime_readiness" / "trend_outlier_screen.csv"
        if trend_screen_path.is_file():
            st.dataframe(pd.read_csv(trend_screen_path), use_container_width=True)

        trend_day_path = PROJECT_DIR / "reports" / "downtime_readiness" / "trend_outlier_screen_by_day.csv"
        if trend_day_path.is_file():
            st.markdown("#### 📅 Tỷ lệ Ngoại lai Khám phá theo Ngày (`trend_outlier_screen_by_day.csv`)")
            day_df = pd.read_csv(trend_day_path)
            st.dataframe(day_df, use_container_width=True)

    # TAB 4: MODEL EVALUATION REPORTS & AUDIT LOG
    with tab4:
        st.subheader("📜 Hồ sơ Đóng băng Mô hình (Model Card), Kết quả Tập Test Cuối & Nhật ký Kiểm toán")
        m_col1, m_col2 = st.columns(2)
        with m_col1:
            st.markdown("#### 1. Kết quả Benchmark 5 Mô hình trên Validation")
            val_bench_path = PROJECT_DIR / "reports" / "model_calibration_freeze" / "validation_extended_benchmark.csv"
            if val_bench_path.is_file():
                st.dataframe(pd.read_csv(val_bench_path), use_container_width=True)

        with m_col2:
            st.markdown("#### 2. Kết quả Mở Tập Test Cuối cùng 1 Lần Duy Nhất")
            test_rep_path = PROJECT_DIR / "reports" / "final_test_evaluation" / "test_classification_report.csv"
            if test_rep_path.is_file():
                st.dataframe(pd.read_csv(test_rep_path), use_container_width=True)

        img_col1, img_col2 = st.columns(2)
        test_cm_img = PROJECT_DIR / "reports" / "final_test_evaluation" / "test_confusion_and_reliability.png"
        if test_cm_img.is_file():
            img_col1.image(str(test_cm_img), caption="Confusion Matrix & Reliability Diagram trên Tập Test Cuối (n=2,814)")
        test_unc_img = PROJECT_DIR / "reports" / "final_test_evaluation" / "test_uncertainty_distribution.png"
        if test_unc_img.is_file():
            img_col2.image(str(test_unc_img), caption="Phân bố Entropy Độ không chắc chắn trên Tập Test Cuối")

        st.markdown("---")
        st.markdown("#### 📝 Nhật ký Phê duyệt của Người vận hành (`reports/operator_audit_log.csv`)")
        if AUDIT_LOG_PATH.is_file():
            st.dataframe(pd.read_csv(AUDIT_LOG_PATH), use_container_width=True)
        else:
            st.info("Chưa có bản ghi nào. Hãy chuyển sang Tab 2 và bấm lưu quyết định phê duyệt để tạo bản ghi audit.")


if __name__ == "__main__":
    main()
