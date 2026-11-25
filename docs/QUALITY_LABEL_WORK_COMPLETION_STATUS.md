# Trạng thái hoàn thành xác nhận nhãn chất lượng - Theme 3

## Tóm tắt trạng thái

- Chuẩn bị kỹ thuật: `COMPLETE`
- Xác nhận nhãn trong phạm vi học thuật (Academic Scope Freeze): `APPROVED_WITH_CONDITIONS`
- Xác nhận SOP/QC từ nhà máy ngoài workspace: `NOT_AVAILABLE_IN_COURSE_DATASET`
- Cách ly batch xung đột (`97_2020_06_25`): `QUARANTINE_UNRESOLVED` (`COMPLETE_AS_A_SAFE_TECHNICAL_STATE`)
- Công việc 1 tổng thể: `COMPLETE_FOR_ACADEMIC_EVALUATION` (Sẵn sàng chuyển sang bước Calibration & Model Freeze; giữ cảnh báo giới hạn nghiệp vụ trong Demonstrator)

Công việc 1 đã được nhóm dự án khóa hồ sơ ở trạng thái an toàn học thuật (`APPROVED_WITH_CONDITIONS` + `QUARANTINE_UNRESOLVED`) để tiến hành đóng băng mô hình và đánh giá tập Test cuối, đồng thời vẫn ghi rõ yêu cầu ký duyệt QC nếu triển khai tại nhà máy thực tế.

## Công việc kỹ thuật đã hoàn thành

### Provenance nhãn

- Đã xác nhận ánh xạ nguồn cho 702/703 batch nhất quán:
  - `good.csv` -> `good`
  - `low bad.csv` -> `low_bad`
  - `high bad.csv` -> `high_bad`
- Đã ghi số dòng nguồn:
  - good: 13.302 dòng
  - low_bad: 2.578 dòng
  - high_bad: 14.495 dòng
- Đã ghi tổng số dòng thừa sau deduplication: 4.230 dòng
- Giữ nguyên file nguồn.
- Giữ `quality_class` là nhãn sinh ra từ provenance của file nguồn.

### Xử lý batch xung đột

- Đã xác định batch `97_2020_06_25` xuất hiện ở cả `good.csv` và `low bad.csv`.
- Đã xác nhận 36 tổ hợp SP/PV giống nhau gán `good` và 36 tổ hợp giống nhau gán `low_bad`.
- Đã xác nhận `output_log.csv` ghi cả hai nhãn nhưng không giải quyết xung đột.
- Đã chốt quyết định chính thức trong [`QUALITY_LABEL_CONFIRMATION_REQUEST.md`](QUALITY_LABEL_CONFIRMATION_REQUEST.md): **`[x] QUARANTINE_UNRESOLVED`** — cách ly toàn bộ batch xung đột khỏi quá trình chuẩn bị train/validation/test có giám sát.
- Đã giữ 72 bản ghi cách ly cùng provenance trong `Theme3/Processed_Data/quarantine_conflicting_batches.csv`.

### Tài liệu đã hoàn thành

- Cập nhật [`docs/data_dictionary_theme3.md`](data_dictionary_theme3.md) về provenance và trạng thái chốt học thuật.
- Cập nhật [`docs/field_confirmation_register.csv`](field_confirmation_register.csv) cho `quality_class` và 33 trường dữ liệu.
- Hoàn tất và ký duyệt phạm vi học thuật trong [`QUALITY_LABEL_CONFIRMATION_REQUEST.md`](QUALITY_LABEL_CONFIRMATION_REQUEST.md) và [`SP_BOUNDS_CONFIRMATION_REQUEST.md`](SP_BOUNDS_CONFIRMATION_REQUEST.md).

## Giới hạn nghiệp vụ ngoài workspace (Ghi nhận vào Báo cáo & Demonstrator)

Vì gói dữ liệu học phần COS40007 không đính kèm tài liệu SOP phòng Lab/QC của nhà máy Vegemite, các thông tin sau được ghi nhận là giới hạn dữ liệu (`NOT_AVAILABLE_IN_COURSE_DATASET`) và được hiển thị minh bạch trên Demonstrator:

- Phương pháp đo kiểm phòng Lab và ngưỡng vật lý cắt lớp giữa `good`, `low_bad`, `high_bad`.
- Độ trễ thời gian từ lúc lấy mẫu tại `Set Time` đến khi có kết quả kiểm tra độ đặc cuối cùng.
- Hồ sơ gốc tại nhà máy để phân xử batch `97_2020_06_25` (do đó batch này bị cách ly vĩnh viễn khỏi mô hình).

## Quy tắc mở cổng đã tuân thủ

Nhóm dự án cam kết và đã thực thi nghiêm ngặt:

- Không tạo nhãn mới từ min/max quan sát.
- Không gán lại batch xung đột `97_2020_06_25` bằng majority vote hoặc độ giống dòng.
- Không dùng recall, macro-F1 hay accuracy để duyệt định nghĩa nhãn.
- Không dùng `output_log.csv` làm công cụ giải quyết xung đột.
- Chỉ mở tập `test.csv` một lần duy nhất sau khi đã khóa toàn bộ protocol mô hình, hiệu chỉnh xác suất và quy tắc ngưỡng.
