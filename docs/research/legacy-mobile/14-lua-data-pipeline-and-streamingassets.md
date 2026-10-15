# 14 — Trinh Sát Chuyên Sâu: Cấu Trúc Bảng Dữ Liệu Lua & StreamingAssets PC 120 FPS

> **Dự án:** Ragnarok X: Next Generation (ROX PC 120 FPS)  
> **Ngày lập:** 2026-10-09  
> **Mục tiêu:** Bóc tách toàn bộ hệ thống AssetBundles, các bảng dữ liệu nghiệp vụ Lua dạng plaintext và cơ chế nạp tài nguyên trong `rox_Data\StreamingAssets\Windows`.

---

## 1. Executive Summary

Phân tích nhị phân và giải mã AssetBundles trong `rox_Data\StreamingAssets\Windows` mang lại các phát hiện mang tính bước ngoặt:

1. **Bảng Cấu Hình Dạng Plaintext Lua 100%:** Toàn bộ bảng dữ liệu kinh tế, nhiệm vụ, NPC và câu cá không hề bị mã hóa nhị phân độc quyền mà được lưu dưới dạng **bảng Lua thuần túy (Plaintext Lua Tables)** bên trong các TextAssets của Unity AssetBundles.
2. **Kê Khai Toàn Diện Trong `BundleList.txt`:** File index ánh xạ trực tiếp từ tên logic (`lua_data_data_0.bundle`, `lua_data_en.bundle`...) sang mã băm MD5 trên đĩa.
3. **Nắm Trọn Vẹn Dữ Liệu Nghiệp Vụ:**
   * NPC ID của toàn bộ Bảng Ủy Thác tại các thành phố lớn.
   * Danh mục nhiệm vụ có Bonus x2 trong `data_entrust_QuestSpecialPool`.
   * Toàn bộ 253 KB bảng yêu cầu vật phẩm của Đơn Hàng Hội trong `data_guild_guildOrder`.

---

## 2. Bản Đồ Tài Nguyên Trong `StreamingAssets`

```
RO_SEAGame\rox_Data\StreamingAssets\
│
├── Assembly-CSharp.dll.bytes (8.22 MB) ──► Bản build C# Assembly hot-update
├── Assembly-CSharp.dhao.bytes (77 bytes) ──► Checksum xác thực tính toàn vẹn
├── manifest.txt (48 bytes) ──────────────► Hash: 81AEEF4F1BD68019B8CB4DCBF6A9E8B5
│
└── Windows\ (Hơn 504 AssetBundles)
    ├── BundleList.txt (46.9 KB) ────────► Bảng chỉ mục ánh xạ toàn bộ Bundles
    │
    ├── c35e985f8f344e7e47defa872b12833d.bundle (4.79 MB) ──► lua_data_data_0
    │   ├── data_npc_NPC (6.15 MB) ─────────────► Toàn bộ thông số NPC trong game
    │   └── data_NpcGenerator_NpcGenerator ─────► Điểm spawn NPC và tọa độ map
    │
    ├── 5d68f4f1d1da5d907668021ebebd0688.bundle (4.13 MB) ──► lua_data_data_4
    │   ├── data_entrust_QuestBoard ────────────► Quy tắc Bảng Ủy Thác (Max 10 Q, Max 200%)
    │   └── data_entrust_QuestSpecialPool ──────► Bể nhiệm vụ thưởng Bonus x2
    │
    ├── 7b07a1d6938eb8892e45a74bcff508c3.bundle (10.7 MB) ─► lua_data_data_1
    │   ├── data_guild_guildOrder (253 KB) ─────► Toàn bộ yêu cầu nộp 8 đơn hàng Hội
    │   └── data_SnowFestival_IceFishing ───────► Dữ liệu minigame câu cá
    │
    └── 23d30c856130b1332cd84b6a180a0e34.bundle (6.91 MB) ──► lua_data_data_2
        ├── data_Fishing_Fishing ───────────────► Danh mục cá, mồi câu và điểm câu
        └── data_RecurringQuest_RecurringQuest ──► Danh mục nhiệm vụ tuần hoàn
```

---

## 3. Mổ Xẻ Chi Tiết Các Bảng Dữ Liệu Nghiệp Vụ Cốt Lõi

### 3.1 Bảng Ủy Thác: `data_entrust_QuestBoard`
Trích xuất từ TextAsset trong `5d68f4f1d1da5d907668021ebebd0688.bundle`:
```lua
return {
    [1] = {
        ["Id"] = 1,
        ["dailyMaximumAccept"] = 10,       -- Giới hạn nhận tối đa 10 Q mỗi ngày
        ["dailyMaximumRefresh"] = 10,      -- Tối đa 10 lần làm mới danh sách
        ["baseRewardPercentage"] = 100,    -- Thưởng cơ bản 100%
        ["maximumRewardPercentage"] = 200, -- Thưởng tối đa 200% (Full Bonus x2)
        ["rewardMinLevel"] = 30,           -- Cấp tối thiểu để mở tính năng
        ["entrustNpcId"] = {               -- Danh sách NPC Bảng Ủy Thác các thành phố:
            11101014,                      -- Prontera
            10101013,                      -- Izlude
            13101009,                      -- Geffen
            11801007,                      -- Morroc
            12101007,                      -- Payon
            14101007,                      -- Alberta
            16101008,                      -- Comodo
            17101010,                      -- Umbala
            18101010,                      -- Niflheim
            19101013,                      -- Glast Heim
            50101013, 51101013
        }
    }
}
```
* **Ứng dụng cho Tool:** Tool chỉ việc kiểm tra nhân vật đang ở map nào và gửi yêu cầu tương tác trực tiếp tới đúng `entrustNpcId` của thành phố đó.

---

### 3.2 Bể Nhiệm Vụ Thưởng Bonus x2: `data_entrust_QuestSpecialPool`
* Bảng này chứa danh sách các ID nhiệm vụ có đánh dấu **Bonus đặc biệt** (như nhóm ID `29001`, `29002`, `29050`, `29051`...).
* **Ứng dụng cho Tool:** Khi mở Bảng ủy thác, Tool đối chiếu danh sách Q hiện tại với bảng này để **ưu tiên chọn chính xác các Quest có Bonus x2**, giúp người dùng nhận trọn vẹn điểm kinh nghiệm và Zeny thưởng tối đa mà không bị lãng phí lượt nhận.

---

### 3.3 Đơn Hàng Hội (Guild Orders): `data_guild_guildOrder`
Trích xuất từ `7b07a1d6938eb8892e45a74bcff508c3.bundle` (kích thước 253 KB):
```lua
local table = {
    [1] = {
        ["Id"] = 1,
        ["ItemId"] = 10403012,             -- ID vật phẩm yêu cầu nộp
        ["PlayerLevel"] = { 15, 25 },      -- Khung cấp độ người chơi
        ["SubmitAmount"] = { 50 },         -- Số lượng vật phẩm cần nộp
        ["AidAward"] = { { ["amount"] = 20000, ["type"] = 1 } },
        ["SubmitAward"] = { { ["amount"] = 1, ["staticId"] = 10204103, ["type"] = 5 } },
        ["crystalOrder"] = 0
    },
    [2] = {
        ["Id"] = 2,
        ["ItemId"] = 10406802,
        ["PlayerLevel"] = { 15, 25 },
        ["SubmitAmount"] = { 50 },
        -- ...
    }
}
```
* **Ứng dụng cho Tool:** Tool đọc trước bảng này, quét hòm đồ nhân vật (`BagMgr`), nếu phát hiện có đủ vật phẩm sẽ tự động kích hoạt nộp ngay lập tức mà không cần người chơi phải mở giao diện tìm kiếm thủ công.

---

## 4. Ý Nghĩa Đối Với Kiến Trúc Tool Hoàn Chỉnh

1. **Tự động hóa hoàn toàn từ Dữ liệu gốc:** Chúng ta không cần hardcode bất kỳ ID vật phẩm hay NPC nào. Tool có thể đọc trực tiếp các bảng Lua này để cập nhật theo mọi sự kiện và bản vá của game.
2. **Khả năng Bơm Lệnh (Command Injection) qua Lua:** Vì game dùng xLua để chạy các bảng này, ta có thể dùng `luaL_dostring` của [`xlua.dll`](file:///D:/CenNextWorkSpace/RoxPC/RO_SEA/RO_SEAGame/rox_Data/Plugins/x86_64/xlua.dll) để đọc và ghi trực tiếp vào các biến toàn cục trong game.
