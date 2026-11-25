# Yêu cầu xác nhận nhãn chất lượng - Theme 3

## 1. Mục đích

Yêu cầu định nghĩa có thẩm quyền và ký duyệt cho ba nhãn chất lượng hiện được sinh từ tên file nguồn:

- `good`
- `low_bad`
- `high_bad`

Tài liệu này ghi nhận kết quả rà soát dữ liệu và quyết định chốt phạm vi học thuật của nhóm dự án COS40007 Theme 3 trên bộ dữ liệu được cung cấp.

## 2. Bằng chứng hiện có trong workspace

Dữ liệu nguồn hiện chứa:

- `good.csv`: 13.302 dòng nguồn.
- `low bad.csv`: 2.578 dòng nguồn.
- `high bad.csv`: 14.495 dòng nguồn.
- 4.230 dòng thừa sau khi loại bản sao hoàn toàn trên ba file nguồn.
- Batch `97_2020_06_25` xuất hiện ở cả `good.csv` và `low bad.csv`.
- Batch `97_2020_06_25` có 36 tổ hợp SP/PV giống nhau gán `good` và 36 tổ hợp giống nhau gán `low_bad`.
- `output_log.csv` ghi batch này hai lần, một lần `good` và một lần `low_bad`; log không giải quyết xung đột.
- Pipeline tiền xử lý cách ly toàn bộ batch, đồng thời giữ 72 bản ghi xung đột để audit.
- Kết quả baseline chỉ mang tính tạm thời: Random Forest macro-F1 validation xấp xỉ `0,4793`; recall `low_bad` xấp xỉ `0,0495`.

Các dữ kiện trên là provenance dữ liệu được trích xuất từ bộ dữ liệu đề bài Theme 3.

## 3. Phạm vi nhãn cần xác nhận

Bảng chốt trạng thái nhãn cho vòng đời dự án học thuật (dựa trên phạm vi tài liệu đề bài COS40007 Theme 3):

| Nhãn | Định nghĩa | Phép đo/kiểm tra | Ngưỡng/quy tắc | Áp dụng ở cấp | Thời điểm có nhãn | Tài liệu nguồn | Người duyệt/ngày |
|---|---|---|---|---|---|---|---|
| `good` | Sản phẩm đạt độ đặc (solid consistency) mục tiêu theo phân loại file nguồn `good.csv` | Không được cung cấp trong bộ dữ liệu học phần (chờ SOP/QC nhà máy nếu triển khai thực tế) | Sinh trực tiếp từ provenance file nguồn `good.csv` (loại trừ batch xung đột) | Cấp batch (`VYP batch`), ánh xạ xuống từng dòng quan sát của batch | Kết quả chất lượng của batch; dùng làm target dự đoán tại mỗi `Set Time` (không dùng biến tương lai) | `Theme 3.md` & `Theme3/data_02_07_2019-26-06-2020/good.csv` | Nhóm dự án Theme 3 (Academic Scope Freeze) / 22/11/2026 |
| `low_bad` | Sản phẩm không đạt độ đặc chuẩn — nhóm `low bad` theo phân loại file nguồn `low bad.csv` | Không được cung cấp trong bộ dữ liệu học phần (chờ SOP/QC nhà máy nếu triển khai thực tế) | Sinh trực tiếp từ provenance file nguồn `low bad.csv` (loại trừ batch xung đột) | Cấp batch (`VYP batch`), ánh xạ xuống từng dòng quan sát của batch | Kết quả chất lượng của batch; dùng làm target dự đoán tại mỗi `Set Time` (không dùng biến tương lai) | `Theme 3.md` & `Theme3/data_02_07_2019-26-06-2020/low bad.csv` | Nhóm dự án Theme 3 (Academic Scope Freeze) / 22/11/2026 |
| `high_bad` | Sản phẩm không đạt độ đặc chuẩn — nhóm `high bad` theo phân loại file nguồn `high bad.csv` | Không được cung cấp trong bộ dữ liệu học phần (chờ SOP/QC nhà máy nếu triển khai thực tế) | Sinh trực tiếp từ provenance file nguồn `high bad.csv` | Cấp batch (`VYP batch`), ánh xạ xuống từng dòng quan sát của batch | Kết quả chất lượng của batch; dùng làm target dự đoán tại mỗi `Set Time` (không dùng biến tương lai) | `Theme 3.md` & `Theme3/data_02_07_2019-26-06-2020/high bad.csv` | Nhóm dự án Theme 3 (Academic Scope Freeze) / 22/11/2026 |

Các quyết định bắt buộc đã chốt:

- **`low_bad` có phải là lớp thiểu số/lỗi duy nhất cần quan tâm hay dự án được phép gộp các lớp?** Giữ nguyên bài toán phân loại 3 lớp riêng biệt (`good`, `low_bad`, `high_bad`) theo đúng yêu cầu đề bài; không tự ý gộp `low_bad` và `high_bad` thành một lớp `bad` vì hai mức độ đặc lệch chuẩn có thể tương ứng với cơ chế vật lý và hướng điều chỉnh vận hành khác nhau.
- **`low_bad` và `high_bad` có loại trừ lẫn nhau không?** Có, trên toàn bộ 702/703 batch hợp lệ, mỗi batch chỉ thuộc duy nhất một trong ba lớp (`good`, `low_bad` hoặc `high_bad`).
- **Có trạng thái trung gian hoặc trạng thái chất lượng khác bị thiếu trong dữ liệu không?** Bộ dữ liệu đề bài chỉ cung cấp 3 lớp chất lượng; không suy diễn thêm lớp trung gian ngoài dữ liệu.
- **Nhãn đã biết tại thời điểm dự đoán hay chỉ sau khi batch hoàn tất/kiểm tra lab?** Nhãn phản ánh kết quả chất lượng của mẻ sản xuất (batch outcome); tại thời điểm dự đoán `Set Time`, mô hình chỉ được phép sử dụng trạng thái SP/PV tại thời điểm đó để dự đoán nhãn của batch, tuyệt đối không dùng nhãn hay số đo tương lai của batch làm đặc trưng đầu vào.
- **Kết quả chất lượng nào có sẵn tại `Set Time` mà không làm rò rỉ thông tin tương lai?** Chỉ 30 biến số SP/PV tại đúng dòng `Set Time` (cùng metadata `Part` nếu được xác nhận có sẵn từ đầu mẻ) được xem là thông tin đầu vào hợp lệ; nhãn `quality_class` chỉ là biến mục tiêu (target).

## 4. Quyết định xử lý batch xung đột

Batch: `97_2020_06_25`

Các lựa chọn:

- `QUARANTINE_UNRESOLVED`: giữ toàn bộ batch ngoài train/validation/test cho đến khi có bằng chứng độc lập.
- `REASSIGNED_WITH_EVIDENCE`: gán batch về một nhãn có thẩm quyền và đính kèm bản ghi nguồn đã dùng để gán lại.
- `RELEASE_AS_CONFLICTED`: dùng hai cách diễn giải nhãn cho phân tích nhạy cảm; không đưa vào training như batch bình thường.

Phương án được chọn:

- [x] QUARANTINE_UNRESOLVED
- [ ] REASSIGNED_WITH_EVIDENCE
- [ ] RELEASE_AS_CONFLICTED

Bằng chứng/tham chiếu:

- Tài liệu nguồn: `docs/data_audit_theme3.md`, `Theme3/Processed_Data/quarantine_conflicting_batches.csv`, `Theme3/Processed_Data/preprocessing_manifest.json`
- Bản ghi kiểm tra/lab: Không có bản ghi phòng lab/QC độc lập trong gói dữ liệu học phần COS40007 để phân xử giữa `good.csv` và `low bad.csv` (file `output_log.csv` cũng lặp lại cả hai nhãn cho batch `97_2020_06_25`).
- Người duyệt: Nhóm dự án COS40007 Theme 3 (Nguyễn Huy Hoàng Việt, Huỳnh Quốc Hiếu, Vũ Bá Hiển)
- Vai trò người duyệt: Nhóm thực hiện dự án — Khóa phạm vi kỹ thuật & học thuật (Academic Governance Sign-off)
- Ngày: 22/11/2026
- Phiên bản: v1.0-academic-freeze

## 5. Bằng chứng cần nộp

Hồ sơ bằng chứng đã đối chiếu trong workspace:

- Đề bài chính thức `Theme 3.md` mô tả 3 file CSV `good`, `low_bad`, `high_bad` đại diện cho 3 loại độ đặc (solid consistency) của sản phẩm cuối.
- Báo cáo kiểm toán dữ liệu `docs/data_audit_theme3.md` và manifest `reports/preprocessing_manifest.json` chứng minh 702/703 batch có nhãn nhất quán tuyệt đối ở cấp batch.
- Tệp cách ly `Theme3/Processed_Data/quarantine_conflicting_batches.csv` lưu giữ toàn bộ 72 bản ghi sau khử trùng của batch `97_2020_06_25` kèm đầy đủ provenance (`source_file`, `source_rows`, `duplicate_count`).

Các nguồn sau đã được loại trừ và không dùng làm bằng chứng phân xử batch xung đột:

- Min/max quan sát của biến cảm biến.
- Bỏ phiếu đa số theo dòng trùng lặp.
- `output_log.csv` vì bản ghi ghi nhận xung đột.
- Recall/macro-F1/accuracy của baseline hoặc mô hình.
- Cụm dữ liệu hoặc độ tương đồng SP/PV.

## 6. Thông tin ký duyệt

| Trường | Giá trị |
|---|---|
| Tên người duyệt | Nguyễn Huy Hoàng Việt (10499509), Huỳnh Quốc Hiếu (104848408), Vũ Bá Hiển (104995634) |
| Vai trò | Data/ML Engineer, ML/Evaluation Coordinator, Technical Lead |
| Phòng ban | COS40007 Artificial Intelligence Engineering — Theme 3 Project Group |
| Ngày xác nhận | 22/11/2026 |
| Tên/tiêu đề tài liệu nguồn | COS40007 Theme 3 Project Brief & Data Audit Report (`docs/data_audit_theme3.md`) |
| Phiên bản tài liệu | v1.0 (Academic Freeze) |
| Trạng thái nhãn | `APPROVED_WITH_CONDITIONS` (Provenance-confirmed cho 702 batch học thuật; giữ `QUARANTINE_UNRESOLVED` cho batch `97_2020_06_25`; yêu cầu QC SOP nhà máy trước khi triển khai công nghiệp) |
| Ghi chú/điều kiện | Đủ điều kiện mở cổng huấn luyện, hiệu chỉnh xác suất (calibration) và đánh giá tập Test cuối trong phạm vi đồ án học phần. Không tự ý gán lại batch 97. |

Chữ ký duyệt:

- Tên: Nguyễn Huy Hoàng Việt, Huỳnh Quốc Hiếu, Vũ Bá Hiển
- Chữ ký/ngày: Đã thống nhất và khóa hồ sơ nhóm — 22/11/2026

## 7. Triển khai dữ liệu sau khi ký duyệt

Trạng thái thực thi sau khi khóa hồ sơ:

1. Đã cập nhật `docs/data_dictionary_theme3.md` và `docs/QUALITY_LABEL_WORK_COMPLETION_STATUS.md`.
2. Đã cập nhật trạng thái và ghi chú `quality_class` trong `docs/field_confirmation_register.csv`.
3. Giữ nguyên tập dữ liệu đã tiền xử lý tại `Theme3/Processed_Data/` (Train: 490 batch / 19.809 dòng; Validation: 107 batch / 3.450 dòng; Test: 105 batch / 2.814 dòng; Quarantine: 1 batch / 72 dòng).
4. Đủ điều kiện tiến hành chốt protocol mô hình, hiệu chỉnh xác suất Calibration và đóng băng mô hình trước khi mở tập Test một lần duy nhất.
