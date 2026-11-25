# Cơ sở học thuật và đề xuất quy trình phê duyệt SP

## Kết luận

Các bài báo đáng tin cậy hỗ trợ **phương pháp kiểm soát evaporator và dạng ràng buộc**, nhưng không cung cấp operating bounds hợp lệ cho dây chuyền Vegemite cụ thể. Không được chuyển công nghệ hoặc range của một nghiên cứu qua nhà máy này.

Vì vậy, “expert-approved bound” hợp lệ phải đến từ P&ID/tag list, PLC/DCS limits, operating procedure và sign-off của process expert. Literature được dùng để:

- xác định các group variable có quan hệ điều khiển;
- yêu cầu constraint-aware control;
- đưa fouling/minimum-wetting và model mismatch vào risk gate;
- tránh dùng observed extrema làm giới hạn an toàn;
- yêu cầu xác minh sau khi thay đổi SP trên pilot/controlled trial.

## Nguồn học thuật có tính chính thống

### Evaporator thực phẩm và thiết bị tương tự

1. Zhang Y, Munir MT, Udugama I, Yu W, Young BR. *Modelling of a milk powder falling film evaporator for predicting process trends and comparison of energy consumption*. Journal of Food Engineering. 2018;225:26-33. DOI: 10.1016/j.jfoodeng.2018.01.016. Tính hợp lệ: mô hình falling-film evaporator thực phẩm nhiều effect; không cung cấp bound Vegemite cụ thể.

2. Silveira ACP et al. *Pilot-scale investigation of effectiveness of evaporation of skim milk compared to water*. Dairy Science & Technology. 2013;93:537-549. DOI: 10.1007/s13594-013-0138-1. Tính hợp lệ: dữ liệu pilot thực phẩm dưới vacuum, chênh lệch behavior của milk versus water. Không chứng minh range cho TFE/FFTE.

3. Cyklis P. *Effect of fouling on falling film evaporator performance in industrial conditions of fruit juice concentrate production*. Journal of Food Engineering. 2022;317:110884. DOI: 10.1016/j.jfoodeng.2021.110884. Tính hợp lệ: fouling làm thay đổi heat-transfer/performance trong điều kiện công nghiệp. Hỗ trợ requirement theo dõi fouling và ràng buộc vận hành theo trạng thái equipment.

4. Morison KR, Worth QAG, O'Dea NP. *Minimum Wetting and Distribution Rates in Falling Film Evaporators*. Food and Bioproducts Processing. 2006;84(C4):302-310. DOI: 10.1205/fbp06031. Tính hợp lệ: film break-up/minimum wetting là giới hạn vật lý quan trọng. Không thể dùng số liệu ngành khác làm bound nhà máy.

5. Paramalingam S, Winchester J, Marsh C. *On the Fouling of Falling Film Evaporators Due to Film Break-Up*. Food and Bioproducts Processing. 2000;78(C4):79-84. DOI: 10.1205/096030800532770. Tính hợp lệ: liên kết film break-up với fouling/degradation.

### Điều khiển và constraint-aware control

6. Hofmann J, Ponomarev A, Hagenmeyer V, Gröll L. *A new multivariable control concept for the falling film evaporator process*. Journal of Process Control. 2021;106:72-83. DOI: 10.1016/j.jprocont.2021.08.015. Tính hợp lệ: multivariable control, disturbance rejection, decoupling và constraint-aware operating state. Nguồn này là basis kỹ thuật để yêu cầu hard/soft constraints; không cung cấp hard limit Vegemite.

7. Van Wijck MPCM, Quaak P, van Haren JJ. *Multivariable supervisory control of a four-effect falling-film evaporator*. Food Control. 1994;5:83-89. DOI: 10.1016/0956-7135(94)90090-6. Tính hợp lệ: multivariable supervisory control trong falling-film evaporator. Hỗ trợ coi SP/PV là hệ liên kết, không xếp hạng từng SP độc lập.

8. *Modern process control techniques in the production of dried milk products – a review*. Le Lait. 2005;85:37-46. DOI: 10.1051/lait:2005021. Tính hợp lệ: review process control cho dairy concentration/drying. Hỗ trợ thiết kế model, controls and process-state awareness. Tác giả cụ thể nên được xác nhận lại trên trang publisher trước khi dùng trong bibliography chính thức.

### Prescriptive analytics và causal limits

9. Bertsimas D, Kallus N. *From Predictive to Prescriptive Analytics*. Management Science. 2020;66(3):1025-1044. DOI: 10.1287/mnsc.2018.3253. Tính hợp lệ: framework phân biệt prediction và prescription/decision.

10. Elmachtoub AN, Grigas P. *Smart 'Predict, then Optimize'*. Management Science. 2022;68(1):9-26. DOI: 10.1287/mnsc.2020.3922. Tính hợp lệ: objective và constraints phải được chọn riêng cho optimization.

11. Pearl J. *Causal Inference in Statistics: An Overview*. Statistics Surveys. 2009;3:96-146. DOI: 10.1214/09-SS057. Tính hợp lệ: lý do không coi correlation SP-quality là causal effect.

## Đề xuất approval policy hợp lý

### 1. Bắt buộc cho mọi bound

Expert xác nhận từng field bằng P&ID/tag list hoặc approved operating manual:

- unit và scale;
- tag historian exact;
- normal operating range;
- hard equipment limit;
- startup/shutdown-specific limit nếu khác;
- control authority;
- slew-rate/deadband;
- fouling/cleaning state;
- Part-dependent range nếu có;
- source, approver, date và revision.

Observed ranges trong `reports/setpoint_readiness/observed_sp_ranges.csv` chỉ được dùng làm model support/domain audit, không được dùng làm approved bound.

### 2. Hai loại range cần tách rõ

- **Hard operating envelope:** không được đề xuất ngoài vì có thể vi phạm safety/equipment/quality/legal constraint.
- **Model recommendation envelope:** range nhỏ hơn hard envelope để đảm bảo input gần miền data/model validation. Đây không thay thế hard envelope.

Candidate SP chỉ được sinh khi nằm trong giao của hai envelope và dữ liệu ở trạng thái process tương thích.

### 3. Phạm vi start-up khuyến nghị

Do model hiện tại có macro-F1 validation 0.4793 và low_bad recall 0.0495, hệ thống chưa đủ để đưa ra autonomous/SP operator recommendation. Thử nghiệm recommendation chỉ được chạy ở mode:

- advisory-only;
- rank within approved bounds;
- one change at a time;
- show current SP, candidate SP, delta, model score and uncertainty;
- require human approval;
- log approval/rejection;
- no DCS/PLC write.

### 4. Gate đào tạo và đánh giá

Không khóa test result trước khi:

- all 7 SP tags được confirm;
- units and control authority được confirm;
- hard bounds được sign-off;
- model gate và probability calibration được duyệt;
- domain shift and low_bad recall được xem xét;
- expert xác nhận current process state;
- pilot/controlled trial plan được approved.

### 5. Đề xuất số candidate steps

Trong module demo, cách hợp lý là expert cấu hình step grid, ví dụ 3-5 candidate points trên từng SP. Không hard-code phần trăm hoặc mặc định 10% step. Mỗi step phải:

- nằm trong hard bound;
- nằm trong model support;
- tuân thủ slew-rate;
- được expert approve;
- tách startup, steady-state và cleaning modes.

## Điều đáng giá để expert ký

Expert nên ký một trong ba quyết định:

1. `APPROVED`: bounds đủ căn cứ, có source/revision và đủ điều kiện để mở advisory ranking.
2. `APPROVED_WITH_CONDITIONS`: bounds chỉ áp dụng theo Part, operating mode hoặc cleaning state.
3. `NOT_APPROVED`: thiếu unit/tag/equipment/process authority hoặc chưa có trial evidence.

Không ký `APPROVED` dựa riêng trên min/max trong CSV hoặc model accuracy.
