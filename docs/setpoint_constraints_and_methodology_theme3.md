# Phân tích Ràng buộc Vận hành và Cơ chế Khuyến nghị Setpoint (Theme 3)

## 1. Mục tiêu thiết kế

Trong bài toán Theme 3, bên cạnh việc dự đoán lớp chất lượng sản phẩm (`good`, `low_bad`, `high_bad`), hệ thống cần gợi ý thông số cài đặt máy (Setpoint — `SP`) giúp nâng cao khả năng thu được sản phẩm đạt chuẩn (`good`). Tài liệu này tổng hợp cơ sở lý thuyết điều khiển quá trình bốc hơi thực phẩm, kết quả kiểm toán 7 biến Setpoint trong dữ liệu và kiến trúc hai chế độ (Safety Gate & Academic What-If Simulation) được nhóm triển khai trong hệ thống.

## 2. Kiểm toán 7 biến Setpoint trong dữ liệu lịch sử

Dữ liệu chất lượng cung cấp 7 cột cài đặt máy thuộc hai hệ thống cô đặc `FFTE` (Falling Film Tubular Evaporator) và `TFE` (Thin Film Evaporator). Kết quả thống kê từ [`setpoint_readiness_theme3.py`](../setpoint_readiness_theme3.py) trên tập Train và Validation như sau:

| Tên biến Setpoint (`SP`) | Hệ thống | Khoảng quan sát Train (`min` – `max`) | Khoảng phân vị Train (`q01` – `q99`) | Khoảng quan sát Validation (`min` – `max`) | Số dòng Validation vượt ngoài Train `min`–`max` |
|---|---|---:|---:|---:|---:|
| `FFTE Feed solids SP` | FFTE | 25,0 – 50,0 | 25,0 – 50,0 | 25,0 – 50,0 | 0 |
| `FFTE Production solids SP` | FFTE | 39,0 – 43,0 | 39,0 – 43,0 | 41,0 – 43,0 | 0 |
| `FFTE Steam pressure SP` | FFTE | 12,0 – 850,0 | 55,0 – 158,79 | 60,0 – 160,0 | 0 |
| `TFE Out flow SP` | TFE | 1240,0 – 3278,6 | 1725,3 – 3083,72 | 1925,3 – 2846,51 | 0 |
| `TFE Production solids SP` | TFE | 0,0 – 88,0 | 27,49 – 85,0 | 0,0 – 98,0 | 3 |
| `TFE Vacuum pressure SP` | TFE | -89,0 – -35,0 | -89,0 – -36,37 | -80,0 – -36,37 | 0 |
| `TFE Steam pressure SP` | TFE | 2,0 – 135,0 | 55,0 – 127,55 | 2,0 – 130,0 | 0 |

### Nhận xét kỹ thuật từ số liệu quan sát

1. **Cực trị lịch sử không phải giới hạn phần cứng an toàn:** Ở biến `FFTE Steam pressure SP`, khoảng phân vị 1%–99% nằm gọn trong dải `55,0 – 158,79`, nhưng giá trị cực đại trong lịch sử vọt lên tới `850,0` và cực tiểu xuống `12,0`. Tương tự, `TFE Production solids SP` có giá trị `0,0` (trạng thái khởi động/ngừng cấp liệu) và có 3 dòng trên tập Validation đạt `98,0` vượt ra ngoài miền huấn luyện (`88,0`). Nếu lấy trực tiếp `[min, max]` của CSV làm miền tối ưu hóa tự động, thuật toán có nguy cơ đề xuất các điểm cài đặt rơi vào trạng thái dừng máy hoặc quá áp.
2. **Thiếu thông số kỹ thuật nhà máy trong gói dữ liệu:** Bộ dữ liệu môn học không đi kèm bản vẽ P&ID, đơn vị vật lý chuẩn của từng kênh đo hay tốc độ thay đổi cho phép (slew-rate) trên bộ điều khiển PLC/DCS.

## 3. Cơ sở học thuật cho thiết kế ràng buộc Setpoint

Thiết kế module khuyến nghị Setpoint của nhóm dựa trên ba nhóm tài liệu nghiên cứu chính:

### 3.1 Đặc tính vật lý của thiết bị cô đặc màng rơi (Falling-Film / Thin-Film Evaporator)
- **Zhang et al. (2018)** (*Journal of Food Engineering*, 225, 26–33, DOI: `10.1016/j.jfoodeng.2018.01.016`) và **Silveira et al. (2013)** (*Dairy Science & Technology*, 93, 537–549): Quá trình bốc hơi thực phẩm nhiều cấp chịu sự tương tác phi tuyến chặt chẽ giữa áp suất hơi đốt, độ chân không và nồng độ chất khô đầu vào.
- **Morison et al. (2006)** (*Food and Bioproducts Processing*, 84(C4), 302–310) và **Paramalingam et al. (2000)** (*Food and Bioproducts Processing*, 78(C4), 79–84): Lưu lượng nhập liệu và nhiệt độ thành ống bị giới hạn bởi ngưỡng thấm ướt tối thiểu (*minimum wetting rate*); nếu giảm lưu lượng hoặc tăng nhiệt quá mức sẽ gây khô màng cục bộ (*film break-up*) và đóng cặn (*fouling*).
- **Cyklis (2022)** (*Journal of Food Engineering*, 317, 110884, DOI: `10.1016/j.jfoodeng.2021.110884`): Trạng thái bám bẩn thiết bị làm dịch chuyển hệ số truyền nhiệt theo thời gian, giải thích hiện tượng dịch chuyển phân phối cảm biến (domain shift) giữa các giai đoạn sản xuất.

### 3.2 Điều khiển đa biến có ràng buộc và phân tích đề xuất (Prescriptive Analytics)
- **Hofmann et al. (2021)** (*Journal of Process Control*, 106, 72–83) và **Van Wijck et al. (1994)** (*Food Control*, 5, 83–89): Các biến điều khiển trong hệ thống bốc hơi phải được đặt trong miền ràng buộc cứng (*hard equipment envelope*) và ràng buộc vận hành ổn định (*soft operational envelope*).
- **Bertsimas & Kallus (2020)** (*Management Science*, 66(3), 1025–1044), **Elmachtoub & Grigas (2022)** (*Management Science*, 68(1), 9–26) và **Pearl (2009)** (*Statistics Surveys*, 3, 96–146): Mô hình phân loại huấn luyện trên dữ liệu quan sát lịch sử chỉ ước lượng xác suất có điều kiện $P(Y=\text{good} \mid \text{SP}, \text{PV})$, không tự động chứng minh quan hệ nhân quả khi can thiệp thay đổi SP. Do đó, đầu ra đề xuất phải giới hạn trong miền dữ liệu có mật độ mẫu hỗ trợ (model support region) và có kỹ sư vận hành phê duyệt.

## 4. Kiến trúc triển khai trong Pipeline và Web Demonstrator

Để giải quyết đồng thời bài toán học thuật của Theme 3 và nguyên tắc an toàn công nghiệp, nhóm triển khai cơ chế hai lớp trong [`setpoint_readiness_theme3.py`](../setpoint_readiness_theme3.py) và [`demonstrator_engine_theme3.py`](../demonstrator_engine_theme3.py):

1. **Lớp kiểm soát an toàn vận hành (Operational Safety Gate):**
   - Kiểm tra sự tồn tại và tính hợp lệ của tệp cấu hình giới hạn được phê duyệt `approved_operating_bounds.json` (theo cấu trúc mẫu `approved_operating_bounds.template.json`).
   - Khi chưa có thông số P&ID chính thức từ nhà máy, hệ thống giữ trạng thái cổng vận hành ở mức `NOT_APPROVED` và khóa mọi kết nối điều khiển trực tiếp (`NO PLC/DCS WRITE`).
2. **Lớp mô phỏng xếp hạng Setpoint tư vấn (Advisory What-If Candidate SP Ranking):**
   - Trên giao diện Streamlit Demonstrator, hệ thống cung cấp chế độ phân tích độ nhạy What-If cho người vận hành trong miền hỗ trợ lịch sử (`q01`–`q99` của tập Train).
   - Giữ cố định loại nguyên liệu `Part` (`Yeast - BRD`, `Yeast - BRN`, `Yeast - FMX`) và toàn bộ 23 biến cảm biến đo lường (`PV`) tại thời điểm hiện tại.
   - Quét lưới ứng viên thay đổi từng thông số SP một (*one-at-a-time sensitivity*) kết hợp đối chiếu với các vector 7-SP lịch sử đã tạo ra mẻ `good` trên cùng loại `Part` trong tập Train.
   - Chấm điểm bằng mô hình Random Forest đã đóng băng, xếp hạng Top-K cấu hình giúp cải thiện $P(\text{good})$, hiển thị độ lệch $\Delta \text{SP}$, chỉ số độ không chắc chắn (Normalized Entropy) và lưu quyết định phê duyệt/từ chối của người vận hành vào nhật ký `reports/operator_audit_log.csv`.
