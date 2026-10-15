# Module 03: Hệ Thống Phụ Ma & Thuật Toán Pity (Enchantment System)

Dữ liệu được trích xuất từ bảng cấu hình gốc: `data_equip_EnchantmentRandom`, `data_equip_EnchantmentAttr`, `data_equip_EnchantmentAttrLock`.

---

## 1. Cơ Chế Thuật Toán: Bảo Hiểm Pity Counter & Trọng Số Ngẫu Nhiên

ROX không sử dụng xúc xắc ngẫu nhiên phẳng (Flat Random) mà sử dụng **Trọng số phân bổ kết hợp Bộ đếm bảo hiểm (Pity System)**:

| Cấp Thuộc Tính Hiện Tại (`propLv`) | Bộ Đếm Bảo Hiểm (`pityCounter`) | Dải Level Có Thể Ra (`randomRange`) | Trọng Số Xác Suất (`randomWeight`) | Tỉ lệ thực tế (%) |
| :---: | :---: | :---: | :---: | :---: |
| **Lv 0 $\rightarrow$ 1** | Không | `[1]` | `[1]` | **100% ra Lv 1** |
| **Lv 1 $\rightarrow$ 2** | **4 lần** | `[1, 2]` | `[1, 1]` | **50%** Lv 1 / **50%** Lv 2 |
| **Lv 2 $\rightarrow$ 3** | **6 lần** | `[1, 2, 3]` | `[23, 44, 33]` | 23% Lv 1 / 44% Lv 2 / **33% Lv 3** |
| **Lv 3 $\rightarrow$ 4** | **8 lần** | `[2, 3, 4]` | `[25, 50, 25]` | 25% Lv 2 / 50% Lv 3 / **25% Lv 4** |
| **Lv 4 $\rightarrow$ 5** | **8 lần** | `[3, 4, 5]` | `[25, 50, 25]` | 25% Lv 3 / 50% Lv 4 / **25% Lv 5** |
| **Lv 5 $\rightarrow$ 6** | **12 lần** | `[4, 5, 6]` | `[28, 55, 17]` | 28% Lv 4 / 55% Lv 5 / **17% Lv 6** |
| **Lv 6 $\rightarrow$ 7** | **16 lần** | `[5, 6, 7]` | `[30, 55, 15]` | 30% Lv 5 / 55% Lv 6 / **15% Lv 7** |

---

## 2. Nguyên Lý Vận Hành Pity Counter
1. Khi người chơi roll phụ ma thất bại (không tăng cấp thuộc tính), một biến đếm ẩn trên server sẽ tăng thêm +1.
2. Khi biến đếm chạm mốc `pityCounter`:
   * Lần roll tiếp theo **buộc phải trả về level cao nhất** trong `randomRange`.
   * Ví dụ ở Lv 2: Sau 6 lần xịt, lần thứ 7 chắc chắn 100% nhảy lên Lv 3.
3. Sau khi lên cấp thành công, bộ đếm Pity được reset về 0 cho cấp độ mới.

---

## 3. Phân Hệ Phụ Ma Theo Thành Phố (Enchant Pools)

Mỗi thành phố có đá phụ ma riêng gắn liền với mã định danh thư viện `libId`:

| Thành Phố | Loại Đá Phụ Ma | Nhóm Chỉ Số Đặc Trưng |
| :--- | :--- | :--- |
| **Prontera** | Đá Phụ Ma Prontera | Thuộc tính cơ bản (STR, AGI, VIT, INT, DEX, LUK) |
| **Morroc** | Đá Phụ Ma Morroc | Xuyên giáp vật lý (P.Pen), Xuyên giáp phép (M.Pen), Sát thương nguyên tố |
| **Geffen** | Đá Phụ Ma Geffen | Tấn công phép thuật (M.Atk), Giảm thời gian niệm phép (Variable/Fixed Cast Time) |
| **Payon** | Đá Phụ Ma Payon | Bạo kích (Crit), Kháng bạo (Crit Res), Sát thương bạo kích (Crit Dmg) |
| **Alberta** | Đá Phụ Ma Alberta | Tốc độ đánh (ASPD), Bỏ qua né tránh, Hút máu |
| **Izlude** | Đá Phụ Ma Izlude | Máu tối đa (Max HP), Giảm sát thương phần trăm |

---

## 4. Cơ Chế Khóa Dòng (Enchant Lock)

Trích xuất từ `data_equip_EnchantmentAttrLock`:
* Khi trang bị có nhiều dòng phụ ma, người chơi có thể khóa 1 hoặc 2 dòng tốt để tiếp tục roll dòng còn lại.
* **Chi phí tiêu hao:** Tiêu tốn số lượng Đá Khóa Phụ Ma tăng vọt theo cấp số cộng dựa trên số lượng dòng bị khóa.
