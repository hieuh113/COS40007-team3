# ĐẶC TẢ ĐỊNH NGHĨA DỰ ÁN

## 1. Tên dự án

**AI hỗ trợ giám sát chất lượng và khuyến nghị setpoint trong sản xuất Vegemite**

- Học phần: COS40007 Artificial Intelligence Engineering
- Theme: Theme 3 – Product Manufacturing / Mechanical Engineering

## 2. Mục tiêu

Phát triển một demonstrator AI sử dụng dữ liệu sản xuất lịch sử để hỗ trợ người vận hành giám sát chất lượng Vegemite và trạng thái quy trình. Dự án giải quyết hai câu hỏi trọng tâm của Theme 3:

1. Nên cân nhắc những cài đặt máy nào để đạt độ đặc mong muốn của sản phẩm?
2. Những bất thường quy trình nào có thể dẫn đến downtime hoặc làm mẻ sản xuất thất bại?

Dự án sẽ:

- Tiền xử lý và gán nhãn dữ liệu quy trình được cung cấp theo ba lớp chất lượng `good`, `low_bad` và `high_bad`.
- Huấn luyện và đánh giá mô hình chất lượng bằng thông số máy (SP), giá trị quy trình/cảm biến (PV), batch, `Part` và thời gian khi phù hợp.
- Dùng mô hình để xếp hạng các cấu hình SP ứng viên nhằm đạt chất lượng mong muốn, trong giới hạn vận hành đã được xác minh.
- Đánh giá liệu nhật ký downtime có đủ điều kiện cho bài toán dự đoán downtime có giám sát hay không. Nếu không, nêu rõ giới hạn và phân tích phát hiện bất thường như một nhánh riêng.
- Trình bày kết quả và giới hạn của hệ thống trong một giao diện demonstrator.

Các khuyến nghị chỉ mang tính tư vấn. Hệ thống không tự động gửi lệnh điều khiển máy móc (PLC/DCS). Mối liên hệ dự đoán trong dữ liệu lịch sử không tự chứng minh rằng thay đổi SP sẽ gây ra cải thiện chất lượng.

## 3. Yêu cầu hệ thống

### 3.1 Yêu cầu chức năng

- **Chuẩn bị dữ liệu:** Nạp các file Theme 3 được phép sử dụng; kiểm tra schema, dữ liệu thiếu, bản ghi trùng, timestamp và phân bố lớp. Giữ nguyên dữ liệu nguồn; ghi lại quyết định làm sạch và gán nhãn.
- **Nhãn chất lượng:** Tạo nhãn có thể truy xuất từ ba file chất lượng và kiểm tra mâu thuẫn giữa các batch. Xác minh vai trò của `output_log.csv` trước khi dùng file này để xử lý mâu thuẫn nhãn.
- **Dự đoán chất lượng:** Huấn luyện baseline và các mô hình phân loại dữ liệu bảng phù hợp để ước lượng lớp `good`, `low_bad` và `high_bad` từ thông tin có sẵn tại thời điểm dự đoán.
- **Khuyến nghị setpoint:** Xếp hạng các SP ứng viên theo mục tiêu đã nêu, chẳng hạn tăng xác suất dự đoán `good`. Chỉ thay đổi thông số có thể điều khiển và sử dụng giới hạn vận hành được nguồn có thẩm quyền xác nhận. Nếu thiếu giới hạn hoặc đầu vào hợp lệ, không đưa ra khuyến nghị vận hành thực tế.
- **Downtime/phát hiện bất thường:** Chỉ ghép sự kiện downtime với phép đo quy trình khi định nghĩa sự kiện, timestamp và ánh xạ thiết bị đủ tin cậy. Nếu nhãn giám sát không đủ, chỉ cung cấp anomaly score như một đầu ra khảo sát riêng, không xem là xác suất downtime.
- **Demonstrator:** Hiển thị dự đoán, SP ứng viên, chẩn đoán bất thường theo cụm thiết bị (`FFTE`, `TFE`, `Extract Tank`), bằng chứng liên quan và giới hạn dữ liệu. Ghi rõ đầu ra chỉ mang tính tư vấn và cần con người xem xét.

### 3.2 Yêu cầu dữ liệu, mô hình và đánh giá

- Tạo data dictionary ngắn gọn, mô tả ý nghĩa trường, đơn vị, nguồn, khả năng điều khiển và thời điểm dữ liệu sẵn có. Xác minh ý nghĩa SP/PV thay vì suy đoán từ tên cột.
- Giữ batch, `Part` và thời gian để truy vết, phân tích và chia tập dữ liệu. Không dùng mã định danh hoặc thông tin phát sinh sau kết quả làm đặc trưng nếu chưa có lý do phù hợp và kiểm tra rò rỉ.
- So sánh mô hình chất lượng với baseline lớp đa số. Báo confusion matrix, precision/recall/F1 theo lớp, macro-F1 và balanced accuracy; bổ sung precision-recall theo từng lớp khi hữu ích, đặc biệt với `low_bad` [11, 12].
- Nếu hiển thị xác suất mô hình hoặc dùng xác suất để xếp hạng SP, đánh giá calibration và báo cáo proper scoring rule như Brier score hoặc log loss [13, 14].
- Giữ các quan sát liên quan trong cùng batch ở cùng một tập. Với tuyên bố dự đoán sản xuất tương lai, dùng holdout theo thời gian hoặc phương pháp có xét thời gian phù hợp với câu hỏi dự đoán. Nêu rõ phép chia đánh giá khả năng tổng quát hóa nào [15, 16].
- Chỉ fit các bước điền dữ liệu thiếu, chuẩn hóa, chọn đặc trưng và cân bằng lớp trên dữ liệu huấn luyện. Không dùng số đo tương lai, nhãn cuối cùng của batch hoặc dữ liệu ghi nhận sau sự kiện downtime để dự đoán trạng thái trước đó.
- Với downtime, xác định prediction horizon và quy tắc ghép sự kiện trước khi đánh giá. Khi dữ liệu cho phép, báo cáo sự kiện phát hiện/bỏ sót, cảnh báo sai và thời gian báo trước (lead time) [20, 21].
- Xem feature importance là bằng chứng dự đoán, không phải bằng chứng nhân quả. Mối liên hệ trong dữ liệu lịch sử không chứng minh đổi SP sẽ cải thiện chất lượng; kết luận nhân quả cần giả định bổ sung và xác nhận phù hợp [18, 19].

### 3.3 An toàn, độ tin cậy và quản lý dữ liệu

- Không gửi lệnh điều khiển máy móc tự động. Yêu cầu người vận hành hoặc chuyên gia có thẩm quyền xem xét mọi khuyến nghị.
- Không suy ra giới hạn SP an toàn từ giá trị nhỏ nhất/lớn nhất quan sát được trong dataset.
- Báo rõ đầu vào thiếu, không hợp lệ hoặc nằm ngoài phạm vi; không trả kết quả có vẻ thành công khi hệ thống không thể dự đoán đáng tin cậy.
- Ghi lại phiên bản dataset, quy tắc gán nhãn, chiến lược chia tập, phiên bản mô hình/phần mềm và random seed để bảo đảm khả năng tái lập.

### 3.4 Đối chiếu rubric

Dự án đáp ứng các tiêu chí chấm điểm Theme 3:

- Tiền xử lý dữ liệu và trích xuất đặc trưng — **35%**
- Huấn luyện và kiểm định — **20%**
- Khuyến nghị SP và dự đoán downtime — **25%**
- Chỉ số đánh giá — **10%**
- Giao diện người dùng — **10%**

### 3.5 Tiêu chí nghiệm thu

1. Nhãn chất lượng và quyết định tiền xử lý được ghi lại, có thể truy xuất về file nguồn.
2. Mô hình chất lượng được so sánh với baseline và đánh giá trên các batch và/hoặc giai đoạn thời gian giữ lại, kèm metric theo lớp.
3. Cách chia tập và pipeline tiền xử lý ngăn rò rỉ theo batch/bản ghi trùng; các phép biến đổi chỉ được fit trên dữ liệu huấn luyện.
4. Đầu ra SP nằm trong giới hạn vận hành đã xác minh và được ghi rõ là tư vấn; nếu thiếu giới hạn được xác nhận, hệ thống từ chối đưa ra khuyến nghị vận hành thực tế.
5. Chỉ gọi downtime là dự đoán khi nhãn sự kiện, thời gian, horizon và đánh giá đã được xác minh. Nếu không, phải báo cáo rõ là kết quả đánh giá mức sẵn sàng dữ liệu hoặc phân tích bất thường.
6. Demonstrator phân biệt các loại đầu ra, nêu giới hạn và không điều khiển thiết bị.

## 4. Đầu vào

### 4.1 Dữ liệu chất lượng và quy trình được cung cấp

Nguồn chính là `Theme3/data_02_07_2019-26-06-2020/`. Tài liệu Theme 3 mô tả dữ liệu bao phủ khoảng một năm sản xuất với các batch dùng những loại yeast khác nhau (`Part`).

Kiểm kê trong workspace:

- `good.csv`: 13.302 dòng.
- `low bad.csv`: 2.578 dòng.
- `high bad.csv`: 14.495 dòng.
- Tổng cộng: 30.375 dòng thô; tỷ lệ lớp xấp xỉ lần lượt là 43,8%, 8,5% và 47,7%.
- Ba file có 33 cột chung, gồm `VYP batch`, `Part`, `Set Time`, bảy cột SP và các giá trị quy trình/cảm biến. Ví dụ: `FFTE Feed solids SP`, `TFE Vacuum pressure SP`, `FFTE Feed solids PV`, `TFE Temperature` và `TFE Production solids PV`.
- `FFTE`, `TFE` và `Extract Tank` là các hệ thống sản xuất được nêu trong tài liệu Theme 3.

Các số liệu này được tái tạo bằng pipeline của dự án. Kiểm tra phát hiện 4.230 dòng trùng hoàn toàn và batch `97_2020_06_25` xuất hiện trong cả `good` và `low_bad`, với 36 tổ hợp SP/PV giống nhau nhưng mang nhãn khác nhau. Hệ thống ghi lại và cách ly mâu thuẫn chưa giải quyết thay vì tự chọn nhãn.

### 4.2 Downtime và dữ liệu quy trình bổ sung

- File downtime `Theme3/Downtime/Yeast Prep DT 04_05_20 - 01_07_20.csv` có 218 dòng, trong khoảng 04/05–02/07/2020. File có các trường như ngày/giờ sản xuất, line/sub-line, nguyên nhân, thời lượng và ghi chú. Không mặc định mọi bản ghi đều là sự cố ngoài kế hoạch.
- Workspace còn có các file Infinity về sản xuất và dữ liệu trend tần suất cao của Evaporator/FFTE. Trước khi ghép với dữ liệu chất lượng, cần xác minh schema, đơn vị, timestamp, tag thiết bị và liên kết batch.

### 4.3 Đặc trưng và metadata đầu vào

- **SP:** cài đặt máy có thể được người vận hành điều chỉnh.
- **PV/cảm biến:** giá trị quy trình được đo; cần xác minh ý nghĩa, đơn vị và thời điểm có sẵn của từng trường.
- **`Part`:** loại yeast/nguyên liệu; giữ lại để phân tích và chia nhóm phù hợp.
- **`VYP batch` và `Set Time`:** mã batch và timestamp dùng để truy vết, liên kết dữ liệu và chia tập; không tự động dùng làm đặc trưng mô hình.
- **Downtime:** thời gian, loại sự kiện và ánh xạ thiết bị/hệ thống, cùng dữ liệu quy trình được ghi trước prediction horizon.

## 5. Đầu ra mong đợi

### 5.1 Mô hình chất lượng

- Lớp chất lượng dự đoán và, nếu được kiểm định đầy đủ, xác suất của `good`, `low_bad` và `high_bad`.
- So sánh với baseline, confusion matrix, precision/recall/F1 từng lớp, macro-F1 và balanced accuracy.
- Kết quả precision-recall cho lớp thiểu số khi phù hợp. Nếu hiển thị hoặc dùng xác suất để xếp hạng SP, báo cáo calibration và Brier score hoặc log loss.
- Đánh giá trên batch/giai đoạn thời gian giữ lại; nêu rõ giới hạn dữ liệu và mâu thuẫn nhãn chưa giải quyết.

### 5.2 Khuyến nghị SP

- Danh sách xếp hạng các cấu hình SP ứng viên theo mục tiêu chất lượng đã xác định, giữ cố định trạng thái quy trình không thể điều khiển.
- Giá trị SP hiện tại và ứng viên, mức thay đổi, điểm mô hình và việc ứng viên có đáp ứng giới hạn vận hành đã xác minh hay không.
- Phân tích độ nhạy hoặc đánh giá của chuyên gia nếu khả thi. Đầu ra chỉ mang tính tư vấn, không chứng minh cải thiện nhân quả. Nếu chưa có giới hạn vận hành an toàn, phải nêu rõ không thể đưa ra khuyến nghị vận hành thực tế.

### 5.3 Downtime và bất thường

- Nếu dữ liệu sự kiện đầy đủ: đầu ra nguy cơ downtime cho prediction horizon và thiết bị/hệ thống xác định, được đánh giá bằng metric phù hợp theo sự kiện và thời điểm cảnh báo.
- Nếu dữ liệu sự kiện không đầy đủ: cung cấp anomaly score riêng hoặc báo cáo mức sẵn sàng dữ liệu; không trình bày đây là dự đoán downtime đã được xác nhận.

### 5.4 Demonstrator

- Giao diện nhận batch/trạng thái quy trình hợp lệ và hiển thị kết quả chất lượng, xếp hạng SP hoặc lý do không đưa ra khuyến nghị vận hành, cùng chẩn đoán downtime/anomaly theo từng cụm máy (`FFTE`, `TFE`, `Extract Tank`).
- Hiển thị rõ trạng thái thiếu hoặc ngoài phạm vi, độ không chắc chắn và nguồn gốc kết quả; không thực hiện điều khiển máy.

## 6. Sản phẩm bàn giao

1. Đặc tả dự án này và data dictionary cho các trường được phép sử dụng.
2. Báo cáo kiểm toán dữ liệu, pipeline gán nhãn và tiền xử lý có thể tái lập, bao gồm nhật ký bản ghi trùng và mâu thuẫn nhãn.
3. Script phân tích dữ liệu, mô hình hóa chất lượng, kiểm định và tính metric, kèm cấu hình và hướng dẫn chạy.
4. Baseline và mô hình chất lượng đã đánh giá, nêu rõ cách chia batch/thời gian và giới hạn.
5. Phương pháp xếp hạng SP ứng viên theo giới hạn vận hành đã xác minh, cùng tài liệu giải thích cổng kiểm soát an toàn.
6. Phân tích mức sẵn sàng dữ liệu downtime và sàng lọc anomaly được phân biệt rõ.
7. Demonstrator, hướng dẫn sử dụng, báo cáo kỹ thuật và thuyết trình mô tả phương pháp, bằng chứng đáp ứng rubric, kết quả, rủi ro và giới hạn.
8. Mã nguồn/cấu hình có thể chia sẻ và đầu ra mẫu. Không phân phối dữ liệu sản xuất nếu chưa được cấp phép.

**Cơ sở dự án:** COS40007 Design Project, Theme 3; các file được cung cấp trong `Theme3/`. Tài liệu nghiên cứu phương pháp được chú giải trong [`docs/RESEARCH_BACKGROUND_THEME3_VI.md`](RESEARCH_BACKGROUND_THEME3_VI.md); các nguồn này hỗ trợ lựa chọn phương pháp nhưng không xác nhận hiệu năng hoặc giới hạn vận hành an toàn của dây chuyền.
