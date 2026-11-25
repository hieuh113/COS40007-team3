# CƠ SỞ NGHIÊN CỨU VÀ TÀI LIỆU THAM KHẢO

## Dự án Theme 3: AI hỗ trợ giám sát sản xuất Vegemite bằng dữ liệu quy trình và camera UAV

**Ngày biên soạn:** 14/10/2026  

> **Lưu ý về phạm vi bằng chứng:** Các công trình dưới đây cung cấp nền tảng và ví dụ nghiên cứu trong những lĩnh vực liên quan. Chúng không chứng minh rằng một mô hình cụ thể sẽ hoạt động tốt trên dữ liệu Vegemite, rằng các giới hạn SP cụ thể là an toàn, hoặc rằng camera UAV có thể nhận diện một tình trạng chưa được xác định và đánh giá trong bối cảnh nhà máy của dự án.

## 1. Tóm tắt

Theme 3 đặt ra ba mục tiêu phân tích chính từ dữ liệu sản xuất: dự đoán lớp chất lượng, đề xuất giá trị SP và phát hiện/dự đoán downtime. Việc bổ sung UAV nên được hiểu là thêm một **nguồn quan sát bằng hình ảnh** cho các điều kiện nhìn thấy được, không thay thế dữ liệu cảm biến và không biến UAV thành bộ điều khiển máy móc.

Tài liệu nghiên cứu cho thấy các mục tiêu này có liên hệ nhưng không đồng nhất:

1. **Dự đoán chất lượng** là bài toán học từ đầu vào quy trình để ước lượng kết quả chất lượng.
2. **Đề xuất SP** là bước hỗ trợ quyết định, phải có mục tiêu và giới hạn vận hành được xác nhận; không thể chỉ đổi tên đầu ra của mô hình phân loại thành “khuyến nghị”.
3. **Phát hiện bất thường** tìm trạng thái khác thường; điều đó không tự động có nghĩa là máy sẽ dừng.
4. **Dự đoán downtime** cần nhãn sự kiện, dữ liệu theo thời gian đáng tin cậy và khoảng cảnh báo được định nghĩa.
5. **Camera UAV** có thể hỗ trợ kiểm tra trực quan trong một số bối cảnh, nhưng cần hình ảnh phù hợp, quyền thu thập, nhãn và đánh giá riêng.

## 2. Dự đoán chất lượng trong sản xuất

Tercan và Meisen tổng hợp có hệ thống các phương pháp machine learning và deep learning dùng để dự đoán chất lượng trong sản xuất [1]. Công trình này hữu ích để định vị việc dùng dữ liệu cảm biến/quy trình cho dự đoán chất lượng và để nhận diện những vấn đề thường gặp về dữ liệu, đặc trưng và triển khai. Lieber và cộng sự cung cấp một ví dụ về dự đoán chất lượng trong các công đoạn sản xuất liên kết, kết hợp phương pháp có giám sát và không giám sát [2]. Tao và cộng sự trình bày khung rộng hơn về sản xuất thông minh dựa trên dữ liệu [3].

### Liên hệ với dự án

- Có cơ sở để khảo sát mô hình phân loại trên dữ liệu cảm biến/SP, sau khi xác nhận định nghĩa nhãn `good`, `low_bad` và `high_bad`.
- Nên lập baseline trước khi so sánh các mô hình phức tạp, báo cáo metric theo từng lớp và kiểm tra khả năng tổng quát hóa theo batch/thời gian.
- Ví dụ ở ngành khác chỉ có giá trị tham khảo về phương pháp. Chúng không xác nhận đặc trưng nào có ý nghĩa trong sản xuất Vegemite.
- Dữ liệu gần nhau trong một batch hoặc theo thời gian có thể khiến chia ngẫu nhiên theo từng hàng đánh giá quá lạc quan; cách chia phải phù hợp cấu trúc batch và thời gian.

## 3. Từ dự đoán sang đề xuất setpoint

Bertsimas và Kallus nghiên cứu mối liên hệ giữa predictive analytics và prescriptive analytics: dự đoán được dùng làm đầu vào cho một quyết định nhằm tối ưu mục tiêu trong bối cảnh dữ liệu [4]. Góc nhìn này giúp phân biệt một hệ thống trả lời “chất lượng nào có khả năng xảy ra?” với hệ thống trả lời “nên cân nhắc cấu hình SP nào?”.

### Liên hệ với dự án

Một quy trình đề xuất SP có trách nhiệm cần:

1. Chọn mục tiêu rõ ràng, chẳng hạn xếp hạng ứng viên theo xác suất dự đoán lớp `good`.
2. Giữ cố định các biến trạng thái không điều khiển được tại thời điểm tư vấn.
3. Chỉ tạo ứng viên SP trong giới hạn vận hành được xác nhận bởi tài liệu hoặc chuyên gia có thẩm quyền.
4. So sánh ứng viên với SP hiện tại và trình bày mức thay đổi, điểm mô hình cùng giới hạn.
5. Từ chối đề xuất khi thiếu giới hạn đã duyệt, đầu vào không hợp lệ hoặc trạng thái nằm ngoài miền dữ liệu.

Đây vẫn là khuyến nghị dựa trên mô hình quan sát. Dữ liệu lịch sử và xác suất dự đoán không tự chứng minh rằng thay đổi SP sẽ gây ra cải thiện chất lượng. Vì vậy, kết quả cần được chuyên gia xem xét; không được trình bày như lệnh điều khiển hay bằng chứng nhân quả.

## 4. Bất thường, bảo trì dự đoán và downtime

Carvalho và cộng sự tổng quan các phương pháp machine learning trong bảo trì dự đoán [5]. Susto và cộng sự nghiên cứu cách tiếp cận phân loại cho bảo trì dự đoán, trong đó thời điểm cảnh báo và chân trời dự đoán là những yếu tố quan trọng [6]. Yan và cộng sự khảo sát các phương pháp deep transfer learning cho phát hiện bất thường trên chuỗi thời gian công nghiệp [7].

### Cần phân biệt ba loại đầu ra

| Khái niệm | Câu hỏi chính | Yêu cầu dữ liệu |
|---|---|---|
| Phát hiện bất thường | Trạng thái hiện tại có khác với mẫu thường thấy không? | Chuỗi cảm biến và định nghĩa/giả định về trạng thái bình thường; có thể không cần nhãn downtime. |
| Phân loại hoặc dự đoán downtime | Sự kiện dừng có xảy ra trong khoảng thời gian xác định không? | Nhãn sự kiện đủ tin cậy, timestamp, ánh xạ máy/hệ thống và dữ liệu trước sự kiện. |
| Bảo trì dự đoán | Khi nào thiết bị có thể cần can thiệp/bảo trì? | Dữ liệu lỗi hoặc bảo trì và quy tắc đánh giá phù hợp với mục tiêu bảo trì. |

### Liên hệ với dự án

- Dữ liệu downtime Theme 3 được mô tả là chỉ có trong tháng 5–6/2020. Cần kiểm tra số lượng sự kiện và mức độ đầy đủ trước khi quyết định có huấn luyện dự đoán downtime hay không.
- Không có bản ghi downtime không đồng nghĩa chắc chắn với “bình thường”; phải biết nhật ký có ghi đầy đủ các sự kiện hay không.
- Nếu dữ liệu không đủ cho dự đoán có giám sát, có thể báo cáo phân tích bất thường như một nhánh riêng, nhưng không gọi đó là dự đoán shutdown đã được xác nhận.
- Khi có nhãn và timestamp phù hợp, nên định nghĩa trước khoảng dự đoán/lead time; đánh giá cả cảnh báo sai, khả năng phát hiện sự kiện và thời gian cảnh báo.
- Do sự kiện downtime thường ít hơn quan sát bình thường, accuracy đơn lẻ có thể gây hiểu nhầm. Cần xem precision/recall, PR-AUC khi phù hợp và số cảnh báo sai theo thời gian hoặc batch.

## 5. UAV và thị giác máy tính trong kiểm tra công nghiệp

Nooralishahi và cộng sự tổng quan kiểm tra không phá hủy cơ sở công nghiệp bằng drone và đưa ra các nghiên cứu trường hợp [8]. Al Radi và cộng sự nghiên cứu kiểm tra bằng thị giác hoạt động của flare stack với UAV; bài báo mô tả phát hiện ngọn lửa/khói trong bối cảnh được nghiên cứu [9]. Đây là ví dụ về UAV như nền tảng đưa camera tới vị trí quan sát, chứ không phải bằng chứng cho mọi loại nhà máy hoặc mọi tình trạng sản xuất.

Redmon và cộng sự giới thiệu YOLO, một phương pháp phát hiện đối tượng một giai đoạn [10]. Đây là công trình nền tảng về object detection, có thể dùng để giải thích một họ kỹ thuật được cân nhắc cho phân tích ảnh. Nó không phải mô hình đã được huấn luyện hoặc kiểm định trên hình ảnh UAV của dự án.

### Liên hệ với dự án

- UAV bổ sung **bằng chứng thị giác** cho những tình trạng nhìn thấy được trong trường quan sát, ví dụ khói hoặc vật cản nếu chuyên gia xác nhận chúng phù hợp với quy trình.
- Camera không thay thế sensor/PV trong việc đo trạng thái bên trong máy và không trực tiếp đo độ đặc sản phẩm.
- Cần xác định trước khu vực camera có thể quan sát, điều kiện ánh sáng/góc nhìn, nhãn hình ảnh và cách phân chia tập đánh giá.
- Nếu dùng video, chia train/test theo phiên ghi hình hoặc thời gian khi phù hợp để tránh các khung hình gần như giống nhau xuất hiện ở cả hai tập.
- Cần có phê duyệt về an toàn, quyền riêng tư và quyền lưu trữ hình ảnh trước khi thu thập dữ liệu tại địa điểm thật.
- Nếu chưa có ảnh được phép và được gán nhãn, chỉ nên trình bày thiết kế tích hợp hoặc bản minh họa chưa kiểm định, không công bố hiệu năng phát hiện.

## 6. Khoảng trống nghiên cứu và lựa chọn thiết kế

Các tài liệu được xem xét hỗ trợ tính hợp lý của từng hướng công nghệ, nhưng chưa giải quyết các câu hỏi đặc thù của dự án:

1. Các lớp `good`, `low_bad` và `high_bad` được định nghĩa chính xác như thế nào, và có batch nào xuất hiện trong nhiều lớp không?
2. Những cột SP/PV nào thực sự có thể dùng tại thời điểm dự đoán, đơn vị là gì và giới hạn vận hành nào đã được phê duyệt?
3. Nhật ký downtime có ghi đầy đủ sự kiện không, các sự kiện được ánh xạ ra sao tới `FFTE`, `TFE`, `Extract Tank` hoặc thiết bị liên quan, và dữ liệu có đủ cho một chân trời dự đoán cụ thể không?
4. Có hình ảnh UAV nào sẵn có, được phép sử dụng và gán nhãn cho các tình trạng phù hợp không?
5. Timestamp hình ảnh có thể đồng bộ đáng tin cậy với batch, cảm biến và sự kiện downtime không?

Do đó, nghiên cứu nên được dùng để **biện minh cho lựa chọn phương pháp và cách đánh giá**, chứ không để điền thay các thông tin còn thiếu của dữ liệu dự án. Kế hoạch thực nghiệm cần xác minh dữ liệu trước khi chốt mô hình, nhãn, giới hạn SP hoặc tuyên bố hiệu năng.

## 7. Cách áp dụng tài liệu nghiên cứu vào dự án

- Dùng [1]–[3] trong phần nền tảng về dự đoán chất lượng và sản xuất dựa trên dữ liệu.
- Dùng [4] để giải thích vì sao đề xuất SP là bước prescriptive analytics riêng, cần giới hạn và sự xem xét của chuyên gia.
- Dùng [5]–[7] để định nghĩa và phân biệt bảo trì dự đoán, dự đoán downtime và phát hiện bất thường.
- Dùng [8]–[9] để biện minh cho việc khảo sát UAV như nền tảng quan sát/kiểm tra trực quan trong bối cảnh công nghiệp.
- Dùng [10] như nguồn nền tảng về object detection, không như bằng chứng hiệu năng trên dữ liệu dự án.
- Dùng [11]–[14] để biện minh cho metric lớp thiểu số, đánh giá calibration và scoring rule khi đầu ra xác suất được sử dụng.
- Dùng [15]–[16] để giải thích lựa chọn kiểm định ngoài mẫu theo thời gian; kết hợp với chia nhóm theo batch theo yêu cầu dữ liệu dự án.
- Dùng [17] để nhấn mạnh việc xác minh ý nghĩa, đơn vị và thời điểm sẵn có của biến quy trình/soft sensor.
- Dùng [18]–[19] để tách bài toán dự đoán khỏi mục tiêu quyết định và suy luận nhân quả khi xếp hạng SP.
- Dùng [20]–[21] để định hướng đánh giá cảnh báo theo chuỗi thời gian/sự kiện, không chỉ từng hàng dữ liệu.
- Dùng [22] để yêu cầu xem xét chất lượng thu nhận ảnh trước khi đánh giá thị giác UAV.
- Khi viết báo cáo, trích dẫn các nghiên cứu đúng phạm vi; nêu rõ khác biệt về ngành, thiết bị, dữ liệu và điều kiện thử nghiệm.
- Không tuyên bố mô hình tốt hơn hay khuyến nghị an toàn nếu chưa có đánh giá trên tập kiểm định phù hợp và giới hạn được xác nhận.

## 8. Tài liệu tham khảo có chú giải

Các mục [1]–[10] dưới đây là bộ tài liệu nền ban đầu; [11]–[22] bổ sung đánh giá mất cân bằng, kiểm định theo thời gian, quyết định SP, downtime/anomaly và chất lượng dữ liệu ảnh; [23]–[47] mở rộng batch, calibration, process monitoring và causal readiness; [48]–[57] bổ sung bằng chứng trực tiếp cho lựa chọn mô hình tabular. Các nguồn bổ sung không xác nhận hiệu năng trên dữ liệu của dự án.

### Dự đoán chất lượng và sản xuất dựa trên dữ liệu

**[1] Tercan, H. & Meisen, T. (2022).** “Machine learning and deep learning based predictive quality in manufacturing: a systematic review.” *Journal of Intelligent Manufacturing*, 33, 1879–1905.  
DOI: [10.1007/s10845-022-01963-8](https://doi.org/10.1007/s10845-022-01963-8)  
**Loại nguồn:** Tổng quan có hệ thống.  
**Giá trị sử dụng:** Nền tảng cho việc khảo sát machine learning/deep learning trong dự đoán chất lượng sản xuất.  
**Giới hạn:** Tổng quan nhiều ngành; không xác nhận các lớp chất lượng hoặc quan hệ dữ liệu cụ thể của quy trình Vegemite.

**[2] Lieber, D., Stolpe, M., Konrad, B., Deuse, J. & Morik, K. J. (2013).** “Quality Prediction in Interlinked Manufacturing Processes based on Supervised & Unsupervised Machine Learning.” *Procedia CIRP*, 7, 193–198.  
DOI: [10.1016/j.procir.2013.05.033](https://doi.org/10.1016/j.procir.2013.05.033)  
**Loại nguồn:** Nghiên cứu trường hợp quy trình sản xuất liên kết.  
**Giá trị sử dụng:** Ví dụ về tiền xử lý, trích xuất đặc trưng và kết hợp phương pháp có giám sát/không giám sát cho dự đoán chất lượng.  
**Giới hạn:** Nghiên cứu trên quy trình cán thép; kết quả không tự chuyển giao sang sản xuất thực phẩm và không chứng minh quan hệ nhân quả.

**[3] Tao, F., Qi, Q., Liu, A. & Kusiak, A. (2018).** “Data-driven smart manufacturing.” *Journal of Manufacturing Systems*, 48, 157–169.  
DOI: [10.1016/j.jmsy.2018.01.006](https://doi.org/10.1016/j.jmsy.2018.01.006)  
**Loại nguồn:** Bài tổng quan/khung về sản xuất thông minh dựa trên dữ liệu.  
**Giá trị sử dụng:** Định vị vai trò của dữ liệu trong giám sát và hỗ trợ quyết định sản xuất.  
**Giới hạn:** Phạm vi rộng; không phải nghiên cứu trực tiếp về chất lượng Vegemite hoặc đề xuất SP cho dây chuyền cụ thể.

### Prescriptive analytics và quyết định

**[4] Bertsimas, D. & Kallus, N. (2020).** “From Predictive to Prescriptive Analytics.” *Management Science*, 66(3), 1025–1044.  
DOI: [10.1287/mnsc.2018.3253](https://doi.org/10.1287/mnsc.2018.3253)  
**Loại nguồn:** Nghiên cứu phương pháp/khung phân tích.  
**Giá trị sử dụng:** Cơ sở khái niệm cho việc dùng dự đoán để hỗ trợ lựa chọn quyết định, giúp phân biệt dự đoán chất lượng với tối ưu/đề xuất SP.  
**Giới hạn:** Không cung cấp giới hạn vận hành hay bằng chứng tác động nhân quả cho thiết bị của dự án. Trích dẫn theo thông tin tập/số năm 2020.

### Bảo trì dự đoán và phát hiện bất thường

**[5] Carvalho, T. P. et al. (2019).** “A systematic literature review of machine learning methods applied to predictive maintenance.” *Computers & Industrial Engineering*, 137, article 106024.  
DOI: [10.1016/j.cie.2019.106024](https://doi.org/10.1016/j.cie.2019.106024)  
**Loại nguồn:** Tổng quan có hệ thống.  
**Giá trị sử dụng:** Tổng hợp phương pháp ML cho bảo trì dự đoán và các cân nhắc về dữ liệu, nhãn hỏng hóc và đánh giá.  
**Giới hạn:** Không chứng minh dữ liệu downtime ngắn hoặc không đầy đủ đủ để xây dựng mô hình đáng tin cậy.

**[6] Susto, G. A., Schirru, A., Pampuri, S., McLoone, S. & Beghi, A. (2015).** “Machine Learning for Predictive Maintenance: A Multiple Classifier Approach.” *IEEE Transactions on Industrial Informatics*, 11(3), 812–820.  
DOI: [10.1109/TII.2014.2349359](https://doi.org/10.1109/TII.2014.2349359)  
**Loại nguồn:** Nghiên cứu phương pháp bảo trì dự đoán.  
**Giá trị sử dụng:** Hỗ trợ thảo luận việc định nghĩa cảnh báo, chân trời dự đoán và đánh đổi trong dự đoán sự kiện.  
**Giới hạn:** Bối cảnh nghiên cứu khác dự án; không xác nhận hiệu năng trên dữ liệu downtime Vegemite.

**[7] Yan, P. et al. (2024).** “A Comprehensive Survey of Deep Transfer Learning for Anomaly Detection in Industrial Time Series: Methods, Applications, and Directions.” *IEEE Access*, 12, 3768–3789.  
DOI: [10.1109/ACCESS.2023.3349132](https://doi.org/10.1109/ACCESS.2023.3349132)  
**Loại nguồn:** Tổng quan về phát hiện bất thường chuỗi thời gian công nghiệp.  
**Giá trị sử dụng:** Cung cấp bối cảnh về phát hiện bất thường và giúp phân biệt nhánh không giám sát với dự đoán downtime có nhãn.  
**Giới hạn:** Tổng quan không xác nhận độ chính xác trên dữ liệu dự án; học chuyển giao không loại bỏ khác biệt giữa cảm biến/dây chuyền.

### UAV và thị giác máy tính

**[8] Nooralishahi, P. et al. (2021).** “Drone-Based Non-Destructive Inspection of Industrial Sites: A Review and Case Studies.” *Drones*, 5(4), 106.  
DOI: [10.3390/drones5040106](https://doi.org/10.3390/drones5040106)  
**Loại nguồn:** Tổng quan và nghiên cứu trường hợp.  
**Giá trị sử dụng:** Nền tảng cho UAV như phương tiện thu nhận hình ảnh phục vụ kiểm tra trực quan cơ sở công nghiệp.  
**Giới hạn:** Bối cảnh công nghiệp/hạ tầng khác nhà máy cụ thể của dự án; không xác định tình trạng nào có thể nhận diện từ camera của dự án.

**[9] Al Radi, M. et al. (2022).** “Vision-based Inspection of Flare Stacks Operation Using a Visual Servoing Controlled Autonomous Unmanned Aerial Vehicle (UAV).” *IECON 2022 – 48th Annual Conference of the IEEE Industrial Electronics Society*, 1–6.  
DOI: [10.1109/IECON49645.2022.9968467](https://doi.org/10.1109/IECON49645.2022.9968467)  
**Loại nguồn:** Nghiên cứu trường hợp kiểm tra trực quan bằng UAV.  
**Giá trị sử dụng:** Ví dụ về phân tích hình ảnh UAV để giám sát tình trạng nhìn thấy được trong một bối cảnh công nghiệp.  
**Giới hạn:** Bài nghiên cứu về flare stack, không phải sản xuất thực phẩm; phần xác nhận được mô tả trong tóm tắt liên quan mô phỏng nhà máy hóa dầu. Không suy ra dự án cần điều khiển UAV tự động.

**[10] Redmon, J., Divvala, S., Girshick, R. & Farhadi, A. (2016).** “You Only Look Once: Unified, Real-Time Object Detection.” *Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 779–788.  
DOI: [10.1109/CVPR.2016.91](https://doi.org/10.1109/CVPR.2016.91) · [Bản ghi chính thức CVF](https://openaccess.thecvf.com/content_cvpr_2016/html/Redmon_You_Only_Look_CVPR_2016_paper.html)  
**Loại nguồn:** Công trình phương pháp nền tảng về object detection.  
**Giá trị sử dụng:** Tham khảo khi giới thiệu họ phương pháp YOLO được cân nhắc cho phát hiện đối tượng/tình trạng nhìn thấy trong ảnh.  
**Giới hạn:** Không phải mô hình đã được huấn luyện/đánh giá trên ảnh UAV hoặc ảnh nhà máy của dự án; cần dữ liệu và kiểm định riêng.

### Đánh giá phân loại mất cân bằng và xác suất

**[11] He, H. & Garcia, E. A. (2009).** “Learning from Imbalanced Data.” *IEEE Transactions on Knowledge and Data Engineering*, 21(9), 1263–1284.  
DOI: [10.1109/TKDE.2008.239](https://doi.org/10.1109/TKDE.2008.239)  
**Loại nguồn:** Tổng quan/phương pháp về học từ dữ liệu mất cân bằng.  
**Giá trị sử dụng:** Biện minh cho việc không dựa riêng vào accuracy và báo cáo metric theo lớp; nếu xử lý mất cân bằng, mọi bước lấy mẫu/trọng số phải được đặt trong tập huấn luyện.  
**Giới hạn:** Không chứng minh kỹ thuật cân bằng cụ thể nào sẽ cải thiện kết quả trên bộ dữ liệu này.

**[12] Saito, T. & Rehmsmeier, M. (2015).** “The Precision-Recall Plot Is More Informative than the ROC Plot When Evaluating Binary Classifiers on Imbalanced Datasets.” *PLOS ONE*, 10(3), e0118432.  
DOI: [10.1371/journal.pone.0118432](https://doi.org/10.1371/journal.pone.0118432) · [Bài báo của nhà xuất bản](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0118432)  
**Loại nguồn:** Nghiên cứu phương pháp với mô phỏng và phân tích lại dữ liệu.  
**Giá trị sử dụng:** Hỗ trợ bổ sung precision-recall cho lớp thiểu số `low_bad`; với bài toán ba lớp, báo cáo từng lớp theo one-vs-rest và nêu rõ cách tổng hợp.  
**Giới hạn:** So sánh chính của bài báo tập trung vào phân loại nhị phân, không quy định cách tổng hợp tối ưu cho bài toán đa lớp này.

**[13] Guo, C., Pleiss, G., Sun, Y. & Weinberger, K. Q. (2017).** “On Calibration of Modern Neural Networks.” *Proceedings of the 34th International Conference on Machine Learning*, PMLR 70, 1321–1330.  
[Trang bài báo PMLR](https://proceedings.mlr.press/v70/guo17a.html)  
**Loại nguồn:** Nghiên cứu phương pháp về calibration.  
**Giá trị sử dụng:** Nếu giao diện hiển thị xác suất hoặc dùng xác suất để xếp hạng SP, đánh giá calibration riêng trên dữ liệu giữ lại; độ chính xác phân lớp không đồng nghĩa xác suất được hiệu chỉnh tốt.  
**Giới hạn:** Kết quả trên mạng nơ-ron và benchmark của bài báo không tự động chuyển sang mọi mô hình bảng hay quy trình này.

**[14] Gneiting, T. & Raftery, A. E. (2007).** “Strictly Proper Scoring Rules, Prediction, and Estimation.” *Journal of the American Statistical Association*, 102(477), 359–378.  
DOI: [10.1198/016214506000001437](https://doi.org/10.1198/016214506000001437)  
**Loại nguồn:** Tổng quan/phương pháp thống kê về scoring rule.  
**Giá trị sử dụng:** Cơ sở cho việc đánh giá xác suất bằng proper scoring rule như Brier score hoặc log loss, bên cạnh metric sau khi chọn lớp.  
**Giới hạn:** Không đặt ngưỡng hoặc hàm chi phí phù hợp riêng cho người vận hành của dự án.

### Kiểm định dữ liệu theo thời gian và cảm biến quy trình

**[15] Bergmeir, C. & Benítez, J. M. (2012).** “On the Use of Cross-Validation for Time Series Predictor Evaluation.” *Information Sciences*, 191, 192–213.  
DOI: [10.1016/j.ins.2011.12.028](https://doi.org/10.1016/j.ins.2011.12.028)  
**Loại nguồn:** Nghiên cứu phương pháp đánh giá mô hình chuỗi thời gian.  
**Giá trị sử dụng:** Hỗ trợ chọn chiến lược đánh giá phù hợp câu hỏi dự đoán; với tuyên bố về batch tương lai, cần xem xét holdout thời gian hoặc đánh giá cuốn chiếu thay vì mặc định chia ngẫu nhiên.  
**Giới hạn:** Kết luận phụ thuộc giả định và cấu trúc chuỗi thời gian; không thay thế yêu cầu giữ các bản ghi cùng batch trong cùng partition.

**[16] Tashman, L. J. (2000).** “Out-of-sample Tests of Forecasting Accuracy: An Analysis and Review.” *International Journal of Forecasting*, 16(4), 437–450.  
DOI: [10.1016/S0169-2070(00)00065-0](https://doi.org/10.1016/S0169-2070(00)00065-0)  
**Loại nguồn:** Tổng quan phương pháp kiểm định dự báo ngoài mẫu.  
**Giá trị sử dụng:** Hỗ trợ mô tả rõ giai đoạn kiểm tra và dùng đánh giá theo thời gian khi mục tiêu là dữ liệu sản xuất trong tương lai.  
**Giới hạn:** Bài báo tập trung vào đánh giá dự báo; cần kết hợp với group split để xử lý rò rỉ theo batch.

**[17] Kadlec, P., Gabrys, B. & Strandt, S. (2009).** “Data-driven Soft Sensors in the Process Industry.” *Computers & Chemical Engineering*, 33(4), 795–814.  
DOI: [10.1016/j.compchemeng.2008.12.012](https://doi.org/10.1016/j.compchemeng.2008.12.012)  
**Loại nguồn:** Tổng quan về soft sensor trong công nghiệp quy trình.  
**Giá trị sử dụng:** Hỗ trợ khảo sát việc dùng dữ liệu SP/PV theo cửa sổ thời gian để ước lượng trạng thái hoặc chỉ số không đo liên tục; yêu cầu ghi rõ thời điểm đo và khả năng sẵn có của biến.  
**Giới hạn:** Không xác nhận đơn vị, ý nghĩa tag hoặc một soft sensor cụ thể cho quy trình Vegemite.

### Prescriptive analytics và giới hạn suy luận nhân quả

**[18] Elmachtoub, A. N. & Grigas, P. (2022).** “Smart ‘Predict, then Optimize’.” *Management Science*, 68(1), 9–26.  
DOI: [10.1287/mnsc.2020.3922](https://doi.org/10.1287/mnsc.2020.3922)  
**Loại nguồn:** Nghiên cứu phương pháp prescriptive analytics.  
**Giá trị sử dụng:** Củng cố rằng mục tiêu quyết định và ràng buộc phải được xác định riêng; giảm lỗi dự đoán không đồng nghĩa tự động chọn được SP hữu ích.  
**Giới hạn:** Không chứng minh hiệu quả can thiệp SP trong nhà máy này và không cung cấp giới hạn vận hành an toàn.

**[19] Pearl, J. (2009).** “Causal Inference in Statistics: An Overview.” *Statistics Surveys*, 3, 96–146.  
DOI: [10.1214/09-SS057](https://doi.org/10.1214/09-SS057)  
**Loại nguồn:** Tổng quan học thuật về suy luận nhân quả.  
**Giá trị sử dụng:** Hỗ trợ phân biệt liên hệ dự đoán từ dữ liệu quan sát với kết luận rằng thay đổi SP gây ra thay đổi chất lượng; kết luận nhân quả đòi hỏi giả định và thiết kế xác nhận thích hợp.  
**Giới hạn:** Khung tổng quát, không phân tích yếu tố gây nhiễu cụ thể của quy trình dự án.

### Đánh giá bất thường theo thời gian và kiểm tra UAV

**[20] Hwang, W.-S., Yun, J.-H., Kim, J. & Kim, H. C. (2019).** “Time-Series Aware Precision and Recall for Anomaly Detection.” Bài báo trong kỷ yếu ACM, 2241–2244.  
DOI: [10.1145/3357384.3358118](https://doi.org/10.1145/3357384.3358118)  
**Loại nguồn:** Nghiên cứu phương pháp đánh giá phát hiện bất thường theo chuỗi thời gian.  
**Giá trị sử dụng:** Hỗ trợ đánh giá cảnh báo theo sự kiện/chuỗi thời gian thay vì xem từng timestamp độc lập, nhất là khi một sự kiện kéo dài qua nhiều quan sát.  
**Giới hạn:** Không xác định quy tắc ghép downtime hoặc horizon thích hợp cho dữ liệu Theme 3.

**[21] Lavin, A. & Ahmad, S. (2015).** “Evaluating Real-Time Anomaly Detection Algorithms—The Numenta Anomaly Benchmark.” *2015 IEEE 14th International Conference on Machine Learning and Applications (ICMLA)*, 38–44.  
DOI: [10.1109/ICMLA.2015.141](https://doi.org/10.1109/ICMLA.2015.141)  
**Loại nguồn:** Bài báo benchmark/phương pháp đánh giá anomaly detection trực tuyến.  
**Giá trị sử dụng:** Nhấn mạnh tính kịp thời và cảnh báo sai khi đánh giá cảnh báo streaming; gợi ý báo missed events, false alerts và warning time khi có timestamp sự kiện đáng tin cậy.  
**Giới hạn:** Benchmark không phải nghiên cứu downtime sản xuất; không áp dụng máy móc scoring rule nếu chưa phù hợp yêu cầu vận hành.

**[22] Morgenthal, G. & Hallermann, N. (2014).** “Quality Assessment of Unmanned Aerial Vehicle (UAV) Based Visual Inspection of Structures.” *Advances in Structural Engineering*, 17(3), 289–302.  
DOI: [10.1260/1369-4332.17.3.289](https://doi.org/10.1260/1369-4332.17.3.289)  
**Loại nguồn:** Nghiên cứu đánh giá kiểm tra trực quan bằng UAV.  
**Giá trị sử dụng:** Hỗ trợ ghi nhận chất lượng thu nhận ảnh và điều kiện góc nhìn, khoảng cách, ánh sáng, chuyển động trước khi đánh giá mô hình thị giác.  
**Giới hạn:** Nghiên cứu trên kết cấu dân dụng, không xác nhận các nhãn hoặc điều kiện hình ảnh của dây chuyền thực phẩm.

## 9. Phụ lục tài liệu bổ sung [23]–[47]

Phụ lục này bổ sung các nguồn trực tiếp hỗ trợ kiểm định theo batch/thời gian, calibration, lớp thiểu số, batch-process control, predictive maintenance và false alarms. Các nguồn chỉ được dùng như căn cứ phương pháp hoặc khung đánh giá; không chuyển thành evidence về giới hạn vận hành Vegemite.

### Kiểm định thời gian, batch và rò rỉ dữ liệu

**[23] Roberts, D. R. et al. (2017).** “Cross-validation strategies for data with temporal, spatial, hierarchical or phylogenetic structure.” *Ecography*, 40(8), 913–929.  
DOI: [10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881)  
**Giá trị sử dụng:** Cổ vũ kiểm định phải tách theo cấu trúc phụ thuộc, không rời rạc từng dòng. Áp dụng cho batch: giữ trọn batch trong một partition và kiểm tra trượt theo thời gian.

**[24] Arlot, S. & Celisse, A. (2010).** “A survey of cross-validation procedures for model selection.” *Statistics Surveys*, 4, 40–79.  
DOI: [10.1214/09-SS054](https://doi.org/10.1214/09-SS054)  
**Giá trị sử dụng:** Giải thích trade-off giữa ước lượng hiệu năng, model selection và cross-validation; cần tách rõ calibration/threshold từ test.

**[25] Meiners, M., Mayr, A., Thomsen, M. & Franke, J. (2020).** “Application of Machine Learning for Product Batch Oriented Control of Production Processes.” *Procedia CIRP*, 93, 431–436.  
DOI: [10.1016/j.procir.2020.04.006](https://doi.org/10.1016/j.procir.2020.04.006)  
**Giá trị sử dụng:** Hỗ trợ mô hình batch-oriented hai giai đoạn và việc xem xét tương tác giữa bán thành phẩm, thiết bị và tham số quy trình.

**[26] Witt, C., Bux, M., Gusew, W. & Leser, U. (2019).** “Predictive performance modeling for distributed batch processing using black box monitoring and machine learning.” *Information Systems*, 82, 33–52.  
DOI: [10.1016/j.is.2019.01.006](https://doi.org/10.1016/j.is.2019.01.006)  
**Giá trị sử dụng:** Minh họa dự đoán theo batch bằng giám sát black-box và biến tình trạng hệ thống; hỗ trợ requirements provenance và không trộn quan sát rò rỉ.

**[27] Hespeler, S. C., Moriano, P., Li, M. & Hollifield, S. C. (2025).** “Temporal cross-validation impacts multivariate time series subsequence anomaly detection evaluation.” Preprint.  
DOI: [10.48550/arXiv.2506.12183](https://doi.org/10.48550/arXiv.2506.12183)  
**Giá trị sử dụng:** Cảnh báo rằng thiết kế temporal partition ảnh hưởng lớn tới precision-recall anomaly detection. Chỉ xem là nguồn gần, vì chưa có DOI peer-review chính thức trong record hiện tại.

### Mất cân bằng lớp và cost-sensitive learning

**[28] Chawla, N. V., Bowyer, K. W., Hall, L. O. & Kegelmeyer, W. P. (2002).** “SMOTE: Synthetic Minority Over-sampling Technique.” *Journal of Artificial Intelligence Research*, 16, 321–357.  
DOI: [10.1613/jair.953](https://doi.org/10.1613/jair.953)  
**Giá trị sử dụng:** Nền tảng oversampling thiểu số; mọi SMOTE/biến thể phải fit trên train/OOF, không fit trước trước split.

**[29] Fernández, A., García, S., Galar, M., Prati, R. C., Krawczyk, B. & Herrera, F. (2018).** *Learning from Imbalanced Data Sets.* Springer.  
DOI: [10.1007/978-3-319-98074-4](https://doi.org/10.1007/978-3-319-98074-4)  
**Giá trị sử dụng:** Hệ thống hóa resampling, cost-sensitive learning, metric và extreme imbalance; không tự động chọn được ngưỡng vận hành.

**[30] Buda, M., Maki, A. & Mazurowski, M. A. (2018).** “A systematic study of the class imbalance problem in convolutional neural networks.” *Pattern Recognition Letters*, 106, 38–45.  
DOI: [10.1016/j.patrec.2018.07.011](https://doi.org/10.1016/j.patrec.2018.07.011)  
**Giá trị sử dụng:** Cổ vũ đánh giá các chiến lược mất cân bằng theo bài toán thực tế và kiểm tra xem cải thiện recall có đổi false-positive hay không.

**[31] Elkan, C. (2001).** “The Foundations of Cost-Sensitive Learning.” *IJCAI-01*, 973–978.  
Persistent record: [https://dl.acm.org/doi/10.5555/645530.658061](https://dl.acm.org/doi/10.5555/645530.658061)  
**Giá trị sử dụng:** Cơ sở để biến chi phí miss/false alarm thành threshold hoặc class weights thay vì cố định threshold 0.5.

**[32] Billion-Polak, P., Prusa, J. D. & Khoshgoftaar, T. M. (2024).** “Low-shot learning and class imbalance: a survey.” *Journal of Big Data*, 11, 1.  
DOI: [10.1186/s40537-023-00851-z](https://doi.org/10.1186/s40537-023-00851-z)  
**Giá trị sử dụng:** Hỗ trợ chiến lược cho lớp hiếm và low-shot; cho thấy cần báo cáo uncertainty/coverage thay vì tuyên bố hiệu năng chung.

**[33] Jiang, J. et al. (2025).** “A review of machine learning methods for imbalanced data challenges in chemistry.” *Chemical Science*, 16, 7637–7658.  
DOI: [10.1039/D5SC00270B](https://doi.org/10.1039/d5sc00270b)  
**Giá trị sử dụng:** Tổng quan phương pháp imbalance trong quy trình khoa học dữ liệu; quan trọng khi số lớp thiểu số nhỏ và risk of overfitting cao.

### Calibration, ngưỡng và false alarms

**[34] Niculescu-Mizil, A. & Caruana, R. (2005).** “Predicting good probabilities with supervised learning.” *ICML*, 625–632.  
Persistent record: [10.1145/1102351.1102430](https://doi.org/10.1145/1102351.1102430)  
**Giá trị sử dụng:** Cơ sở so sánh calibration của nhiều họ mô hình và post-hoc calibration.

**[35] Zadrozny, B. & Elkan, C. (2002).** “Transforming classifier scores into accurate multiclass probability estimates.” *ICML*, 694–701.  
Persistent record: [10.1145/775047.775151](https://doi.org/10.1145/775047.775151)  
**Giá trị sử dụng:** Hỗ trợ chuyển điểm phân loại thành xác suất đa lớp phục vụ ranking và uncertainty.

**[36] Leathart, T. & Polaczuk, M. (2020).** “Temporal Probability Calibration.” Preprint.  
DOI: [10.48550/arXiv.2002.02644](https://doi.org/10.48550/arXiv.2002.02644)  
**Giá trị sử dụng:** Gợi ý rằng calibration có thể phụ thuộc độ dài chuỗi hoặc tình trạng temporal; cần dùng calibration fold/OOF rồi mở test một lần.

**[37] De Santis, E., Arnò, F. & Rizzi, A. (2022).** “Estimation of fault probability in medium voltage feeders through calibration techniques in classification models.” *Soft Computing*, 26(15), 7175–7193.  
DOI: [10.1007/s00500-022-07194-6](https://doi.org/10.1007/s00500-022-07194-6)  
**Giá trị sử dụng:** Ví dụ calibration tăng độ tin cậy xác suất cảnh báo thiết bị và hỗ trợ risk-based assessment.

**[38] Luche, J. R. D., Goussain, B. G. C. dos Santos & Freitas, C. R. de (2026).** “Robust Baselines and Probability Calibration for TPM-Oriented Predictive Maintenance.” *International Journal of Prognostics and Health Management*, 17(1).  
DOI: [10.36001/ijphm.2026.v17i1.4659](https://doi.org/10.36001/ijphm.2026.v17i1.4659)  
**Giá trị sử dụng:** Minh họa baseline RF/MLP, nested CV, SMOTE và calibration; cần xem đây là công trình mới và chưa có lịch sử trích dẫn lâu dài.

### Batch-process monitoring và predictive maintenance

**[40] Qin, S. J. (2003).** “Statistical process monitoring: basics and beyond.” *Journal of Chemometrics*, 17(8–9), 480–502.  
DOI: [10.1002/cem.800](https://doi.org/10.1002/cem.800)  
**Giá trị sử dụng:** Nền tảng statistical process monitoring, latent variables và baseline fault detection; cần phân biệt monitoring với supervised quality prediction.

**[41] Kadlec, P., Gabrys, B. & Strandt, S. (2009)** ở nguồn [17] là nền tảng cho soft sensor trong quy trình công nghiệp. Kết luận cần ghi rõ latency, missing data, update cycle và availability-at-prediction.

**[42] Kang, Z., Catal, C. & Tekinerdogan, B. (2020).** “Machine learning applications in production lines: A systematic literature review.” *Computers & Industrial Engineering*, 149, 106773.  
DOI: [10.1016/j.cie.2020.106773](https://doi.org/10.1016/j.cie.2020.106773)  
**Giá trị sử dụng:** Tổng hợp ứng dụng ML trên dây chuyền, quality, risk, cost và dữ liệu; giúp lập backlog evaluation/bài toán.

**[43] Sankhye, S. & Hu, G. (2020).** “Machine Learning Methods for Quality Prediction in Production.” *Logistics*, 4(4), 35.  
DOI: [10.3390/logistics4040035](https://doi.org/10.3390/logistics4040035)  
**Giá trị sử dụng:** Ví dụ dự đoán conformity theo batch và feature construction; không chứng minh cơ chế nhân quả hoặc SP hợp lệ.

**[45] Saha, S. S., Sandha, S. S. & Srivastava, M. B. (2022).** “Machine Learning for Microcontroller-Class Hardware: A Review.” *IEEE Sensors Journal*, 22(22), 21362–21390.  
DOI: [10.1109/JSEN.2022.3210773](https://doi.org/10.1109/JSEN.2022.3210773)  
**Giá trị sử dụng:** Hỗ trợ đánh giá độ trễ, bộ nhớ, energy và deployment constraints nếu demonstrator chạy trên edge device; không liên quan đến tính an toàn SP.

### Cận quan sát nhân quả và setpoint recommendation

**[46] Künzel, S. R., Sekhon, J. S., Bickel, P. J. & Yu, B. (2019).** “Metalearners for estimating heterogeneous treatment effects using machine learning.” *PNAS*, 116(10), 4156–4165.  
DOI: [10.1073/pnas.1804597117](https://doi.org/10.1073/pnas.1804597117)  
**Giá trị sử dụng:** Tạo nền tảng phương pháp cho heterogeneous treatment effects; nếu có dữ liệu can thiệp SP/controlled trial, phải dùng bài toán causal riêng thay vì rank SP theo classifier.

**[47] Athey, S. & Wager, S. (2019).** “Estimating treatment effects with causal forests: An application.” *Observational Studies*, 5(2), 37–51.  
DOI: [10.1214/18-AOS1709](https://doi.org/10.1214/18-AOS1709)  
**Giá trị sử dụng:** Nêu cách đánh giá treatment effect từ dữ liệu quan sát/causal forest; yêu cầu giả định overlap, no unmeasured confounding và validation theo can thiệp.

## 10. Nguồn bổ sung về lựa chọn mô hình tabular [48]–[57]

**[48] Chen, T. & Guestrin, C. (2016).** “XGBoost: A Scalable Tree Boosting System.” *Proceedings of KDD*, 785–794.  
DOI: [10.1145/2939672.2939785](https://doi.org/10.1145/2939672.2939785)  
**Giá trị sử dụng:** Cơ sở kỹ thuật cho gradient boosting có regularization, missing-value handling và scalable split; cần tune cost-sensitive weight/calibration theo batch/time ở dự án này.

**[49] Ke, G. et al. (2017).** “LightGBM: A Highly Efficient Gradient Boosting Decision Tree.” *NeurIPS*, 3146–3154.  
Persistent record: [https://proceedings.neurips.cc/paper/6907](https://proceedings.neurips.cc/paper/6907)  
**Giá trị sử dụng:** Ứng viên leaf-wise gradient boosting cho dữ liệu bảng và feature đa dạng; tốc độ không thay requirement về temporal/batch validation.

**[50] Prokhorenkova, L. et al. (2018).** “CatBoost: unbiased boosting with categorical features.” *NeurIPS*, 6638–6648.  
Persistent record: [arXiv:1706.09516](https://arxiv.org/abs/1706.09516)  
**Giá trị sử dụng:** Ứng viên cho ordered boosting và ordered target encoding; sensor/metadata ở đây chủ yếu số, nên lợi thế biến phân loại cần được kiểm tra local thay vì suy diễn.

**[51] Erickson, N. et. al. (2025).** “TabArena: A Living Benchmark for Machine Learning on Tabular Data.” *NeurIPS Datasets and Benchmarks*.  
DOI/Persistent record: [https://openreview.net/forum?id=2gaiIurY1G](https://openreview.net/forum?id=2gaiIurY1G)  
**Giá trị sử dụng:** Hỗ trợ xem gradient-boosted trees và GBDT vẫn mạnh trong benchmark tabular, còn deep/foundation models có thể catch up dưới tuning dài; kết quả benchmark ngoài không thay model selection trên Vegemite.

**[52] Gardner, J. R. et al. (2024).** “Benchmarking distribution shift on tabular datasets.” *TableShift*.  
Persistent record: [https://arxiv.org/abs/2311.00187](https://arxiv.org/abs/2311.00187)  
**Giá trị sử dụng:** Nhấn mạnh đánh giá distribution shift, batch/time shift và subgroup robustness thay vì chỉ random holdout.

**[53] Hollmann, N. et al. (2025).** “Accurate predictions on small tabular datasets with TabPFN.” *Nature*, 637, 319–326.  
DOI: [10.1038/s41586-024-08328-6](https://doi.org/10.1038/s41586-024-08328-6)  
**Giá trị sử dụng:** Nguồn foundation model cho dữ liệu tabular nhỏ; phải kiểm tra giới hạn kích thước training data và tốc độ inference trước khi xem là candidate cho ~26k dòng.

**[54] Qu, H. et al. (2025).** “TabICL: A Tabular Foundation Model for In-context Learning on Large Data.”  
DOI/Persistent record: [10.48550/arXiv.2502.05564](https://doi.org/10.48550/arXiv.2502.05564)  
**Giá trị sử dụng:** Cung cấp khả năng ứng viên cho tabular foundation model ở quy mô lớn; benchmark local vẫn bắt buộc vì nhỏ/lớn được xử lý khác nhau qua implementation.

**[55] Shmuel, A., Glickman, O. & Lazebnik, T. (2024).** “A comprehensive benchmark of machine learning and deep learning models for tabular data.” *Neurocomputing*, 610, 128547.  
DOI/Persistent record: [10.1016/j.neucom.2024.128547](https://doi.org/10.1016/j.neucom.2024.128547)  
**Giá trị sử dụng:** Nhấn mạnh không có họ mô hình luôn thắng; cần baseline gradient boosting và tree ensembles trước khi đầu tư deep tabular models.

**[56] Grinsztajn, L., Oyallon, E. & Varoquaux, G. (2022).** “Why do tree-based models still outperform deep learning on tabular data?” *NeurIPS 2022 Datasets and Benchmarks*.  
DOI/Persistent record: [10.48550/arXiv.2207.08815](https://doi.org/10.48550/arXiv.2207.08815)  
**Giá trị sử dụng:** Giải thích vì sao tree-based models thường vượt deep/tabular networks trên dữ liệu heterogeneity nhưng vẫn có exception; hỗ trợ giữ RF/gradient boosting làm local benchmark trước.

**[57] Davis, J. & Goadrich, M. (2006).** “The relationship between Precision-Recall and ROC curves.” *ICML*, 233–240.  
DOI/Persistent record: [10.1145/1143844.1143874](https://doi.org/10.1145/1143844.1143874)  
**Giá trị sử dụng:** Căn cứ dùng Precision-Recall AUC cho lớp thiểu số thay vì chỉ AUROC/accuracy; hỗ trợ đánh giá `low_bad` và false alarms.

## 11. Cách dùng bộ nguồn mở rộng

1. Dùng [23]–[27] để thiết kế split theo batch và thời gian; không dùng random row split làm bằng chứng dự đoán tương lai.
2. Dùng [28]–[33] để xử lý `low_bad` dưới loss/miss cost, nhưng calibration, class weight và sampling phải nằm trong validation folds.
3. Dùng [34]–[38] để chọn calibration và threshold bằng dữ liệu validation; không khóa test cho đến khi protocol freeze.
4. Dùng [40]–[45] để định nghĩa batch monitoring, downtime events, equipment mapping, horizon, lead time và false-alert metric.
5. Dùng [46]–[47] để phân biệt causal SP recommendation khỏi quality prediction; dữ liệu quan sát hiện tại không đủ tự động chứng minh tác động nhân quả.
6. Mọi recommendation vẫn bị chặn bởi operating bounds chưa được xác nhận. Nguồn học thuật không thay P&ID, PLC/DCS limit, operating procedure hoặc sign-off của process expert.
