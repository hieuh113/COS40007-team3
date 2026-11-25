# Thiết kế Gán nhãn Chất lượng và Xử lý Xung đột Dữ liệu (Theme 3)

## 1. Phạm vi tài liệu

Tài liệu này trình bày quy tắc gán nhãn mục tiêu (`quality_class`), bằng chứng kiểm toán trên dữ liệu nguồn và quyết định kỹ thuật của nhóm đối với batch xung đột nhãn trong bài toán dự đoán độ đặc sản phẩm Vegemite (COS40007 — Theme 3).

## 2. Nguồn gốc và thống kê dữ liệu nhãn

Dữ liệu sản xuất trong `Theme3/data_02_07_2019-26-06-2020/` gồm ba tệp CSV tương ứng với ba mức độ đặc (solid consistency) của sản phẩm cuối cùng:

- `good.csv` (`good`): 13.302 dòng thô (301 batch).
- `low bad.csv` (`low_bad`): 2.578 dòng thô (59 batch).
- `high bad.csv` (`high_bad`): 14.495 dòng thô (344 batch).
- Tổng cộng: 30.375 dòng thô trên 703 mã `VYP batch` duy nhất. Sau khi loại bỏ các dòng trùng lặp hoàn toàn (exact duplicates) trong từng tệp, tập dữ liệu giảm đi 4.230 dòng dư thừa, còn lại 26.145 dòng duy nhất.

## 3. Quy tắc định nghĩa biến mục tiêu `quality_class`

| Mã nhãn | Tệp nguồn | Ý nghĩa trong bài toán | Cấp độ áp dụng | Quy tắc chống rò rỉ thông tin (Leakage Prevention) |
|---|---|---|---|---|
| `good` | `good.csv` | Sản phẩm đạt độ đặc mục tiêu | Gán theo kết quả của `VYP batch`, ánh xạ xuống từng dòng thời gian của batch | Tại mỗi thời điểm `Set Time`, mô hình chỉ sử dụng 30 biến SP/PV hiện tại để dự đoán nhãn batch; không tổng hợp các dòng tương lai trong cùng batch |
| `low_bad` | `low bad.csv` | Sản phẩm lệch chuẩn độ đặc nhóm `low bad` (lớp thiểu số ~6,8% tập train) | Gán theo kết quả của `VYP batch`, ánh xạ xuống từng dòng thời gian của batch | Không dùng kết quả kiểm tra cuối mẻ hoặc thông tin sau `Set Time` làm đặc trưng đầu vào |
| `high_bad` | `high bad.csv` | Sản phẩm lệch chuẩn độ đặc nhóm `high bad` | Gán theo kết quả của `VYP batch`, ánh xạ xuống từng dòng thời gian của batch | Không dùng kết quả kiểm tra cuối mẻ hoặc thông tin sau `Set Time` làm đặc trưng đầu vào |

### Lựa chọn thiết kế bài toán phân loại 3 lớp

1. **Không gộp hai lớp lỗi (`low_bad` và `high_bad`):** Hai nhóm lệch chuẩn độ đặc đại diện cho hai trạng thái vật lý trái chiều trong quá trình cô đặc chân không (`FFTE`/`TFE`). Việc giữ nguyên cấu trúc phân loại đa lớp (3-class classification) giúp thông tin đầu ra phục vụ trực tiếp cho bước tư vấn điều chỉnh Setpoint.
2. **Tính loại trừ lẫn nhau ở cấp batch:** Kết quả kiểm toán xác nhận trên 702/703 batch (chiếm 99,86% tổng số mẻ), mỗi mã `VYP batch` chỉ xuất hiện duy nhất ở một tệp chất lượng.
3. **Giới hạn từ bộ dữ liệu học phần:** Gói dữ liệu gốc không đính kèm biên bản đo lường phòng thí nghiệm (QC/Lab SOP) quy định ngưỡng cắt vật lý cụ thể của nhà máy. Do đó, nhãn `quality_class` được định nghĩa chặt chẽ dựa trên provenance của tệp dữ liệu nguồn.

## 4. Phân tích và quyết định cách ly batch xung đột `97_2020_06_25`

Quá trình chạy kịch bản kiểm toán [`audit_theme3_data.py`](../audit_theme3_data.py) phát hiện một trường hợp xung đột nhãn duy nhất:

- Mã mẻ sản xuất **`97_2020_06_25`** xuất hiện đồng thời trong cả hai tệp `good.csv` và `low bad.csv`.
- Sau khi khử trùng lặp, có đúng 36 tổ hợp thông số SP/PV giống hệt nhau mang nhãn `good` và 36 tổ hợp tương ứng mang nhãn `low_bad` (tổng cộng 72 bản ghi).
- Đối chiếu với tệp nhật ký `output_log.csv` (704 dòng), batch `97_2020_06_25` cũng được ghi nhận hai lần với cả hai nhãn `good` và `low_bad`. Như vậy, `output_log.csv` chỉ phản ánh lại sự trùng lặp này chứ không cung cấp căn cứ phân xử nhãn đúng.

### Phương án xử lý trong Pipeline (`preprocess_theme3_data.py`)

Nhóm thống nhất áp dụng chính sách **Cách ly toàn phần (`QUARANTINE_UNRESOLVED`)**:

- Tách toàn bộ 72 bản ghi sau khử trùng của batch `97_2020_06_25` sang tệp riêng `Theme3/Processed_Data/quarantine_conflicting_batches.csv` kèm đầy đủ thông tin truy vết (`source_file`, `source_rows`, `duplicate_count`).
- Không đưa batch này vào bất kỳ tập `train.csv`, `validation.csv` hay `test.csv` nào.
- Tuyệt đối không sử dụng bỏ phiếu đa số (majority vote), độ tương đồng khoảng cách đặc trưng hay xác suất của mô hình baseline để tự gán lại nhãn cho batch xung đột.

Sau bước cách ly, 702 batch hợp lệ (26.073 dòng duy nhất) được đưa vào chia tập theo trình tự thời gian và bảo toàn ranh giới batch: Train (490 batch / 19.809 dòng), Validation (107 batch / 3.450 dòng) và Test (105 batch / 2.814 dòng).
