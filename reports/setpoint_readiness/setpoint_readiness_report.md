# Setpoint recommendation readiness

## Decision

**Chưa đủ căn cứ đưa ra khuyến nghị vận hành hoặc xếp hạng SP ứng viên.** Không tìm thấy operating bounds được chuyên gia/tài liệu có thẩm quyền phê duyệt trong tài liệu project. Script không tạo candidate ranking.

Các min/max và quantile trong `observed_sp_ranges.csv` chỉ mô tả giá trị đã quan sát ở train/validation. Chúng không phải giới hạn an toàn/được phê duyệt và không được dùng để tạo candidate bounds.

## SP fields inspected

| SP field | Train min-max | Train q01-q99 | Validation min-max | Validation outside train range |
|---|---:|---:|---:|---:|
| `FFTE Feed solids SP` | 25 to 50 | 25 to 50 | 25 to 50 | 0 |
| `FFTE Production solids SP` | 39 to 43 | 39 to 43 | 41 to 43 | 0 |
| `FFTE Steam pressure SP` | 12 to 850 | 55 to 158.789 | 60 to 160 | 0 |
| `TFE Out flow SP` | 1240 to 3278.6 | 1725.3 to 3083.72 | 1925.3 to 2846.51 | 0 |
| `TFE Production solids SP` | 0 to 88 | 27.49 to 85 | 0 to 98 | 3 |
| `TFE Vacuum pressure SP` | -89 to -35 | -89 to -36.37 | -80 to -36.37 | 0 |
| `TFE Steam pressure SP` | 2 to 135 | 55 to 127.546 | 2 to 130 | 0 |

## Additional blocking conditions

- Don vi, y nghia chi tiet cua tag, co the dieu khien, va thoi diem SP/PV co san chua duoc xac nhan trong data dictionary.
- Mo hinh chat luong hien tai chi dat validation macro-F1 0,4793; recall `low_bad` 0,0495. Xac suat chua duoc phe duyet de dung xep hang SP.
- Khuyen nghi tu du lieu quan sat khong chung minh tinh nhan qua. Can co process state hien tai hop le, muc tieu duoc chot, va review/validation boi chuyen gia.

## Conditions to reopen ranking

1. Them bounds duoc phe duyet cho ca 7 SP vao `approved_operating_bounds.json`, moi muc co min, max va citation/source; khong dien bang train min/max.
2. Xac nhan don vi, tag semantics, control authority, snapshot timing va input operating domain.
3. Duyet lai quality model tren batch/time holdout; neu dung probability score thi hoan tat calibration/uncertainty review.
4. Chi khi cac gate nay qua moi sinh candidate, giu nguyen `Part` va process state, ghi muc thay doi va trinh nguoi van hanh review. Khong tu dong dieu khien may.

This run used only train/validation summaries; the final test split was not opened.
