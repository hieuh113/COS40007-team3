# EDA và baseline - Theme 3

Lần chạy này chỉ đọc `train.csv` và `validation.csv`; không mở và không đánh giá `test.csv`.

- Số feature numeric: 30
- Train: 19,809 dòng / 490 batch
- Validation: 3,450 dòng / 107 batch
- Số ô feature bị thiếu: train 0, validation 0
- Lớp nhiều nhất trong train: `high_bad`
- Ứng viên không-baseline tốt nhất theo macro-F1 validation, rồi balanced accuracy: `random_forest_balanced`
- Macro-F1 validation: 0.4793; majority baseline: 0.1993
- scikit-learn: 1.8.0

## Phân bố lớp

| Split | Lop | So dong | Ti le | So batch |
|---|---|---:|---:|---:|
| train | `good` | 8,208 | 41.4% | 209 |
| train | `low_bad` | 1,338 | 6.8% | 29 |
| train | `high_bad` | 10,263 | 51.8% | 252 |
| validation | `good` | 1,757 | 50.9% | 47 |
| validation | `low_bad` | 222 | 6.4% | 8 |
| validation | `high_bad` | 1,471 | 42.6% | 52 |

## Phân bố theo `Part` trong train

| Part | Lop | So dong |
|---|---|---:|
| Yeast - BRD | `good` | 3,632 |
| Yeast - BRD | `high_bad` | 4,520 |
| Yeast - BRD | `low_bad` | 552 |
| Yeast - BRN | `good` | 2,118 |
| Yeast - BRN | `high_bad` | 1,751 |
| Yeast - BRN | `low_bad` | 406 |
| Yeast - FMX | `good` | 2,458 |
| Yeast - FMX | `high_bad` | 3,992 |
| Yeast - FMX | `low_bad` | 380 |

## So sánh trên validation

| Model | Accuracy | Macro-F1 | Balanced accuracy | Log loss | Multiclass Brier |
|---|---:|---:|---:|---:|---:|
| `random_forest_balanced` | 0.6580 | 0.4793 | 0.4781 | 0.8098 | 0.4865 |
| `hist_gradient_boosting` | 0.6020 | 0.4354 | 0.4388 | 1.1945 | 0.6114 |
| `logistic_regression_balanced` | 0.4203 | 0.3794 | 0.4552 | 1.1161 | 0.6767 |
| `majority_baseline` | 0.4264 | 0.1993 | 0.3333 | 20.6755 | 1.1472 |

Ứng viên tốt nhất: `random_forest_balanced`. Metric theo lớp trên validation:

| Lop | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| `good` | 0.6506 | 0.7769 | 0.7082 | 1,757 |
| `low_bad` | 0.7333 | 0.0495 | 0.0928 | 222 |
| `high_bad` | 0.6687 | 0.6077 | 0.6368 | 1,471 |

Log loss của ứng viên tốt nhất trên validation: 0.8098 (lower is better). Đây là proper scoring rule, không thay thế kiểm tra reliability/calibration riêng.
Multiclass Brier score trên validation: 0.4865 (mean squared probability error, lower is better). ECE one-vs-rest theo 10 quantile bins: `{"good": 0.07882671447750984, "low_bad": 0.03889742539314075, "high_bad": 0.05435451708568628}`.
Reliability plot và bin counts là kiểm tra ngoài mẫu trên validation, không phải phép hiệu chỉnh xác suất. Chưa bật hiển thị xác suất trong demonstrator.

Confusion matrix của ứng viên tốt nhất (hàng = nhãn thật, cột = nhãn dự đoán; thứ tự `good`, `low_bad`, `high_bad`):

```text
[[1365    3  389]
 [ 157   11   54]
 [ 576    1  894]]
```

**Cảnh báo:** recall `low_bad` của `random_forest_balanced` là 0.0495 (11/222 mẫu validation được nhận đúng). Macro-F1 cao hơn majority baseline nhưng model chưa đủ tin cậy cho lớp này; cần phân tích lỗi/tuning trên train và validation trước khi xem test.

Ứng viên được chọn tạm thời chỉ dựa trên validation, không phải kết quả cuối cùng. Class weights được tính trong `fit` trên train. `StandardScaler` của Logistic Regression nằm trong pipeline và chỉ fit trên train. Không dùng validation/test để fit preprocessing; chưa hiệu chỉnh xác suất.

## Tệp EDA được tạo

`class_distribution.csv`, `train_part_class_counts.csv`, `train_monthly_class_counts.csv`, `train_feature_summary_by_class.csv`, `feature_missingness.csv`, `validation_model_comparison.csv`, `validation_classification_reports.json`, `validation_confusion_matrices.json`, `validation_probability_metrics.json`, `validation_reliability_bins.csv` và bốn biểu đồ PNG.
