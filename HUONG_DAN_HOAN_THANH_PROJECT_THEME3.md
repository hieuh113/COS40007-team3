# Hướng dẫn hoàn thành dự án COS40007 - Theme 3

Tài liệu này là hướng dẫn duy nhất cho cả vòng đời project: tình trạng hiện tại, công việc còn thiếu, thứ tự thực hiện, tiêu chuẩn đánh giá và điều kiện nộp.

## 1. Mục tiêu và ranh giới

Hệ thống Theme 3 hỗ trợ ba câu hỏi:

1. Với trạng thái quy trình hiện tại, lớp chất lượng nào có khả năng xảy ra?
2. Có thể đề xuất setpoint nào trong operating envelope đã được phép?
3. Có bằng chứng đủ để dự đoán downtime hay chỉ sàng lọc anomaly?

Dữ liệu dự án là dữ liệu quan sát, không tự chứng minh tác động nhân quả của setpoint. Dữ liệu không thể chuyển thành lệnh điều khiển PLC/DCS.

## 2. Trạng thái hiện tại

### 2.1 Dữ liệu và tiền xử lý

- Ba file chất lượng có 30.375 dòng và 703 batch duy nhất.
- Có 4.230 dòng dư sau exact deduplication.
- Batch `97_2020_06_25` xuất hiện trong cả `good` và `low_bad`.
- Batch conflict đã được cách ly khỏi train/validation/test.
- Split là batch-disjoint và theo thời gian:
  - Train: 490 batch, 19.809 dòng.
  - Validation: 107 batch, 3.450 dòng.
  - Test: 105 batch, 2.814 dòng.
- Test set chưa được mở cho model selection.

### 2.2 Kết quả mô hình chất lượng

Baseline validation Random Forest:

- Accuracy: `0,6580`.
- Macro-F1: `0,4793`.
- Balanced accuracy: `0,4781`.
- Recall `low_bad`: `0,0495`, tương đương 11/222.
- Majority baseline macro-F1: `0,1993`.

Mô hình hiện là baseline thăm dò. Không được dùng kết quả validation để tuyên bố setpoint recommendation hoặc khẳng định ready for plant deployment.

### 2.2.1 So sánh mô hình và khuyến nghị benchmark tiếp theo

Random Forest chưa đạt yêu cầu đủ mạnh cho lớp thiểu số `low_bad`, dù hiện là mô hình validation tốt nhất trong bốn baseline đã chạy:

- `DummyClassifier`: macro-F1 `0,1993`.
- Logistic Regression cân bằng trọng số: macro-F1 `0,3794`.
- HistGradientBoosting: macro-F1 `0,4354`.
- Random Forest cân bằng: macro-F1 `0,4793`.

Khuyến nghị thứ tự benchmark, vẫn chỉ trên train/OOF/validation:

1. **Giữ Random Forest làm baseline có thể giải thích và so sánh model importance.** Không freeze model theo một metric duy nhất.
2. **Ưu tiên các gradient-boosted tree trong môi trường cục bộ:** HistGradientBoosting đã có trong scikit-learn; LightGBM/XGBoost/CatBoost chỉ là ứng viên cần benchmark sau khi package được xác nhận, không khẳng định sẽ thắng RF.
3. **Đánh giá logistic model hoặc PLS-discriminant như interpretable baseline** trong trường hợp cần mức giải thích cao. PLS hỗ trợ quy trình liên tục/correlation high nhưng không thay các guardrails về leakage và validation.
4. **Chưa ưu tiên TabPFN/TabICL/deep tabular models cho production candidate mặc định.** TabPFN ban đầu có giới hạn kích thước training data theo implementation; TabICL phù hợp dữ liệu lớn hơn nhưng cần benchmark local. Deep/foundation models chưa chứng minh lợi thế đủ mạnh trên dataset hiện tại chỉ dựa trên benchmark tổng quát.

Protocol bắt buộc cho benchmark tiếp:

- Giữ batch-disjoint và walk-forward split.
- Tune bằng train/OOF hoặc validation, không truy cập test.
- Báo cáo macro-F1, balanced accuracy, per-class precision/recall, one-vs-rest PR-AUC cho `low_bad`, log loss và multiclass Brier/ECE.
- Chọn calibration bằng out-of-fold predictions; không dùng observed calibration trên test.
- Báo cáo batch-level stability và worst-batch result, không chỉ mean metric.
- So sánh false alarms/alert volume cùng recall `low_bad`; không đặt threshold chỉ từ yêu cầu recall 0.05 hoặc 0.25.

Kết luận ngoài validation không được nâng thành sự phù hợp vận hành cho đến khi có calibration, batch/time robustness và test freeze đầy đủ.

### 2.3 Setpoint

Chưa đủ căn cứ để mở ranking/xếp hạng SP. Không tìm thấy operating bounds hợp lệ cho cả 7 SP trong workspace.

Các range quan sát trong báo cáo chỉ mô tả dữ liệu đã thấy. Chúng không phải hard operating limits và không được dùng để sinh candidate bounds.

### 2.4 Downtime

Chưa đủ căn cứ cho supervised downtime prediction:

- 218 dòng downtime/sự kiện trong log mẫu.
- `Time` có thể là start time nhưng chưa được xác nhận.
- Không có end timestamp độc lập.
- Không có mapping equipment/tag đã xác nhận.
- Thiếu verified uptime/non-event coverage.
- Log trộn startup, shutdown, sanitation, maintenance và process causes.

Hiện chỉ được phép giữ trend anomaly screen ở mức exploratory, không gọi là downtime probability.

## 3. Công việc 1 - Xác nhận nhãn chất lượng

### 3.1 Trạng thái gate

Dùng [QUALITY_LABEL_CONFIRMATION_REQUEST.md](docs/QUALITY_LABEL_CONFIRMATION_REQUEST.md) để thu thập sign-off. Trạng thái hiện tại:

- Chuẩn bị kỹ thuật: hoàn tất.
- Quarantine batch xung đột: hoàn tất.
- Xác nhận nhãn bằng chứng độc lập: chưa hoàn tất.

### 3.2 Đầu ra cần xác nhận

Cần xác nhận bằng tài liệu/QC authority:

- Định nghĩa `good`, `low_bad`, `high_bad`.
- Measurement/inspection tạo nhãn.
- Ngưỡng hoặc quy tắc cắt lớp.
- Nhãn được gán ở batch, lot, dòng hay thời điểm kiểm tra.
- Thời điểm nhãn có so với `Set Time`.
- Các nhãn có loại trừ lẫn nhau hay cần gộp không.
- Quyết định xử lý batch `97_2020_06_25`.
- Người duyệt, vai trò, ngày, phiên bản tài liệu và evidence.

### 3.3 Quy tắc batch xung đột

Trong thời gian chưa có sign-off:

- Giữ toàn bộ batch `97_2020_06_25` ngoài train/validation/test.
- Không dùng majority vote hoặc 36 tổ hợp giống nhau để chọn nhãn.
- Không dùng `output_log.csv` làm công cụ giải quyết.
- Không dùng kết quả mô hình hoặc observed extrema để suy nhãn.
- Chỉ reassignment sau khi có bằng chứng nghiệp vụ có thẩm quyền.

Chỉ hoàn thành Công việc 1 khi:

- `quality_class` có trạng thái `CONFIRMED`.
- Batch conflict có `QUARANTINE_UNRESOLVED` hoặc `REASSIGNED_WITH_EVIDENCE`.
- Approver, ngày xác nhận và tài liệu nguồn có trong [field_confirmation_register.csv](docs/field_confirmation_register.csv).

## 4. Công việc 2 - Xác nhận setpoint

Dùng [SP_BOUNDS_CONFIRMATION_REQUEST.md](docs/SP_BOUNDS_CONFIRMATION_REQUEST.md).

### 4.1 Dữ liệu bắt buộc cho 7 SP

- `FFTE Feed solids SP`
- `FFTE Production solids SP`
- `FFTE Steam pressure SP`
- `TFE Out flow SP`
- `TFE Production solids SP`
- `TFE Vacuum pressure SP`
- `TFE Steam pressure SP`

Với mỗi SP, cần xác nhận:

- Historian tag chính xác.
- Unit và scale.
- Ý nghĩa SP/PV.
- Control authority.
- Normal operating range.
- Hard equipment limit.
- Startup/shutdown range.
- Slew rate/deadband nếu có.
- Phạm vi theo Part.
- Fouling/cleaning state.
- P&ID/tag list hoặc PLC-DCS reference.
- Operating procedure được duyệt.
- Người ký, vai trò, ngày và revision.

### 4.2 Quy tắc

- Không dùng train/validation min/max làm approved bounds.
- Không ranking SP nếu bất kỳ hard bound bắt buộc nào chưa xác nhận.
- Không suy quan hệ nhân quả SP-quality từ dữ liệu quan sát.
- Chỉ mở candidate ranking sau khi cả 7 SP và control authority được phê duyệt.
- Mọi khuyến nghị là advisory-only, không ghi PLC/DCS.

Trạng thái phê duyệt:

- `APPROVED`
- `APPROVED_WITH_CONDITIONS`
- `NOT_APPROVED`

## 5. Công việc 3 - Xác nhận downtime

### 5.1 Evidence cần thu thập

- Định nghĩa start/end timestamp.
- Event taxonomy: startup, shutdown, sanitation, maintenance, unplanned fault.
- Mapping Dept/Line/Sub Line tới FFTE/TFE/Extract Tank.
- Horizon dự đoán và lead time.
- Uptime/running coverage để tạo negative cases đã xác nhận.
- Clock/timezone/DST và cách join với trend.
- False-alarm cost và missed-event cost.
- Thiết kế đánh giá theo event và thời gian.

### 5.2 Trạng thái gate

Chỉ chuyển sang supervised downtime khi đủ:

- Label rule được xác nhận.
- Equipment mapping được xác nhận.
- Horizon được chốt.
- Non-event coverage được xác minh.
- Dataset cho train/validation/test theo thời gian/batch.

Nếu thiếu dữ kiện, giữ nhánh trend anomaly là exploratory. Không xuất downtime probability hoặc claim event detection effectiveness.

## 6. Công việc 4 - Chốt protocol mô hình chất lượng

Thực hiện trước khi mở test:

- Chốt target chính và target dự phòng.
- Chốt cost của false miss và false alarm.
- Chốt danh sách baseline model.
- Chốt preprocessing fit chỉ trên train/OOF.
- Chốt batch-disjoint/time split.
- Chốt walk-forward hoặc validation protocol.
- Chốt calibration method.
- Chọn ngưỡng trên validation/OOF, không chọn trên test.
- Ghi model card, data version và code version.
- Khóa giao thức trong một tài liệu duy nhất.

Không tune dựa trên test hoặc chỉnh mô hình sau khi test đã mở.

## 7. Công việc 5 - Calibration và ngưỡng

- Fit calibration chỉ trên calibration/OOF fold.
- Báo cáo Brier score, log loss và ECE.
- Báo cáo macro-F1, precision/recall/F1 theo từng lớp.
- Báo cáo PR-AUC cho `low_bad`.
- Chọn ngưỡng theo cost đã duyệt, không dùng 0,5 mặc định.
- Kiểm tra độ ổn định theo Part nếu đủ mẫu.
- Kiểm tra độ ổn định theo thời gian/batch.
- Ghi rõ vùng domain khi mô hình không đáng tin cậy.

Nếu recall `low_bad` vẫn thấp, không cho phép dùng mô hình làm khuyến nghị vận hành.

## 8. Công việc 6 - Mở test cuối

Chỉ mở test sau khi tất cả đã freeze:

- Preprocessing.
- Hyperparameter.
- Calibration.
- Ngưỡng quyết định.
- Test protocol.
- Người duyệt và ngày khóa freeze.

Sau đó:

- Mở test split duy nhất.
- Chạy final evaluation, không chỉnh mô hình sau kết quả.
- Lưu confusion matrix và metric từng lớp.
- Lưu calibration chart và uncertainty summary.
- Lưu provenance train/validation/test.

## 9. Công việc 7 - Hoàn thiện demonstrator

Giao diện cần có:

- Quality prediction và confidence.
- SP readiness approved/conditional/not approved.
- Downtime readiness supported/blocked.
- Nguồn dữ liệu và thời điểm dự đoán.
- Batch provenance.
- Cảnh báo input thiếu hoặc ngoài operating envelope.
- Cảnh báo độ không chắc chắn.
- Advisory-only; không write/command PLC/DCS.
- Ghi duyệt/từ chối của người vận hành.
- Nhật ký audit.

Không cho phép autonomous setpoint change.

## 10. Thứ tự ưu tiên nộp

1. Hoàn tất xác nhận `good`, `low_bad`, `high_bad`.
2. Hoàn tất xác nhận operating bounds cho 7 SP.
3. Hoàn tất downtime evidence nếu làm nhánh downtime.
4. Chốt cost và evaluation protocol.
5. Calibration và threshold freeze.
6. Mở test cuối một lần.
7. Hoàn thiện demonstrator.
8. Kiểm tra report, presentation và final report.

## 11. Điều kiện kết luận

### Quality prediction

Chỉ kết luận sau một lần chạy test cuối theo protocol đã freeze.

### Setpoint recommendation

Chỉ mở sau khi 7 SP có bounds/source/control authority được duyệt và quality model được freeze/calibration.

### Downtime prediction

Chỉ mở sau khi event semantics, equipment mapping, horizon, non-event coverage và event evaluation đạt gate.

### Ready for deployment

Chỉ được kết luận sau expert approval, controlled trial, final test, safety sign-off và quy trình vận hành con người duyệt.

## 12. Hồ sơ nguồn cần tham chiếu

- [QUALITY_LABEL_CONFIRMATION_REQUEST.md](docs/QUALITY_LABEL_CONFIRMATION_REQUEST.md)
- [QUALITY_LABEL_WORK_COMPLETION_STATUS.md](docs/QUALITY_LABEL_WORK_COMPLETION_STATUS.md)
- [SP_BOUNDS_CONFIRMATION_REQUEST.md](docs/SP_BOUNDS_CONFIRMATION_REQUEST.md)
- [field_confirmation_register.csv](docs/field_confirmation_register.csv)
- [data_dictionary_theme3.md](docs/data_dictionary_theme3.md)
- [data_audit_theme3.md](docs/data_audit_theme3.md)
- [PROJECT_SPECIFICATION_DEFINITION_THEME3_VI.md](docs/PROJECT_SPECIFICATION_DEFINITION_THEME3_VI.md)
- [RESEARCH_BACKGROUND_THEME3_UAV_VI.md](docs/RESEARCH_BACKGROUND_THEME3_UAV_VI.md)
