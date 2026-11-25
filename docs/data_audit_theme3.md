# Bao cao kiem toan du lieu va nhan Theme 3

Ngay kiem tra: 10/11/2026  
Script tai lap: [`audit_theme3_data.py`](audit_theme3_data.py)  
Data dictionary: [`data_dictionary_theme3.md`](data_dictionary_theme3.md)

Script doc cac CSV va in ket qua ra terminal; khong sua file nguon.

## Pham vi va ket qua

Ba file nhan co chung 33 cot va 30.375 dong du lieu. Moi cot du lieu trong ba file deu co gia tri; khong co `Set Time` khong parse duoc; cac cot ngoai metadata (`VYP batch`, `Part`, `Set Time`) deu parse thanh so huu han. `Set Time` co dinh dang ngay/thang/nam va gio/phut; timezone khong duoc cung cap.

| File / nhan | So dong | Ti le dong | Batch trong file | Nhom dong lap hoan toan | Dong lap du (excess) | Thoi gian Set Time |
|---|---:|---:|---:|---:|---:|---|
| `good.csv` / `good` | 13.302 | 43,79% | 301 | 301 | 1.806 | 02/07/2019 00:10 - 25/06/2020 20:02 |
| `low bad.csv` / `low_bad` | 2.578 | 8,49% | 59 | 59 | 354 | 04/07/2019 17:31 - 26/06/2020 03:27 |
| `high bad.csv` / `high_bad` | 14.495 | 47,72% | 344 | 346 | 2.070 | 01/07/2019 07:59 - 25/06/2020 23:53 |
| **Tong** | **30.375** | **100%** | **703 batch duy nhat** | **706 nhom trong tung file** | **4.230** | **01/07/2019 - 26/06/2020** |

Ca ba file co cung ba gia tri `Part`: `Yeast - BRD`, `Yeast - BRN`, `Yeast - FMX`. Moi file co 7 cot ten ket thuc bang `SP`; cac cot con lai la metadata hoac process/sensor fields theo mo ta trong brief. Don vi va y nghia chi tiet cua tag khong co trong CSV.

## Duplicate va mau thuan nhan

- Exact duplicate duoc tinh bang toan bo 33 gia tri cot trong mot dong. So `duplicate_excess` la so ban sao vuot qua mot dong dai dien trong moi nhom duplicate: good 1.806, low_bad 354, high_bad 2.070; tong 4.230. Day la cac dong lap hoan toan, khong phai chi la cac dong cung batch.
- Co **36 dong day du giong het nhau** xuat hien trong ca `good.csv` va `low bad.csv`. Tat ca thuoc batch `97_2020_06_25`; day la xung dot nhan theo batch duy nhat giua ba file.
- `output_log.csv` co 704 dong va 703 batch duy nhat, bao phu toan bo 703 batch trong cac file nhan. Batch `97_2020_06_25` xuat hien hai lan, mot lan `low_bad` va mot lan `good`. Tap nhan trong log khop voi tap nhan trong cac file, nhung log **lap lai xung dot thay vi phan xu**; khong duoc dung de chon mot nhan cho batch nay.
- Cac cot `Comments` va `To Product` trong downtime log co gia tri thieu, nhung khong anh huong den viec audit cac cot cua ba quality files.

## Xu ly du lieu de mo hinh hoa

1. Giu nguyen cac file goc. Tao derived dataset rieng, giu `source_file`, `quality_class` va provenance.
2. Trong derived dataset, chi giu mot ban sao cua moi dong lap hoan toan trong cung file nhan; luu so lan lap de audit va tranh tang trong so mau lap. Khong sua hoac xoa ban ghi goc.
3. Cach ly **toan bo batch `97_2020_06_25`** khoi train/validation/test co giam sat cho den khi co nguon nghiep vu doc lap xac nhan nhan. Khong chi bo 36 dong trung, vi nhan mau thuan la o cap batch.
4. Khong dung `output_log.csv` de phan xu mau thuan tren; log ghi ca hai nhan cho batch nay.
5. Giu batch va thoi gian lam metadata cho chia tap. Khong dua `VYP batch` vao feature mac dinh; khong dung thong tin tuong lai trong cung batch de du doan tai `Set Time`.

## Gioi han cua ket qua

Audit xac nhan format va tinh day du ve mat gia tri trong ba quality CSV, nhung khong xac nhan y nghia nghiep vu/nguong cua quality labels, don vi/tag, timezone, latency sensor hay bounds van hanh SP. Cac diem nay can data dictionary chinh thuc hoac xac nhan cua chuyen gia truoc khi dung cho khuyen nghi van hanh.

## Pipeline va split da tao

Script [`preprocess_theme3_data.py`](preprocess_theme3_data.py) tao cac CSV dan xuat va manifest tai `Theme3/Processed_Data/`. Thu muc dau ra co `.gitignore` de tranh dua du lieu san xuat dan xuat len repository. Workspace hien khong co Git repository tai `Project`, nen chua the xac minh hieu luc cua quy tac ignore; cac file nguon khong bi sua.

- Sau khi giu mot ban sao cho moi dong lap trong cung file nhan: 26.145 dong duy nhat. Cach ly 72 dong sau dedup cua batch 97 (36 dong `good`, 36 dong `low_bad`); con 26.073 dong du dieu kien chia tap.
- Chia theo batch tang dan theo `Set Time` dau tien. Ranh gioi chi duoc chon khi khoang thoi gian cac batch ben trai ket thuc truoc khi batch ben phai bat dau, do do batch khong bi cat va cac split khong chong timestamp.
- Train: 490 batch, 19.809 dong, 01/07/2019 07:59 - 27/03/2020 08:17.
- Validation: 107 batch, 3.450 dong, 27/03/2020 08:27 - 04/05/2020 17:33.
- Test: 105 batch, 2.814 dong, 04/05/2020 19:09 - 26/06/2020 03:27.
- Feature matrix candidate chi gom 30 cot SP/process numeric. `VYP batch`, `Part`, `Set Time`, nhan va provenance la metadata; `Part` chua duoc dua vao feature do chua xac nhan thoi diem co san. Khong fit imputer/encoder/scaler va khong resample o buoc tao split: cac file nhan khong co o trong, feature la numeric; neu mo hinh can scaling hoac xu ly imbalance, thuc hien tren train only trong pipeline mo hinh.
- Manifest ghi SHA-256 cua cac CSV nguon, quy tac split, counts va provenance. Moi dong giu file nguon, so dong goc va `duplicate_count`; cac so do tuong lai trong cung batch khong duoc tong hop vao feature cua dong hien tai.