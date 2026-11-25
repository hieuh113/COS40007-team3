# Downtime data readiness and exploratory trend screen

## Decision

**Không đủ căn cứ cho supervised downtime prediction.** Không huấn luyện classifier, không đặt prediction horizon/nhãn giả định, và không xuất downtime probability.

Event log có 218 dòng, từ 2020-05-04 13:30:00 đến 2020-07-02 04:10:00; không có timestamp lỗi hoặc dòng lặp chính xác. `Time` và `Total Time Mins` có thể gợi ý thời điểm/thời lượng, nhưng chưa xác nhận `Time` chính là thời điểm bắt đầu và không có event end timestamp riêng.
Các category thường gặp: Startup=60, Shutdown=56, TFE=51, Sanitation=33, Extract Vat=8, Changeover=3, Personnel=2, FFTE=2. Vì log gồm cả startup/shutdown/sanitation và process causes, không thể gán tất cả dòng thành cùng một loại hỏng hóc ngoài kế hoạch.
Equipment fields trong log chỉ có Dept=2, Line=6, Sub Line=0; mapping tag/thiết bị chưa được xác minh. Thiếu `Comments` ở 104/218 dòng và `To Product` ở 215/218 dòng.
Không có lịch vận hành hoặc khoảng non-event đã xác nhận; vì vậy không thể coi thời điểm không xuất hiện trong log là normal.

## Trend coverage and exploratory outlier screen

| Trend source | Rows | Coverage | Median interval (s) | Events in time window* | Rows with >=1 robust outlier |
|---|---:|---|---:|---:|---:|
| `evaporator` | 359,485 | 2020-05-18 00:00:33 to 2020-05-22 23:59:31.399000 | 1.02 | 27 | 82,916 (23.07%) |
| `ffte` | 132,062 | 2020-06-22 00:00:50 to 2020-06-26 23:59:45.137000 | 2.05 | 25 | 22,061 (16.71%) |
evaporator: 8 measurement tags; missing-value rate ranges from 69.6% to 97.5%.
ffte: 7 measurement tags; missing-value rate ranges from 19.1% to 99.9%.

*Thời điểm event nằm trong dải ngày/giờ của file trend chỉ là overlap theo đồng hồ; không chứng minh event cùng equipment/tag với trend.

Sàng lọc dùng robust z-score theo từng measurement (median/MAD, ngưỡng 4,5), không có nhãn để xác thực và không phải detector đã kiểm định. Các điểm khác thường có thể là startup/shutdown, product/operating mode change, hoặc lỗi chất lượng sensor. Không diễn giải chúng thành downtime risk.

## Next evidence required

1. Người phụ trách quy trình xác nhận event taxonomy: planned stop, startup/shutdown, sanitation, unplanned fault; xác nhận `Time` là start time và duration/end semantics.
2. Cung cấp lịch sản xuất/uptime để xây dựng các khoảng non-event đã xác nhận, không mặc định log absence là normal.
3. Xác nhận Dept/Line/Sub Line tới FFTE/TFE/Extract Tank và trend tags; thống nhất timezone, clock offset và cách ghép thời gian.
4. Chỉ khi đủ coverage mới chốt horizon/label rule, chia theo thời gian/batch và đánh giá event recall, false alarms, missed events, lead time.
5. Nếu chỉ dùng anomaly screening, giữ riêng nhãn exploratory và không gọi là downtime prediction/probability.

Inputs used: downtime log, two supplied weekly trend CSVs. No quality-model test split was opened; no supervised downtime model was trained.
