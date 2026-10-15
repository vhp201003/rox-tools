# Module 02: Hệ Thống Tinh Luyện & Cường Hóa (Equipment Refine & Upgrade)

Dữ liệu được trích xuất từ bảng cấu hình gốc: `data_equip_Refine`, `data_equip_RefineProtect`, `data_equip_UpgradeInherit`, `data_equip_SlotStrengthen`.

---

## 1. Ma Trận Xác Suất Tinh Luyện (Refine Probability Matrix)

Tỉ lệ được định nghĩa chi tiết theo từng cấp độ tinh luyện:

| Cấp Đích | Tỉ Lệ Thành Công (`upgrade_rate`) | Tỉ Lệ Giữ Nguyên (`keepgrade_rate`) | Tỉ Lệ Tụt Cấp (`downgrade_rate`) | Tỉ Lệ Vỡ Đồ (`break_rate`) | Chi Phí Zeny (`need_zeny`) | Điểm May Mắn (`need_luck`) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **+1** | **100.0%** | 0.0% | 0.0% | **0.0%** | 2,000 | 0 |
| **+2** | **50.0%** | 50.0% | 0.0% | **0.0%** | 2,000 | 8 |
| **+3** | **33.0%** | 67.0% | 0.0% | **0.0%** | 4,000 | 12 |
| **+4** | **25.0%** | 75.0% | 0.0% | **0.0%** | 4,000 | 16 |
| **+5** | **25.0%** | 55.0% | **25.0%** | **10.0%** | 10,000 | 32 |
| **+6** | **25.0%** | 40.0% | **25.0%** | **10.0%** | 10,000 | 48 |
| **+7** | **20.0%** | 40.0% | **25.0%** | **15.0%** | 20,000 | 80 |
| **+8** | **20.0%** | 40.0% | **25.0%** | **15.0%** | 20,000 | 120 |
| **+9** | **10.0%** | 45.0% | **30.0%** | **15.0%** | 40,000 | 200 |
| **+10** | **20.0%** | 35.0% | **30.0%** | **15.0%** | 40,000 | 320 |
| **+11** | **20.0%** | 30.0% | **30.0%** | **20.0%** | 100,000 | 500 |
| **+12** | **20.0%** | 30.0% | **30.0%** | **20.0%** | 100,000 | 770 |

---

## 2. Cơ Chế Bảo Hộ / Đá Thần Chúc (Pray Protection)

Trích xuất từ `data_equip_RefineProtect`:
* **Vật phẩm:** Đá Thần Chúc (`pray_material = 10422012`).
* **Hiệu lực bảo vệ:**
  * `break_rate = 0.0%` (Khử hoàn toàn rủi ro vỡ hỏng trang bị).
  * `downgrade_rate = 0.0%` (Khử hoàn toàn rủi ro bị rớt cấp).
* **Kết quả khi dùng bảo hộ:**
  * **25.0%** Thành công lên cấp mới (`pray_upgrade_rate = 25.0%`).
  * **75.0%** Giữ nguyên cấp độ hiện tại (`pray_keepgrade_rate = 75.0%`).

---

## 3. Hệ Thống Điểm May Mắn (Lucky Point Accumulator)

* **Cộng dồn:** Mỗi lần tinh luyện thất bại được hoàn trả `return_luck = 4` điểm.
* **Ngưỡng kích hoạt:** Khi người chơi tích lũy đủ số điểm `need_luck` quy định ở bảng trên (vd: 32 điểm ở +5, 80 điểm ở +7), game sẽ kích hoạt phần thưởng hỗ trợ may mắn hoặc chuyển đổi tỷ lệ.

---

## 4. Nâng Cấp Bậc (Upgrade Tier) & Kế Thừa (Inheritance)

### A. Nâng Cấp Bậc (Upgrade tại Lò Rèn)
* **Tỉ lệ thành công:** **100% THÀNH CÔNG**.
* **Nguyên lý:** Đủ số lượng đá đúc khoáng sản (Smelting) và Zeny theo bảng `data_EquipmentSmelting_EquipmentSmelting` là nâng cấp được (Tier I $\rightarrow$ Tier II $\rightarrow$ Tier III...).

### B. Quy Tắc Kế Thừa (Inheritance)
Trích xuất từ `data_equip_UpgradeInherit`:
* **Hình phạt tụt cấp Tinh Luyện (`reduceRefineLevel`):** Khi kế thừa sang trang bị khác bậc:
  $$\text{Cấp Refine Mới} = \text{Cấp Refine Cũ} - 2$$
  *(Cấp Tinh luyện luôn bị trừ đi 2 cấp).*
* **Đền bù đá hoàn trả:** Trả lại đá tinh luyện theo chuỗi quy đổi:
  `"3,4|4,4|5,4|6,4|7,8|8,16|9,64|10,128|11,256|12,512|13,1024|14,1024|15,1024"`

### C. Cường Hóa Ô Trang Bị (Slot Strengthen)
Trích xuất từ `data_equip_SlotStrengthen` (9.68 MB):
* Cường hóa **gắn theo Ô (Slot) của nhân vật**, không gắn vào trang bị. Thay đổi trang bị không làm mất cấp cường hóa.
* Tỉ lệ thành công: **100%**. Tiêu tốn Đá Cường Hóa và Zeny theo cấp số nhân.
