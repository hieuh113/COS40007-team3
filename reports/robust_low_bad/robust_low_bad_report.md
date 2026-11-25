# Walk-forward `low_bad` experiments

Chỉ đọc train/validation; không mở test. Các fold walk-forward không chồng batch validation, mỗi batch được dự đoán OOF tối đa một lần. Threshold grid được đánh giá trên OOF của train trước khi áp dụng nguyên trạng lên validation.

## Folds

| Fold | Train batches | Validation batches | Train `low_bad` batches | Validation `low_bad` batches/rows | Validation period |
|---|---:|---:|---:|---:|---|
| 1 | 269 | 74 | 7 | 6/365 | 2019-11-07 04:40:00 to 2019-11-27 08:39:00 |
| 2 | 343 | 73 | 13 | 6/219 | 2019-11-27 08:43:00 to 2020-02-18 22:23:00 |
| 3 | 416 | 74 | 19 | 10/326 | 2020-02-19 01:25:00 to 2020-03-27 08:17:00 |

## Phân tích batch `low_bad` trong validation

RF baseline nhận đúng `low_bad` ở 1/8 batch: `7_2020_04_08` (Yeast - BRD, 11/20 hits, 2020-04-08 22:59:00 to 2020-04-08 23:38:00).
So sánh trung vị feature của batch được nhận diện với các batch bị bỏ sót (một batch hit so với 7 batch missed; chỉ mô tả, không suy luận nguyên nhân):
- `TFE Production solids density`: hit-batch median 0.890, missed-batch median 1.200, difference -1.75 train standard deviations
- `FFTE Discharge density`: hit-batch median 1.050, missed-batch median 1.260, difference -1.49 train standard deviations
- `TFE Temperature`: hit-batch median 68.000, missed-batch median 78.000, difference -1.37 train standard deviations
- `TFE Production solids PV`: hit-batch median 42.300, missed-batch median 66.580, difference -1.32 train standard deviations
- `TFE Vacuum pressure PV`: hit-batch median -77.390, missed-batch median -64.185, difference -0.91 train standard deviations

Các chênh lệch SP/PV có thể phản ánh khác biệt batch/Part/thời gian; một batch hit không đủ để kết luận về quy luật tổng quát.

## Train walk-forward OOF

| Candidate | Macro-F1 | Balanced accuracy | `low_bad` precision | `low_bad` recall | `low_bad` FP |
|---|---:|---:|---:|---:|---:|
| `two_stage_batch_equal__raw_score_ge_0.20` | 0.380 | 0.406 | 0.179 | 0.024 | 101 |
| `two_stage_batch_equal__raw_score_ge_0.25` | 0.378 | 0.407 | 0.276 | 0.018 | 42 |
| `two_stage_batch_equal__raw_score_ge_0.15` | 0.377 | 0.399 | 0.090 | 0.032 | 295 |
| `two_stage_batch_equal__raw_score_ge_0.30` | 0.372 | 0.405 | 0.176 | 0.007 | 28 |
| `two_stage_batch_equal__raw_score_ge_0.10` | 0.370 | 0.384 | 0.060 | 0.057 | 811 |
| `two_stage_batch_equal__raw_score_ge_0.45` | 0.368 | 0.403 | 0.000 | 0.000 | 1 |
| `two_stage_non_low_bad__argmax_or_rest` | 0.368 | 0.403 | 0.000 | 0.000 | 0 |
| `two_stage_batch_equal__raw_score_ge_0.50` | 0.368 | 0.403 | 0.000 | 0.000 | 0 |
| `two_stage_batch_equal__raw_score_ge_0.35` | 0.368 | 0.403 | 0.000 | 0.000 | 11 |
| `two_stage_batch_equal__raw_score_ge_0.40` | 0.368 | 0.403 | 0.000 | 0.000 | 5 |
| `multiclass_equal_batch__argmax_or_rest` | 0.357 | 0.395 | 0.071 | 0.001 | 13 |
| `multiclass_equal_row__argmax_or_rest` | 0.357 | 0.395 | 0.000 | 0.000 | 1 |

## Validation check

| Candidate | Macro-F1 | Balanced accuracy | `low_bad` precision | `low_bad` recall | `low_bad` FP |
|---|---:|---:|---:|---:|---:|
| `two_stage_batch_equal__raw_score_ge_0.40` | 0.480 | 0.480 | 0.611 | 0.050 | 7 |
| `multiclass_equal_row` | 0.479 | 0.478 | 0.733 | 0.050 | 4 |
| `two_stage_batch_equal__raw_score_ge_0.35` | 0.478 | 0.479 | 0.440 | 0.050 | 14 |
| `two_stage_batch_equal__raw_score_ge_0.25` | 0.478 | 0.477 | 0.172 | 0.068 | 72 |
| `two_stage_batch_equal__raw_score_ge_0.30` | 0.476 | 0.476 | 0.222 | 0.054 | 42 |
| `two_stage_batch_equal__raw_score_ge_0.20` | 0.471 | 0.471 | 0.110 | 0.095 | 170 |
| `multiclass_equal_batch` | 0.470 | 0.478 | 0.571 | 0.018 | 3 |
| `two_stage_batch_equal__raw_score_ge_0.45` | 0.461 | 0.470 | 0.500 | 0.018 | 4 |
| `two_stage_batch_equal__raw_score_ge_0.15` | 0.452 | 0.453 | 0.065 | 0.117 | 372 |
| `two_stage_batch_equal__argmax_or_rest` | 0.450 | 0.465 | 0.000 | 0.000 | 0 |
| `two_stage_batch_equal__raw_score_ge_0.50` | 0.449 | 0.464 | 0.000 | 0.000 | 4 |
| `two_stage_batch_equal__raw_score_ge_0.10` | 0.442 | 0.474 | 0.087 | 0.342 | 799 |

Sample weighting makes each batch's total training weight equal; this does not create independent information or new `low_bad` batches. `low_bad` scores are uncalibrated; threshold rows are trade-off diagnostics only, not probabilities or deployment recommendations.
The validation period has already been used in prior model/threshold exploration. Treat its results as a final diagnostic for these experiments, not as an untouched estimate. A decision threshold still requires an agreed false-alarm/miss cost. Keep the final test set untouched until model and operating rule are frozen.

See `walk_forward_folds.csv`, `walk_forward_oof_metrics.csv`, `walk_forward_oof_low_bad_batch_recall.csv`, `validation_metrics_after_oof_thresholds.csv`, `validation_low_bad_batch_recall.csv`, `validation_low_bad_batch_profiles.csv`, and `validation_low_bad_hit_missed_feature_profiles.csv` for details.
