# Phân tích lỗi và tuning `low_bad`

Thí nghiệm chỉ fit trên `train.csv` và đánh giá/chọn trade-off trên `validation.csv`; không đọc `test.csv`. Các kết quả validation dưới đây dùng để khảo sát và chọn ứng viên, không phải ước lượng cuối cùng sau tuning.

Validation có 8 batch chứa `low_bad` với tổng 222 dòng. Baseline Random Forest `balanced_subsample` giữ quy tắc argmax có recall 0.0495, precision 0.7333, macro-F1 0.4793, và dự đoán `low_bad` 15 lần.
Tăng class weight mà vẫn dùng argmax không nâng recall `low_bad` vượt baseline (cao nhất 0.0495). Ứng viên macro-F1 cao nhất khi quét ngưỡng là `low_bad_weight_x1__raw_score_ge_0.25`: macro-F1 0.4903, precision/recall `low_bad` 0.2656/0.0766, 47 false positives.

## Baseline recall theo batch

| Batch | low_bad rows | Correct low_bad predictions | Recall |
|---|---:|---:|---:|
| `109_2020_03_31` | 17 | 0 | 0.000 |
| `131_2020_04_03` | 17 | 0 | 0.000 |
| `43_2020_04_21` | 48 | 0 | 0.000 |
| `57_2020_04_23` | 13 | 0 | 0.000 |
| `59_2020_04_23` | 35 | 0 | 0.000 |
| `76_2020_04_28` | 37 | 0 | 0.000 |
| `78_2020_04_28` | 35 | 0 | 0.000 |
| `7_2020_04_08` | 20 | 11 | 0.550 |

## Class weighting với argmax

| Candidate | low_bad precision | low_bad recall | low_bad F1 | Macro-F1 | Balanced accuracy | FP low_bad |
|---|---:|---:|---:|---:|---:|---:|
| `balanced_subsample__argmax` | 0.733 | 0.050 | 0.093 | 0.479 | 0.478 | 4 |
| `low_bad_weight_x8__argmax` | 0.667 | 0.045 | 0.084 | 0.477 | 0.477 | 5 |
| `low_bad_weight_x16__argmax` | 0.769 | 0.045 | 0.085 | 0.473 | 0.473 | 3 |
| `low_bad_weight_x32__argmax` | 0.625 | 0.045 | 0.084 | 0.469 | 0.469 | 6 |
| `low_bad_weight_x4__argmax` | 0.600 | 0.014 | 0.026 | 0.457 | 0.467 | 2 |
| `low_bad_weight_x1__argmax` | 0.000 | 0.000 | 0.000 | 0.452 | 0.466 | 3 |
| `low_bad_weight_x2__argmax` | 0.000 | 0.000 | 0.000 | 0.442 | 0.456 | 2 |

## Phương án ưu tiên recall

| Candidate | Rule | low_bad precision | low_bad recall | Dự đoán low_bad | Macro-F1 | FP low_bad |
|---|---|---:|---:|---:|---:|---:|
| `low_bad_weight_x2__raw_score_ge_0.05` | `raw_score_ge_0.05` | 0.083 | 0.928 | 2486 | 0.268 | 2280 |
| `low_bad_weight_x4__raw_score_ge_0.05` | `raw_score_ge_0.05` | 0.082 | 0.919 | 2500 | 0.254 | 2296 |
| `low_bad_weight_x1__raw_score_ge_0.05` | `raw_score_ge_0.05` | 0.080 | 0.892 | 2471 | 0.256 | 2273 |
| `balanced_subsample__raw_score_ge_0.05` | `raw_score_ge_0.05` | 0.081 | 0.878 | 2407 | 0.273 | 2212 |
| `low_bad_weight_x8__raw_score_ge_0.05` | `raw_score_ge_0.05` | 0.080 | 0.838 | 2314 | 0.277 | 2128 |
| `low_bad_weight_x16__raw_score_ge_0.05` | `raw_score_ge_0.05` | 0.078 | 0.716 | 2037 | 0.322 | 1878 |
| `low_bad_weight_x32__raw_score_ge_0.05` | `raw_score_ge_0.05` | 0.079 | 0.631 | 1774 | 0.346 | 1634 |
| `low_bad_weight_x4__raw_score_ge_0.10` | `raw_score_ge_0.10` | 0.085 | 0.477 | 1240 | 0.399 | 1134 |

## Phương án ưu tiên macro-F1

| Candidate | Rule | low_bad precision | low_bad recall | Dự đoán low_bad | Macro-F1 | Balanced accuracy | FP low_bad |
|---|---|---:|---:|---:|---:|---:|---:|
| `low_bad_weight_x1__raw_score_ge_0.25` | `raw_score_ge_0.25` | 0.266 | 0.077 | 64 | 0.490 | 0.487 | 47 |
| `balanced_subsample__raw_score_ge_0.30` | `raw_score_ge_0.30` | 0.375 | 0.068 | 40 | 0.486 | 0.482 | 25 |
| `balanced_subsample__raw_score_ge_0.25` | `raw_score_ge_0.25` | 0.250 | 0.077 | 68 | 0.485 | 0.481 | 51 |
| `balanced_subsample__raw_score_ge_0.40` | `raw_score_ge_0.40` | 0.706 | 0.054 | 17 | 0.482 | 0.479 | 5 |
| `low_bad_weight_x8__raw_score_ge_0.25` | `raw_score_ge_0.25` | 0.234 | 0.068 | 64 | 0.481 | 0.479 | 49 |
| `low_bad_weight_x4__raw_score_ge_0.25` | `raw_score_ge_0.25` | 0.264 | 0.063 | 53 | 0.480 | 0.478 | 39 |
| `low_bad_weight_x8__raw_score_ge_0.40` | `raw_score_ge_0.40` | 0.688 | 0.050 | 16 | 0.480 | 0.479 | 5 |
| `low_bad_weight_x8__raw_score_ge_0.30` | `raw_score_ge_0.30` | 0.387 | 0.054 | 31 | 0.479 | 0.478 | 19 |

`raw_score_ge_*` là ngưỡng trên điểm `predict_proba` chưa được hiệu chỉnh, không được diễn giải là xác suất tin cậy. Thí nghiệm không tự chọn ngưỡng triển khai: cần nhóm/chuyên gia xác định đánh đổi giữa bỏ sót `low_bad` và false alarms.

Kết quả phải được xem ở cấp batch: nếu recall tập trung vào một vài batch, cải thiện trên dòng không đồng nghĩa tổng quát hóa qua batch. Chốt mô hình/quy tắc dự đoán sau phân tích train-validation; chỉ sau đó mới chạy test một lần để báo cáo cuối.

Artifacts: `validation_low_bad_tradeoffs.csv`, `validation_low_bad_batch_recall.csv`, `validation_low_bad_confusion_matrices.json`.
