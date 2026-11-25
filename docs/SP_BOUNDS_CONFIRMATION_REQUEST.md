# Yêu cầu xác nhận operating bounds cho SP

## 1. Mục đích

Tài liệu này ghi nhận kết quả rà soát và quyết định khóa cổng an toàn (Safety Gate) đối với 7 thông số cài đặt máy (Setpoint - SP) của hệ thống `FFTE` và `TFE`. Khoảng giá trị quan sát trong dữ liệu lịch sử (`observed_sp_ranges.csv`) không được dùng làm bằng chứng cho giới hạn vận hành an toàn của thiết bị.

## 2. Bảng trạng thái xác nhận 7 Setpoint trong bộ dữ liệu học phần

Do gói dữ liệu đề bài COS40007 Theme 3 chỉ cung cấp các tệp CSV lịch sử mà không kèm theo bản vẽ P&ID, danh mục tag Historian hay quy trình vận hành chuẩn (SOP) của nhà máy, toàn bộ 7 SP được chốt ở trạng thái **`NOT_APPROVED` cho điều khiển/khuyến nghị vận hành thực tế tại nhà máy**, cụ thể như sau:

| SP field | Unit | Min approved | Max approved | Observed Train Range (Chỉ tham khảo miền dữ liệu, KHÔNG phải giới hạn an toàn) | Source/P&ID/tag | Control authority | Quyết định Gate vận hành (`approved_operating_bounds.json`) | Confirmed by | Date |
|---|---|---:|---:|---|---|---|---|---|---|
| `FFTE Feed solids SP` | `UNSPECIFIED_IN_BRIEF` | `null` | `null` | 25.0 – 50.0 (q01–q99: 25.0 – 50.0) | Không có P&ID trong workspace | Operator SP (theo brief); chờ xác nhận PLC/DCS loop | `NOT_APPROVED` (Operational Gate Blocked) | Nhóm dự án Theme 3 (Academic Governance) | 22/11/2026 |
| `FFTE Production solids SP` | `UNSPECIFIED_IN_BRIEF` | `null` | `null` | 39.0 – 43.0 (q01–q99: 39.0 – 43.0) | Không có P&ID trong workspace | Operator SP (theo brief); chờ xác nhận PLC/DCS loop | `NOT_APPROVED` (Operational Gate Blocked) | Nhóm dự án Theme 3 (Academic Governance) | 22/11/2026 |
| `FFTE Steam pressure SP` | `UNSPECIFIED_IN_BRIEF` | `null` | `null` | 12.0 – 850.0 (q01–q99: 55.0 – 158.79) | Không có P&ID trong workspace | Operator SP (theo brief); chờ xác nhận PLC/DCS loop | `NOT_APPROVED` (Operational Gate Blocked) | Nhóm dự án Theme 3 (Academic Governance) | 22/11/2026 |
| `TFE Out flow SP` | `UNSPECIFIED_IN_BRIEF` | `null` | `null` | 1240.0 – 3278.6 (q01–q99: 1725.3 – 3083.72) | Không có P&ID trong workspace | Operator SP (theo brief); chờ xác nhận PLC/DCS loop | `NOT_APPROVED` (Operational Gate Blocked) | Nhóm dự án Theme 3 (Academic Governance) | 22/11/2026 |
| `TFE Production solids SP` | `UNSPECIFIED_IN_BRIEF` | `null` | `null` | 0.0 – 88.0 (q01–q99: 27.49 – 85.0; Val max: 98.0) | Không có P&ID trong workspace | Operator SP (theo brief); chờ xác nhận PLC/DCS loop | `NOT_APPROVED` (Operational Gate Blocked) | Nhóm dự án Theme 3 (Academic Governance) | 22/11/2026 |
| `TFE Vacuum pressure SP` | `UNSPECIFIED_IN_BRIEF` | `null` | `null` | -89.0 – -35.0 (q01–q99: -89.0 – -36.37) | Không có P&ID trong workspace | Operator SP (theo brief); chờ xác nhận PLC/DCS loop | `NOT_APPROVED` (Operational Gate Blocked) | Nhóm dự án Theme 3 (Academic Governance) | 22/11/2026 |
| `TFE Steam pressure SP` | `UNSPECIFIED_IN_BRIEF` | `null` | `null` | 2.0 – 135.0 (q01–q99: 55.0 – 127.55) | Không có P&ID trong workspace | Operator SP (theo brief); chờ xác nhận PLC/DCS loop | `NOT_APPROVED` (Operational Gate Blocked) | Nhóm dự án Theme 3 (Academic Governance) | 22/11/2026 |

## 3. Trả lời 7 câu hỏi kiểm toán kỹ thuật (Technical Audit Findings)

1. **Unit chính thức và scale cho mỗi SP là gì?** Chưa được cung cấp trong dữ liệu gốc (`PENDING_VERIFICATION`). Tuyệt đối không tự gán đơn vị (`%`, `kPa`, `L/h`) nếu không có tài liệu nhà máy.
2. **Historian/tag name và P&ID/thiết bị tương ứng là gì?** Chỉ biết tiền tố hệ thống (`FFTE`, `TFE`) từ tên cột và đề bài `Theme 3.md`; không có mã tag P&ID chi tiết.
3. **Giá trị min/max nào là approved operating limit?** Không có trong workspace. Khoảng giá trị quan sát trong tập Train (ví dụ `FFTE Steam pressure SP` từ 12 đến 850, trong khi phân vị 1%–99% nằm ở 55–158.79) cho thấy cực trị lịch sử có thể chứa nhiễu hoặc trạng thái khởi động/tắt máy, không thể dùng làm giới hạn an toàn.
4. **SP có thể được người vận hành điều khiển trực tiếp không?** Theo đề bài `Theme 3.md`, 7 cột hậu tố `SP` là thông số người vận hành có thể điều chỉnh; tuy nhiên quyền điều khiển thực tế trên PLC/DCS chưa được xác minh.
5. **Có giãn cách độc lập, deadband, slew-rate, startup/shutdown hoặc operating mode khác nhau không?** Chưa có tài liệu quy trình xác nhận.
6. **Có ràng buộc riêng cho Part `Yeast - BRD`, `Yeast - BRN`, `Yeast - FMX` không?** Phân tích dữ liệu cho thấy phân bố SP thay đổi theo `Part`, do đó mọi mô phỏng gợi ý SP đều phải giữ cố định `Part` của mẻ hiện tại.
7. **Giá trị nào cùng với điều kiện process state được xem là ngoài operating domain và phải từ chối khuyến nghị?** Mọi dòng dữ liệu có giá trị SP hoặc PV nằm ngoài miền quan sát của tập Train (`train_observed_min` đến `train_observed_max`, ví dụ 3 dòng Validation có `TFE Production solids SP` đạt tới `98.0 > 88.0`) phải bị gắn cờ cảnh báo **Out-of-Domain (OOD)** ngay lập tức.

## 4. Quyết định kiến trúc cho Pipeline & Giao diện Demonstrator

Để vừa tuân thủ tuyệt đối nguyên tắc an toàn công nghiệp, vừa chứng minh đầy đủ năng lực thuật toán Prescriptive Analytics theo Rubric môn học (25% điểm SP Recommendation & Downtime):

1. **Ở chế độ Kiểm định Vận hành (`setpoint_readiness_theme3.py` & Mặc định trên UI):**
   - Không tạo tệp `approved_operating_bounds.json` giả mạo từ min/max.
   - Giữ trạng thái cổng vận hành là **`BLOCKED (NOT_APPROVED)`** và giải thích rõ lý do thiếu P&ID/SOP sign-off.
2. **Ở chế độ Mô phỏng Học thuật trên Giao diện Demonstrator (`Academic What-If Simulation Mode`):**
   - Cho phép người đánh giá/giảng viên bật chế độ mô phỏng *"What-If Candidate SP Ranking"* được giới hạn nghiêm ngặt trong miền hỗ trợ lịch sử (`q01`–`q99` của tập Train cho cùng loại `Part` hoặc các tổ hợp SP lịch sử đã từng tạo ra mẻ `good` trong tập Train), hoặc nạp một tệp `approved_operating_bounds.json` thử nghiệm.
   - Hiển thị rõ nhãn cảnh báo bắt buộc: **"ADVISORY WHAT-IF SIMULATION ONLY — NOT PLANT-APPROVED BOUNDS — NO PLC/DCS WRITE"** và yêu cầu người vận hành xác nhận (`Approve / Reject`) vào nhật ký audit.
