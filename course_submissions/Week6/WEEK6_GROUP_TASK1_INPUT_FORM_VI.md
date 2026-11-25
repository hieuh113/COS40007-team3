# TÀI LIỆU KẾ HOẠCH NHÓM — WEEK 6 GROUP TASK 1

Tài liệu này tổng hợp thông tin phân công công việc, thỏa thuận nhóm, kế hoạch Sprint, kiến trúc hệ thống và thiết kế MLOps/DevOps cho bài nộp **Applied Project Task 1: System Blueprint & Project Planning**.

---

## A. Thông tin bài nộp

- **Tên bài:** Applied Project Task 1: System Blueprint & Project Planning
- **Học phần:** COS40007 Artificial Intelligence Engineering
- **Studio session:** COS40007 Studio
- **Group number (do tutor cấp):** Team 3
- **Tên nhóm/dự án:** AI-Assisted Quality Monitoring and Setpoint Recommendation for Vegemite Production
- **Ngày nộp theo Canvas:** 25 October, 23:59
- **Ngôn ngữ báo cáo:** Tiếng Anh / Tiếng Việt (tài liệu nội bộ nhóm)
- **Tên GitHub Group repository chính xác:** `COS40007-team3`
- **Link repository:** https://github.com/hieuh113/COS40007-team3

## B. Thành viên, vai trò và đóng góp

Thêm hoặc xóa dòng theo số thành viên. Ghi rõ mỗi người phụ trách deliverable nào; vai trò có thể kết hợp nếu nhóm nhỏ.

| Thành viên | Student ID | Vai trò chính | Nhiệm vụ/deliverable phụ trách | Scrum Master sprint nào? |
|---|---|---|---|---|
| Nguyễn Huy Hoàng Việt | 10499509 | Data / ML Engineer | Week 6: soạn phần Group Agreement/Sprint Plan cùng nhóm và mô tả luồng dữ liệu/model. Project: kiểm kê/gán nhãn, preprocessing, baseline chất lượng, batch/time split và review code | Sprint 1 |
| Huỳnh Quốc Hiếu | 104848408 | ML / Evaluation & Project Coordinator | Week 6: setup Jira/Trello, user stories/backlog và hợp nhất PDF. Project: kiểm tra downtime, đánh giá downtime/anomaly nếu dữ liệu cho phép, metrics và điều phối nộp | Sprint 2 |
| Vũ Bá Hiển | 104995634 | Technical Lead / Software & Deployment Design | Week 6: dẫn dắt System Blueprint Diagram và MLOps/DevOps design. Project: thiết kế kiến trúc/phần mềm, demonstrator/deployment và review tích hợp | Sprint 3 |

- **Người đại diện nhóm trao đổi/đặt câu hỏi với tutor:** Vũ Bá Hiển
- **Người chịu trách nhiệm hợp nhất và nộp PDF:** Huỳnh Quốc Hiếu
- **Người quản lý GitHub repository:** Huỳnh Quốc Hiếu; cả ba thành viên cùng đóng góp qua branch/commit và review.
- **Nguyên tắc phân chia công việc để bảo đảm đóng góp cân bằng:** Mỗi người sở hữu một work package có effort mục tiêu xấp xỉ 1/3 tổng khối lượng. Hiển dẫn dắt thiết kế phần mềm/deploy và hỗ trợ kỹ thuật, nhưng không thay thế phần code, kiểm định hoặc tài liệu do Việt và Hiếu phụ trách.
- **Tỷ lệ đóng góp dự kiến (cần đối chiếu với công việc thực tế):** Nguyễn Huy Hoàng Việt ~33%; Huỳnh Quốc Hiếu ~33%; Vũ Bá Hiển ~34%.
- **Review chéo:** Việt review downtime/evaluation của Hiếu; Hiếu review dữ liệu/model của Việt; Hiển review kiến trúc và tích hợp; cả nhóm duyệt bản cuối.

### Đóng góp cá nhân của thành viên

- **Tên và Student ID:** Nguyễn Huy Hoàng Việt — 10499509
- **Phần việc thực hiện:** Kiểm toán dữ liệu nguồn, xây dựng từ điển dữ liệu, thiết kế pipeline tiền xử lý theo batch/thời gian, huấn luyện mô hình phân loại chất lượng và hiệu chỉnh xác suất.
- **Bằng chứng thực hiện:** Script tiền xử lý, báo cáo kiểm toán dữ liệu, kết quả baseline/tuning và đóng góp mã nguồn trên GitHub repository nhóm.
- **Tỷ lệ đóng góp thống nhất:** 33% (nhóm thống nhất phân bổ cân bằng giữa ba thành viên)

## C. Group Agreement

- **Cách nhóm làm việc và ra quyết định:** Reasearch - Họp - Chốt kế hoạch - Kiểm tra kết quả mỗi cuối tuần
- **Tần suất/thời lượng họp:** 1h-1h30p
- **Kênh liên lạc chính:** Messenger
- **Nơi lưu tài liệu dùng chung/bản chính thức:** GitHub Group Repository (tạo thư mục `docs/` để lưu báo cáo, blueprint và tài liệu dự án; repo URL cần bổ sung khi nhóm tạo/xác nhận repository)
- **Thời gian phản hồi tin nhắn dự kiến:** 1h
- **Quy tắc báo sớm khi không hoàn thành task:** Cần thông báo delay bao lâu
- **Hành vi giúp nhóm làm việc hiệu quả (on-track):** Luôn hoàn thành task được giao, nếu có delay phải báo trước
- **Hành vi không được chấp nhận (off-track):** Không trả lời tin nhắn
- **Cách xử lý khi có bất đồng/trễ hạn:** Trao đổi nội bộ, báo cáo lên Supervisor
- **Kỳ vọng chung của nhóm:** 
  1. Hoàn thành các yêu cầu tối thiểu của Project.
  2. Làm việc hiệu quả, kỉ luật.
  3. Thẳng thắn nêu vấn đều để cả nhóm trao đổi, giải quyết.

## D. Sprint Plan và timeline

Mốc nội bộ nên sớm hơn hạn Canvas để có thời gian review và sửa. Điều chỉnh sprint theo lịch học thật của nhóm.

| Sprint / thời gian | Mục tiêu | Công việc chính | Người phụ trách | Deliverable / điều kiện hoàn tất |
|---|---|---|---|---|
| Sprint 1 — From week 5-7 | Chốt scope và nền tảng | Việt kiểm kê schema/nhãn; Hiếu tạo board/user stories; Hiển thống nhất kiến trúc, repo và coding workflow | Việt (Scrum Master); cả nhóm làm | Data dictionary bản đầu, backlog có người phụ trách/ưu tiên, blueprint nháp |
| Sprint 2 — From week 3-7 | Chuẩn bị dữ liệu và mô hình | Việt xử lý dữ liệu/trùng/nhãn và baseline quality; Hiếu đánh giá downtime/anomaly; Hiển review kiến trúc và hỗ trợ tích hợp code | Hiếu (Scrum Master); từng người sở hữu task | Pipeline dữ liệu, baseline, báo cáo tính khả thi downtime |
| Sprint 3 — From Week 7 to 11 | Tích hợp demonstrator và MLOps | Hiển dẫn dắt phần mềm/blueprint/deployment; Việt kiểm thử data/model flow; Hiếu hoàn thiện metrics, monitoring/retraining và backlog | Hiển (Scrum Master); cả nhóm tích hợp | Blueprint cuối, luồng demonstrator, thiết kế MLOps/DevOps và test checklist |
| Sprint 4 — From week 11 - 12 | Hoàn thiện và nộp | Việt xác minh số liệu/kết quả; Hiếu hợp nhất báo cáo và nộp; Hiển review kỹ thuật/GitHub; cả nhóm proofreading | Hiếu (Scrum Master); cả nhóm review | PDF cuối, link/ảnh board và docs, tài liệu đã đưa vào Group GitHub repository |

- **Hạn hoàn thành bản nháp nội bộ:** Week 7
- **Hạn review chéo:** Week 7
- **Hạn nộp nội bộ (trước Canvas):** Trước 3 ngày
- **Khoảng dự phòng nếu có lỗi:** 2 Ngày

## E. System Blueprint Diagram

### Nội dung kiến trúc đã điền sẵn từ dự án

Luồng cốt lõi đề xuất:

**Nguồn dữ liệu Theme3**
(CSV chất lượng `good`/`low_bad`/`high_bad`, SP/PV, `VYP batch`, `Part`, `Set Time`; downtime log)
→ **Data ingestion và audit**
→ **Preprocessing/labeling**
(xác minh nhãn, missing/duplicate, timestamp, liên kết batch và thiết bị)
→ **Feature engineering**
(SP/PV và đặc trưng quy trình sẵn có tại thời điểm dự đoán)
→ **Các nhánh mô hình**
(quality classifier; downtime classifier nếu nhãn/event đủ tin cậy; nếu không thì anomaly analysis riêng)
→ **Decision layer**
(xếp hạng SP ứng viên trong giới hạn vận hành được xác nhận; không tự điều khiển)
→ **Demonstrator/UI**
(quality estimate, SP ranking, downtime/anomaly, bằng chứng và trạng thái không đủ dữ liệu)
→ **Human review**.

**Lưu ý dữ liệu đã biết:** workspace có dữ liệu chất lượng, downtime, Infinity và trend; chưa thấy ảnh/video UAV. Không đưa UAV vào luồng cốt lõi trừ khi nhóm xác nhận có nguồn ảnh hợp lệ. Không đưa UAV vào vì chưa xác định hướng đi cho UAV, chỉ nêu optional

### Nhóm cần xác nhận/điền

- **Công cụ vẽ sơ đồ:** Lucidchart
- **Người vẽ/điều phối thiết kế:** Vũ Bá Hiển; Nguyễn Huy Hoàng Việt kiểm tra data/model flow; Huỳnh Quốc Hiếu kiểm tra sự khớp với backlog và yêu cầu bài.
- **Link hoặc tên file sơ đồ:** (https://lucid.app/lucidchart/d97fba93-9cd5-4e5a-98de-a0739dc4d9a0/edit?viewport_loc=888%2C-271%2C3338%2C1773%2C0_0&invitationId=inv_0746e7dc-96ae-4aae-ad8a-0f6f6c871547)

> Yêu cầu: sơ đồ tối đa 1 trang; thể hiện data source, ingestion, preprocessing, feature engineering, ML, output/UI, mũi tên luồng dữ liệu và sprint liên quan.

## F. MLOps & DevOps Design

### Đề xuất có thể dùng làm mặc định — cần nhóm xác nhận

- **Chia dữ liệu:** Giữ các bản ghi cùng batch trong cùng partition; dùng holdout theo thời gian nếu mục tiêu là mô phỏng dự đoán batch tương lai. Tách train/validation/test; không để test tham gia chọn mô hình.
- **Retraining:** Đây là prototype học thuật trên dữ liệu lịch sử. Chưa tự động retrain trong vận hành; retrain khi có batch mới đã được xác minh/gán nhãn, theo lịch review hoặc khi metric/drift vượt ngưỡng được nhóm xác định.
- **Model monitoring:** Theo dõi chất lượng dữ liệu, missing values, phân bố SP/PV/Part và metric theo lớp khi có nhãn thực tế mới.
- **Data drift:** Phân bố đầu vào (SP/PV/Part) thay đổi so với dữ liệu train.
- **Concept drift:** Quan hệ giữa đầu vào quy trình và lớp chất lượng thay đổi; cần nhãn mới để phát hiện đáng tin cậy.
- **CI/CD:** Dùng GitHub và đề xuất GitHub Actions để chạy kiểm tra mã/test khi có pull request; chỉ đóng gói/phát hành khi người phụ trách review. Đây là thiết kế khái niệm, chưa cần triển khai trong task này.
- **Versioning:** Git cho source code; gắn version cho dataset manifest, preprocessing config, model/checkpoint và kết quả đánh giá. Không đẩy dữ liệu sản xuất nhạy cảm lên repository nếu chưa được phép.
- **Human approval:** Không tự thay thế model hoặc dùng SP mới để điều khiển máy; cần đánh giá holdout và phê duyệt của nhóm/chuyên gia.

### Nhóm xác nhận/điều chỉnh

- **Phân công MLOps/DevOps:** Hiếu soạn monitoring, drift và retraining triggers; Hiển soạn Git/GitHub, CI/CD concept, versioning và deployment/release approval; Việt kiểm tra availability của dữ liệu/nhãn và khả năng đo performance. Cả nhóm review để khớp với blueprint.
- **Cách chia dữ liệu được nhóm chọn:** Chia theo thời gian và giữ nguyên batch trong cùng một tập. Dùng các batch cũ hơn cho train, giai đoạn tiếp theo cho validation và giai đoạn mới nhất cho test; không để test tham gia chọn mô hình. Fit các bước tiền xử lý chỉ trên train. Tỷ lệ chia sẽ được chốt sau khi kiểm tra số batch và phân bố nhãn.

- **Nguồn dữ liệu mới có thể dùng để retrain:** Các batch sản xuất mới được phép sử dụng, có nhãn chất lượng đã xác minh và có đủ SP, PV, `Part`, `VYP batch` và timestamp. Với downtime, chỉ dùng log sự kiện đã xác minh loại sự kiện, thời gian và thiết bị liên quan. Không dùng dữ liệu test làm dữ liệu huấn luyện.

- **Trigger retrain:** Không tự động retrain trong prototype. Xem xét retrain khi có batch mới đã được xác minh/gán nhãn, hoặc monitoring cho thấy drift hay hiệu năng giảm ổn định trên dữ liệu mới có nhãn. Mô hình mới phải được đánh giá trên holdout trước khi được chấp thuận thay thế.

- **Metric theo dõi và ngưỡng cảnh báo:** Theo dõi missing values/schema và phân bố SP/PV/Part; khi có nhãn mới, theo dõi macro-F1, balanced accuracy, recall từng lớp (đặc biệt `low_bad`) và calibration nếu sử dụng xác suất. Chưa đặt ngưỡng số trước khi có baseline; xác định ngưỡng sau baseline và báo động khi metric giảm đáng kể qua các lần đánh giá liên tiếp. Với downtime, theo dõi event recall và false alarms nếu log đủ tin cậy.

- **Tần suất review monitoring:** Kiểm tra khi mỗi batch mới được xác minh/gán nhãn và tổng hợp định kỳ mỗi tháng trong giai đoạn phát triển. Đây là lịch review đề xuất cho prototype, không phải cam kết giám sát thời gian thực.

- **GitHub branch/review strategy:** Dùng `main` cho phiên bản ổn định; mỗi task làm trên branch riêng, ví dụ `feature/data-audit` hoặc `feature/quality-model`, rồi mở pull request vào `main`. Yêu cầu ít nhất một thành viên khác review trước khi merge. Không đưa dữ liệu sản xuất hoặc thông tin bí mật lên repository nếu chưa được phép.

- **GitHub Actions sẽ kiểm tra gì:** Khi có pull request, chạy kiểm tra format/lint, unit tests và kiểm tra schema/pipeline trên dữ liệu mẫu hoặc dữ liệu tổng hợp được phép sử dụng. Chưa cần tự động train hay deploy mô hình trong task này.

- **Ai phê duyệt model/release:** Việt kiểm tra dữ liệu, nhãn và kết quả mô hình; Hiếu kiểm tra metric, đánh giá downtime/anomaly và tài liệu; Hiển review kiến trúc, tích hợp phần mềm và thiết kế phát hành. Cả nhóm thống nhất trước khi merge/release; mọi giới hạn SP dùng cho khuyến nghị vận hành cần được người có thẩm quyền xác nhận.

> Phần MLOps/DevOps trong báo cáo tối đa 4 trang theo Studio handout; trình bày ở mức thiết kế, không cần triển khai CI/CD thật cho bài này.

## G. Project Management Setup (Agile tools)

- **Công cụ nhóm sử dụng:** Jira; Huỳnh Quốc Hiếu setup ban đầu, cả nhóm tự cập nhật task được giao.
- **Tên project/board:** https://cos4007.atlassian.net/jira/software/projects/SCRUM/boards/1?filter=&groupBy=none&atlOrigin=eyJpIjoiMjViN2ZmYTkwNGU3NDFhN2JlMzUzNzkxYmZmMjA0Y2IiLCJwIjoiaiJ9)
- **Nơi lưu project documentation:** GitHub Group Repository, thư mục `docs/`
- **Link repository:** https://github.com/hieuh113/COS40007-team3


### User stories:

1. As an **operator**, I want to see the predicted quality class from current SP/PV values so that I can understand the likely product consistency.
2. As an **operator/process engineer**, I want to compare candidate SP settings within approved limits so that I can review settings associated with the desired quality.
3. As a **maintenance engineer**, I want to see downtime-related alerts or clearly separated anomaly scores so that I can investigate potential process issues.
4. As a **project evaluator**, I want to inspect model metrics on held-out batches/time periods so that I can assess whether the reported performance is credible.

### Backlog và task breakdown

| User story / Epic | Task | Ưu tiên | Người phụ trách | Sprint | Trạng thái |
|---|---|---|---|---|---|
| Data preparation / quality model | Audit nhãn, xử lý/cách ly xung đột, preprocessing và baseline | High | Nguyễn Huy Hoàng Việt | Sprint 1–2 | Đang làm |
| Downtime/anomaly and evaluation | Kiểm tra event readiness, thiết kế metric; triển khai nhánh phù hợp nếu đủ dữ liệu | High | Huỳnh Quốc Hiếu | Sprint 2 | Đang làm |
| System blueprint / demonstrator | Vẽ kiến trúc, xác định tích hợp UI/software và deployment design | High | Vũ Bá Hiển | Sprint 1–3 | Đang làm |
| MLOps, board and DevOps | Monitoring/retraining (Hiếu); GitHub/CI/CD/versioning (Hiển); kiểm tra dữ liệu (Việt) | High | Hiếu + Hiển + Việt | Sprint 1–3 | Đang làm |
| Final report / QA | Kiểm tra kết quả (Việt), hợp nhất và nộp (Hiếu), review kỹ thuật (Hiển) | High | Cả nhóm; Hiếu tích hợp | Sprint 4 | Đang làm |

> Rubric đánh giá chất lượng project management qua user stories rõ ràng, backlog, task breakdown, người phụ trách, ưu tiên và việc sử dụng board thực tế. 

## H. Acknowledgement of Country

Nhóm ghi nhận và tôn trọng các Chủ sở hữu Truyền thống (Traditional Owners) và Cộng đồng Bản địa (First Nations Peoples — Wurundjeri Woi Wurrung people of the Kulin Nation đối với cơ sở Swinburne Hawthorn) tại các địa điểm đào tạo và hợp tác của chương trình học.

- **Địa điểm học tập:** Việt Nam (Swinburne Vietnam Alliance Program)
- **Nội dung ghi nhận:** Nhóm tuân thủ quy chuẩn Acknowledgement of Country theo hướng dẫn chính thức của Swinburne University of Technology.
