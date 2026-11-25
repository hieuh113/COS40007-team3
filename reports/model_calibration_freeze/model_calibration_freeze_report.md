# Báo cáo Benchmark Mô hình Mở rộng, Hiệu chỉnh Xác suất (Calibration) và Đóng băng Mô hình

- **Thời điểm khóa giao thức (Freeze Timestamp):** `2026-11-25T10:47:45`
- **Trạng thái tập Test (`test.csv`):** `UNTOUCHED / LOCKED` (Chỉ sử dụng `train.csv` và `validation.csv` trong toàn bộ bước này).
- **Mô hình chính được chọn:** `random_forest_balanced` (`RandomForestClassifier`, 300 cây, `min_samples_leaf=2`, `class_weight='balanced_subsample'`, `random_state=42`).
- **Phương pháp Calibration được chọn:** `uncalibrated` (fit trên Walk-Forward Out-of-Fold).
- **File Model Artifact đã đóng băng:** `Theme3/Processed_Data/frozen_model/quality_model_frozen.joblib` (SHA-256: `73f696639b66c7a2...`).

## 1. Kết quả Benchmark 5 Mô hình trên Validation (`validation.csv` - 107 batch / 3.450 dòng)

| Model | Accuracy | Macro-F1 | Balanced Acc | Macro PR-AUC | `low_bad` PR-AUC | `low_bad` Recall | `low_bad` Precision | Log Loss | Brier Score | Mean ECE |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `random_forest_balanced` | 0.6580 | 0.4793 | 0.4781 | 0.4907 | 0.1248 | 0.0495 | 0.7333 | 0.8098 | 0.4865 | 0.0574 |
| `hist_gradient_boosting_balanced` | 0.5823 | 0.4467 | 0.4384 | 0.4339 | 0.1436 | 0.0991 | 0.3143 | 1.0712 | 0.6085 | 0.1270 |
| `extra_trees_balanced` | 0.6441 | 0.4358 | 0.4505 | 0.4877 | 0.0947 | 0.0000 | 0.0000 | 0.8134 | 0.4860 | 0.0457 |
| `logistic_regression_balanced` | 0.4203 | 0.3794 | 0.4552 | 0.4206 | 0.0991 | 0.5495 | 0.1018 | 1.1161 | 0.6767 | 0.1951 |
| `majority_baseline` | 0.4264 | 0.1993 | 0.3333 | 0.3333 | 0.0643 | 0.0000 | 0.0000 | 19.8122 | 1.1472 | 0.3824 |

## 2. Kết quả Benchmark 5 Mô hình trên Walk-Forward OOF (`train.csv` - 3 Folds không chồng batch)

| Model | Accuracy | Macro-F1 | Balanced Acc | Macro PR-AUC | `low_bad` PR-AUC | `low_bad` Recall | Log Loss | Brier Score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `extra_trees_balanced` | 0.5625 | 0.3958 | 0.4283 | 0.4234 | 0.1012 | 0.0000 | 1.0884 | 0.5724 |
| `hist_gradient_boosting_balanced` | 0.5208 | 0.3781 | 0.3994 | 0.4102 | 0.1030 | 0.0187 | 1.4037 | 0.6845 |
| `logistic_regression_balanced` | 0.4252 | 0.3596 | 0.3660 | 0.3825 | 0.1045 | 0.1758 | 1.1355 | 0.6791 |
| `random_forest_balanced` | 0.5069 | 0.3569 | 0.3954 | 0.4062 | 0.0991 | 0.0000 | 1.2346 | 0.5989 |
| `majority_baseline` | 0.3633 | 0.1777 | 0.3333 | 0.3333 | 0.1071 | 0.0000 | 21.9910 | 1.2734 |

## 3. So sánh Hiệu chỉnh Xác suất (Probability Calibration trên OOF)

| Phương pháp | OOF Log Loss | OOF Brier | OOF Mean ECE | Val Log Loss | Val Brier | Val Mean ECE | Val Macro-F1 | Val `low_bad` PR-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `uncalibrated` | 1.2346 | 0.5989 | 0.1286 | 0.8098 | 0.4865 | 0.0574 | 0.4793 | 0.1248 |
| `temperature` | 0.9990 | 0.5864 | 0.0993 | 0.9244 | 0.5545 | 0.1458 | 0.4793 | 0.1271 |
| `sigmoid` | 0.9058 | 0.5468 | 0.0572 | 0.8445 | 0.5114 | 0.0906 | 0.4793 | 0.0687 |
| `isotonic` | 0.8856 | 0.5308 | 0.0289 | 0.8581 | 0.5185 | 0.0911 | 0.4793 | 0.0690 |

## 4. Độ ổn định theo phân nhóm `Part` trên Validation

| Part | Số dòng | Số batch | Accuracy | Macro-F1 | Balanced Acc | `low_bad` Recall | `low_bad` PR-AUC | Brier Score |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `Yeast - BRD` | 1,583 | 39 | 0.6235 | 0.3707 | 0.3478 | 0.1618 | 0.2385 | 0.5273 |
| `Yeast - BRN` | 800 | 23 | 0.5413 | 0.3103 | 0.3470 | 0.0000 | 0.1408 | 0.5862 |
| `Yeast - FMX` | 1,067 | 45 | 0.7966 | 0.3483 | 0.3513 | 0.0000 | 0.0499 | 0.3512 |

## 5. Quyết định Đóng băng Giao thức (Frozen Decision Rule)

- **Quy tắc phân loại chính (Primary Classification Rule):** Giữ quy tắc `argmax` của `random_forest_balanced` vì đạt **Macro-F1 cao nhất (`0.4793`)**, **Accuracy cao nhất (`0.6580`)**, **Log Loss tốt nhất (`0.8098`)** và **Precision lớp `low_bad` cao (`0.7333`, chỉ có 4 False Positives trên 3.450 dòng)**.
- **Quy tắc cảnh báo sớm lớp thiểu số (Two-Tier Minority Risk Alert Rule):** Vì `low_bad` chỉ chiếm 6.4% số dòng validation (8 batch) và có sự dịch chuyển phân phối giữa các batch, việc ép hạ ngưỡng phân loại chính xuống `0.05` hoặc `0.10` sẽ làm nổ hàng nghìn báo động giả (False Positives) và kéo tụt Macro-F1. Do đó, hệ thống đóng băng kiến trúc **2 tầng cảnh báo** cho Demonstrator:
  1. **Nhãn dự đoán chính:** Dự đoán theo `argmax`.
  2. **Cảnh báo rủi ro `low_bad` phụ trợ (Advisory Risk Warning):** Khi xác suất $P(\text{low\_bad}) \ge 0.15$ (Mức `WATCH`) hoặc $\ge 0.25$ (Mức `ELEVATED ALERT` — điểm tối ưu hóa Macro-F1 lên `0.4903` trên Validation), giao diện sẽ bật cờ cảnh báo riêng để người vận hành kiểm tra mẻ sản xuất mà không làm sai lệch nhãn phân loại tổng thể.
- **Trạng thái sẵn sàng cho đánh giá Test cuối:** Toàn bộ tham số, bộ hiệu chỉnh, miền dữ liệu 30 biến (`feature_domain`) và quy tắc ngưỡng đã được khóa trong `quality_model_frozen.joblib` và `model_freeze_manifest.json`. Đủ điều kiện mở tập `test.csv` một lần duy nhất.
