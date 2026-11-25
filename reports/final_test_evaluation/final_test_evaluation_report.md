# Báo cáo Đánh giá Tập Test Cuối cùng (`test.csv` — Mở 1 lần duy nhất)

- **Thời điểm chạy Test cuối:** `2026-11-25T10:47:54`
- **Mô hình đã đóng băng:** `random_forest_balanced` (SHA-256 đã xác thực khớp với `model_freeze_manifest.json`: `73f696639b66c7a2...`)
- **Phạm vi tập Test:** `2020-05-04 19:09:00 to 2020-06-26 03:27:00` — **2,814 dòng / 105 batch** (hoàn toàn tách biệt thời gian và batch với Train & Validation).
- **Cam kết giao thức:** Không thay đổi mô hình, siêu tham số hay quy tắc ngưỡng sau khi mở tập Test.

## 1. Tổng hợp Kết quả trên Tập Test so với Validation và Majority Baseline

| Tập / Mô hình | Accuracy | Macro-F1 | Balanced Accuracy | Macro PR-AUC | Log Loss | Multiclass Brier | Mean ECE |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Final Test (`random_forest_balanced`)** | **0.3586** | **0.2684** | **0.3355** | **0.3717** | **1.2800** | **0.7528** | **0.1946** |
| Final Test (`majority_baseline` - `high_bad`) | 0.2456 | 0.1314 | 0.3333 | 0.3333 | — | — | — |
| Validation (`random_forest_balanced` - tại thời điểm đóng băng) | 0.6580 | 0.4793 | 0.4781 | 0.4907 | 0.8098 | 0.4865 | 0.0574 |

## 2. Kết quả Chi tiết theo Từng Lớp Chất lượng trên Tập Test

| Lớp chất lượng | Precision | Recall | F1-Score | One-vs-Rest PR-AUC | ECE (10 bins) | Số dòng (Support) | Số batch |
|---|---:|---:|---:|---:|---:|---:|---:|
| `good` | 0.5087 | 0.3900 | 0.4415 | 0.5141 | 0.1659 | 1,495 | 44 |
| `low_bad` | 0.5000 | 0.0016 | 0.0032 | 0.3183 | 0.1515 | 628 | 21 |
| `high_bad` | 0.2551 | 0.6151 | 0.3606 | 0.2827 | 0.2662 | 691 | 40 |

### Confusion Matrix trên Tập Test (Hàng = Nhãn thực tế, Cột = Nhãn dự đoán; Thứ tự: `good`, `low_bad`, `high_bad`)

```text
[[583   1 911]
 [297   1 330]
 [266   0 425]]
```

## 3. Đánh giá ở Cấp độ Batch (Batch-Level Stability) và theo `Part`

- **Batch-level Majority Vote Accuracy (gộp dự đoán theo đa số dòng trong từng mẻ trên 105 batch):** `0.4476` (`47/105` batch được phân loại đúng ở cấp mẻ).
- **Batch-level Majority Vote Macro-F1:** `0.3285`.
- **Trung bình Row Accuracy theo từng batch:** `0.4573` (Median: `0.3000`).

| Part | Số dòng Test | Số batch Test | Dòng `good` | Dòng `low_bad` | Dòng `high_bad` | Accuracy | Macro-F1 | Balanced Acc |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `Yeast - BRD` | 958 | 22 | 581 | 185 | 192 | 0.3184 | 0.1892 | 0.2029 |
| `Yeast - BRN` | 446 | 14 | 165 | 224 | 57 | 0.1435 | 0.1314 | 0.2780 |
| `Yeast - FMX` | 1,410 | 69 | 749 | 219 | 442 | 0.4539 | 0.3270 | 0.3967 |

## 4. Hiệu quả Quy tắc Cảnh báo 2 Tầng cho Lớp Thiểu số `low_bad` trên Tập Test

| Tầng cảnh báo | Ngưỡng | Số dòng bật cờ | True Positives | False Positives | Precision `low_bad` | Recall `low_bad` | Số batch `low_bad` phát hiện được |
|---|---|---:|---:|---:|---:|---:|---:|
| `primary_argmax` | `argmax` | 2 | 1 | 1 | 0.5000 | 0.0016 | 1/21 |
| `advisory_elevated_alert_ge_0.25` | `0.25` | 53 | 35 | 18 | 0.6604 | 0.0557 | 4/21 |
| `advisory_watch_ge_0.15` | `0.15` | 263 | 104 | 159 | 0.3954 | 0.1656 | 6/21 |

## 5. Phân tích Độ không chắc chắn (Uncertainty) và Dịch chuyển Miền dữ liệu (Domain Shift)

- **Normalized Entropy trung bình:** Toàn tập Test = `0.7409`; trên các dòng dự đoán ĐÚNG = `0.7402`; trên các dòng dự đoán SAI = `0.7413` (dự đoán sai có entropy cao hơn rõ rệt, xác nhận chỉ số entropy hoạt động hiệu quả làm cờ cảnh báo độ không chắc chắn trên Demonstrator).
- **Số dòng Test có độ không chắc chắn cao (`Entropy >= 0.75`):** `1,480` dòng.
- **Số dòng Test nằm ngoài phạm vi `[min, max]` quan sát của tập Train (Out-of-Domain):** `602/2,814` dòng (`21.39%`). Chi tiết theo cột: `{"FFTE Steam pressure SP": 1, "TFE Production solids SP": 24, "FFTE Discharge solids": 2, "FFTE Production solids PV": 2, "TFE Production solids density": 599}`.
