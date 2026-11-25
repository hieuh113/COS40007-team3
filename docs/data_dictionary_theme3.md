# Từ điển dữ liệu - Dữ liệu chất lượng Theme 3

## Phạm vi và quy ước

Dictionary nay mo ta 33 cot chung trong `good.csv`, `low bad.csv` va `high bad.csv` tai `Theme3/data_02_07_2019-26-06-2020/`.

Mo ta ve SP, Part, batch, thoi gian va sensor chi duoc rut ra tu ten cot, brief hoac gia tri quan sat trong du lieu. Don vi, timezone, dinh nghia tag chi tiet, do tre thu thap va operating bounds **chua duoc cac nguon co tham quyen trong workspace xac nhan**. Khong dien cac gia tri nay bang suy doan.

## Trạng thái xác nhận bắt buộc

Moi truong dictionary su dung cac trang thai sau:

- `CONFIRMED`: don vi, y nghia, pham vi va nguon da duoc xac nhan boi tai lieu hoac chuyen gia co tham quyen.
- `DATA_DEFINED`: chi ten cot va gia tri/format da duoc kiem tra trong CSV; chua co nghia nghiep vu hoac don vi.
- `PENDING_VERIFICATION`: yeu cau xac nhan truoc khi dung cho feature nghiep vu, ranking SP, control hay downtime event mapping.
- `NOT_APPLICABLE`: cot metadata khong the hien mot do luong process.

Quy tac gating:

- Khong suy unit tu ten cot.
- Khong suy timezone tu du lieu neu chuoi thoi gian khong kem timezone trong nguon.
- Khong dung min/max quan sat lam operating bounds.
- Khong them cot vao khuyen nghi SP cho den khi duoc chuyen gia xac nhan control authority, unit va pham vi hop le.
- Co the dung cot trong EDA/baseline sau khi kiem tra ngay, missing, datatype va group split; viec dung nay khong tu dong co nghia la da xac nhan nghiep vu.

| Ten cot (giu nguyen) | Nhom | Y nghia theo nguon hien co | Don vi | Thoi diem co san / vai tro | Co the dieu khien? |
|---|---|---|---|---|---|
| `VYP batch` | Metadata | Ma batch san xuat, co ma/ngay trong ten | Khong ap dung | Dung de truy vet, gom nhom va chia tap; khong dung lam feature mac dinh | Khong |
| `Part` | Metadata | Loai yeast/nguyen lieu theo brief | Khong ap dung | Ghi nhan theo quan sat; thoi diem he thong van hanh biet gia tri nay can xac minh. Giu de phan tich theo nhom | Khong |
| `Set Time` | Timestamp | Thoi diem ghi nhan SP va sensor; dang chuoi `day/month/year hour:minute` trong cac file da kiem tra | Thoi gian; timezone chua ro | Moc thoi gian cua dong; dung sap xep va chia theo thoi gian, khong dung lam feature mac dinh | Khong |
| `FFTE Feed solids SP` | SP | Setpoint Feed solids cua FFTE theo ten tag | Chua duoc cung cap | Gia tri tai dong `Set Time`; xac minh dong bo truoc khi dung | Co, theo brief; can xac minh y nghia va bounds voi chuyen gia |
| `FFTE Production solids SP` | SP | Setpoint Production solids cua FFTE theo ten tag | Chua duoc cung cap | Gia tri tai dong `Set Time`; xac minh dong bo truoc khi dung | Co, theo brief; can xac minh y nghia va bounds voi chuyen gia |
| `FFTE Steam pressure SP` | SP | Setpoint Steam pressure cua FFTE theo ten tag | Chua duoc cung cap | Gia tri tai dong `Set Time`; xac minh dong bo truoc khi dung | Co, theo brief; can xac minh y nghia va bounds voi chuyen gia |
| `TFE Out flow SP` | SP | Setpoint Out flow cua TFE theo ten tag | Chua duoc cung cap | Gia tri tai dong `Set Time`; xac minh dong bo truoc khi dung | Co, theo brief; can xac minh y nghia va bounds voi chuyen gia |
| `TFE Production solids SP` | SP | Setpoint Production solids cua TFE theo ten tag | Chua duoc cung cap | Gia tri tai dong `Set Time`; xac minh dong bo truoc khi dung | Co, theo brief; can xac minh y nghia va bounds voi chuyen gia |
| `TFE Vacuum pressure SP` | SP | Setpoint Vacuum pressure cua TFE theo ten tag | Chua duoc cung cap | Gia tri tai dong `Set Time`; xac minh dong bo truoc khi dung | Co, theo brief; can xac minh y nghia va bounds voi chuyen gia |
| `TFE Steam pressure SP` | SP | Setpoint Steam pressure cua TFE theo ten tag | Chua duoc cung cap | Gia tri tai dong `Set Time`; xac minh dong bo truoc khi dung | Co, theo brief; can xac minh y nghia va bounds voi chuyen gia |
| `Extract tank Level` | Sensor/process | Muc Extract tank theo ten cot; chi tiet tag chua co | Chua duoc cung cap | Gia tri ghi tai `Set Time`; do tre/cach lay mau chua ro | Khong, gia tri do |
| `FFTE Discharge density` | Sensor/process | Density cua dong xa FFTE theo ten cot; chi tiet tag chua co | Chua duoc cung cap | Gia tri ghi tai `Set Time`; do tre/cach lay mau chua ro | Khong, gia tri do |
| `FFTE Discharge solids` | Sensor/process | Solids cua dong xa FFTE theo ten cot; chi tiet tag chua co | Chua duoc cung cap | Gia tri ghi tai `Set Time`; do tre/cach lay mau chua ro | Khong, gia tri do |
| `FFTE Feed flow rate PV` | PV/sensor | Gia tri do Feed flow rate cua FFTE | Chua duoc cung cap | Gia tri ghi tai `Set Time`; xac minh thoi diem sensor co san truoc khi du doan | Khong, gia tri do |
| `FFTE Feed solids PV` | PV/sensor | Gia tri do Feed solids cua FFTE | Chua duoc cung cap | Gia tri ghi tai `Set Time`; xac minh thoi diem sensor co san truoc khi du doan | Khong, gia tri do |
| `FFTE Heat temperature 1` | Sensor/process | Kenh nhiet do 1 cua FFTE theo ten cot | Chua duoc cung cap | Gia tri ghi tai `Set Time`; vi tri/cach do chua ro | Khong, gia tri do |
| `FFTE Heat temperature 2` | Sensor/process | Kenh nhiet do 2 cua FFTE theo ten cot | Chua duoc cung cap | Gia tri ghi tai `Set Time`; vi tri/cach do chua ro | Khong, gia tri do |
| `FFTE Heat temperature 3` | Sensor/process | Kenh nhiet do 3 cua FFTE theo ten cot | Chua duoc cung cap | Gia tri ghi tai `Set Time`; vi tri/cach do chua ro | Khong, gia tri do |
| `FFTE Production solids PV` | PV/sensor | Gia tri do Production solids cua FFTE | Chua duoc cung cap | Gia tri ghi tai `Set Time`; xac minh thoi diem sensor co san truoc khi du doan | Khong, gia tri do |
| `FFTE Steam pressure PV` | PV/sensor | Gia tri do Steam pressure cua FFTE | Chua duoc cung cap | Gia tri ghi tai `Set Time`; xac minh thoi diem sensor co san truoc khi du doan | Khong, gia tri do |
| `TFE Input flow PV` | PV/sensor | Gia tri do Input flow cua TFE | Chua duoc cung cap | Gia tri ghi tai `Set Time`; xac minh thoi diem sensor co san truoc khi du doan | Khong, gia tri do |
| `TFE Level` | Sensor/process | Muc TFE theo ten cot; chi tiet tag chua co | Chua duoc cung cap | Gia tri ghi tai `Set Time`; do tre/cach lay mau chua ro | Khong, gia tri do |
| `TFE Motor current` | Sensor/process | Dòng điện motor TFE theo tên cột | Chưa được cung cấp | Giá trị ghi tại `Set Time`; thiết bị/cách lấy mẫu chưa rõ | Không, giá trị đo |
| `TFE Motor speed` | Sensor/process | Toc do motor TFE theo ten cot | Chua duoc cung cap | Gia tri ghi tai `Set Time`; thiet bi/cach lay mau chua ro | Khong, gia tri do |
| `TFE Out flow PV` | PV/sensor | Gia tri do Out flow cua TFE | Chua duoc cung cap | Gia tri ghi tai `Set Time`; xac minh thoi diem sensor co san truoc khi du doan | Khong, gia tri do |
| `TFE Product out temperature` | Sensor/process | Nhiet do product out cua TFE theo ten cot | Chua duoc cung cap | Gia tri ghi tai `Set Time`; diem do chua ro | Khong, gia tri do |
| `TFE Production solids PV` | PV/sensor | Gia tri do Production solids cua TFE | Chua duoc cung cap | Gia tri ghi tai `Set Time`; xac minh thoi diem sensor co san truoc khi du doan | Khong, gia tri do |
| `TFE Production solids density` | Sensor/process | Density cua Production solids TFE theo ten cot | Chua duoc cung cap | Gia tri ghi tai `Set Time`; phuong phap/tag chua ro | Khong, gia tri do |
| `TFE Steam pressure PV` | PV/sensor | Gia tri do Steam pressure cua TFE | Chua duoc cung cap | Gia tri ghi tai `Set Time`; xac minh thoi diem sensor co san truoc khi du doan | Khong, gia tri do |
| `TFE Steam temperature` | Sensor/process | Nhiet do steam TFE theo ten cot | Chua duoc cung cap | Gia tri ghi tai `Set Time`; diem do chua ro | Khong, gia tri do |
| `TFE Tank level` | Sensor/process | Muc tank TFE theo ten cot | Chua duoc cung cap | Gia tri ghi tai `Set Time`; do tre/cach lay mau chua ro | Khong, gia tri do |
| `TFE Temperature` | Sensor/process | Nhiet do TFE theo ten cot; vi tri do chua ro | Chua duoc cung cap | Gia tri ghi tai `Set Time`; do tre/cach lay mau chua ro | Khong, gia tri do |
| `TFE Vacuum pressure PV` | PV/sensor | Gia tri do Vacuum pressure cua TFE | Chua duoc cung cap | Gia tri ghi tai `Set Time`; xac minh thoi diem sensor co san truoc khi du doan | Khong, gia tri do |

## Nhãn mục tiêu

`quality_class` là cột sinh ra từ provenance của tên file nguồn (`good.csv` -> `good`, `low bad.csv` -> `low_bad`, `high bad.csv` -> `high_bad`). Đây mới là cách gán nhãn trong file dữ liệu sau khi audit, không phải định nghĩa nghiệp vụ đã được xác nhận.

Phan loai hien tai:

- `good`: duoc tao tu cac dong trong `good.csv`.
- `low_bad`: được tạo từ các dòng trong `low bad.csv`; file nguồn không cung cấp quy trình đo lab, phương thức kiểm tra, ngưỡng hoặc logic nghiệp vụ.
- `high_bad`: duoc tao tu cac dong trong `high bad.csv`; file nguon khong cung cap tiep tuc dinh nghia nghiep vu.

Trạng thái: `APPROVED_WITH_CONDITIONS` (trong phạm vi đồ án học thuật COS40007; provenance đã được xác nhận cho 702/703 batch và được trình bày chi tiết tại [`quality_label_governance_theme3.md`](quality_label_governance_theme3.md)). Định nghĩa SOP phòng Lab ngoài nhà máy được ghi nhận là giới hạn dữ liệu (`NOT_AVAILABLE_IN_COURSE_DATASET`).

Batch `97_2020_06_25` là tập xung đột nhãn: xuất hiện trong cả `good.csv` và `low bad.csv`, với 36 dòng SP/PV giống nhau cho mỗi nhãn. `output_log.csv` ghi cả hai nhãn cho batch này nhưng không giải quyết xung đột. Hồ sơ dự án đã chốt quyết định chính thức **`QUARANTINE_UNRESOLVED`**: cách ly vĩnh viễn toàn bộ 72 dòng của batch này khỏi tập Train/Validation/Test; không biểu quyết, không suy nhãn từ mô hình và không dùng nhãn thay thế.

## Xác nhận cần bổ sung

Nguon xac nhan mac dinh phai la P&ID/tag list, historian export dictionary, operating procedure hoac chuyen gia quy trinh co tham quyen. Mot ban ghi xac nhan can ghi:

- ten cot du lieu;
- đơn vị vật lý và thang đo;
- tag historian neu co;
- thiết bị/vị trí/hướng tín hiệu;
- thoi diem du lieu san sang va latency;
- SP hay PV;
- control authority;
- operating bound đã duyệt và nguồn xác nhận;
- nguoi xac nhan, ngay, phien ban va ghi chu.

Register de dien va luu tai: `field_confirmation_register.csv`. Tat ca cot khong co bang chung nguon trong workspace deu co status `PENDING_VERIFICATION` hoac `DATA_DEFINED`, va khong duoc label `CONFIRMED` chi vi ten cot nghe hop ly.

## Định nghĩa cột dữ liệu

- `VYP batch`: metadata dinh danh batch; khong dung lam feature.
- `Part`: categorical process metadata; thoi diem co san va definition can xac nhan.
- `Set Time`: chuoi local time `dd/mm/YYYY H:mm` hoac `dd/mm/YYYY H:mm:ss`; timezone va DST status chua xac nhan.
- Cot ket thuc bang `SP`: theo ten hien co duoc coi la setpoint; khong xac nhan don vi/control authority.
- Cot con lai: process/PV/sensor theo ten hien co; khong co schema tag chinh thuc trong workspace.
- `quality_class`: label phai sinh tu file nguon; khong phai cot goc va khong co thu tu nghiep vu xac nhan.