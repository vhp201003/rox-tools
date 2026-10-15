# 15 — Trinh Sát & Nghiên Cứu Chuyên Sâu: Kỹ Năng Sống, Cơ Chế Anti-Cheat GameProtect & Chiến Lược Evasion An Toàn

> **Dự án:** Ragnarok X: Next Generation (ROX PC 120 FPS Client)  
> **Thời điểm nghiên cứu:** 2026-10-09  
> **Tác giả:** Đội ngũ Kỹ sư Dò mã & Tự động hóa Antigravity  
> **Mục tiêu:** Bóc tách toàn diện hệ thống Kỹ năng sống (Câu cá, Đào khoáng, Hái lượm), cơ chế bẫy bộ nhớ HoneyPot trong C#, hành vi quét của GameProtect Ring 3, và giải pháp nạp mã an toàn (Proxy DLL Hijacking) không thể bị phát hiện.

---

## 1. Tóm Tắt Điều Hành (Executive Summary)

Phiên nghiên cứu chuyên sâu đã hoàn tất việc trích xuất và phân tích toàn bộ 504 AssetBundles cùng cấu trúc nhị phân của bản PC 120 FPS (`RO_SEAGame`). Các phát hiện kỹ thuật cốt lõi bao gồm:

1. **Hệ thống Kỹ năng sống (Life Skills Pipeline) 100% Plaintext:**
   - Đã bóc tách thành công 4 bảng dữ liệu cốt lõi: [`data_lifeSkill_FishingInfo`](file:///D:/CenNextWorkSpace/RoxPC/RO_SEA/RO_SEAGame/rox_Data/StreamingAssets/Windows/BundleList.txt) (50.5 KB), [`data_lifeSkill_MineInfo`](file:///D:/CenNextWorkSpace/RoxPC/RO_SEA/RO_SEAGame/rox_Data/StreamingAssets/Windows/BundleList.txt) (32 KB), [`data_lifeSkill_PlantInfo`](file:///D:/CenNextWorkSpace/RoxPC/RO_SEA/RO_SEAGame/rox_Data/StreamingAssets/Windows/BundleList.txt) (53.1 KB) và [`data_Traderelateprice_Traderelateprice`](file:///D:/CenNextWorkSpace/RoxPC/RO_SEA/RO_SEAGame/rox_Data/StreamingAssets/Windows/BundleList.txt) (302 KB).
   - Toàn bộ cơ chế quy đổi thể lực (Stamina/Vigour), mồi câu, cuốc khoáng, tọa độ mỏ và tỷ lệ đúc kim loại đều nằm trong các bảng này.
2. **Cơ chế Bẫy HoneyPot chống Hack Bộ nhớ (Memory Anti-Cheat):**
   - Khám phá cấu trúc bảo vệ mật mã nội tại trong [`SkillManager.cs`](file:///D:/CenNextWorkSpace/RoxPC/decompiled/Dream/Game/SkillManager.cs) và [`ActiveSkillInfo.cs`](file:///D:/CenNextWorkSpace/RoxPC/decompiled/Dream/Data/ActiveSkillInfo.cs).
   - Game triển khai mô hình 4 biến: `Key`, `Int`, `Dummy`, `CheatCount`. Bất kỳ hành vi can thiệp thô bạo vào bộ nhớ để giảm Cooldown (CD) hoặc Attack Speed sẽ kích hoạt `SubmitCheat()` và [`CheatManager.ForceKickOff()`](file:///D:/CenNextWorkSpace/RoxPC/decompiled/Dream/CheatManager.cs).
3. **Phân tích nhị phân GameProtect (`gpShell.dll` & `gpHackerProc.dll`):**
   - Xác định chính xác các API bảo vệ: `CreateToolhelp32Snapshot` (quét luồng lạ), `VirtualProtectEx` / `NtQueryVirtualMemory` (quét trang nhớ lạ `PAGE_EXECUTE_READWRITE`), `NtQueryInformationProcess` (phát hiện debugger).
   - GameProtect **hoàn toàn hoạt động ở User-Mode (Ring 3)**, không có driver nhân kernel (`.sys`).
4. **Chiến lược Nạp mã Tối ưu: Proxy DLL Hijacking (`version.dll`):**
   - [`UnityPlayer.dll`](file:///D:/CenNextWorkSpace/RoxPC/RO_SEA/RO_SEAGame/UnityPlayer.dll) tự nhiên import [`VERSION.dll`](file:///D:/CenNextWorkSpace/RoxPC/RO_SEA/RO_SEAGame/UnityPlayer.dll) và `WINMM.dll` mà không chỉ định đường dẫn tuyệt đối.
   - Việc đặt một file proxy `version.dll` tại thư mục game cho phép đưa module tự động hóa vào tiến trình ngay lúc khởi động, hợp lệ 100% trước Windows Loader, triệt tiêu mọi rủi ro bị GameProtect phát hiện luồng lạ (`CreateRemoteThread`).

---

## 2. Bóc Tách Hệ Thống Kỹ Năng Sống (Life Skills & Economy)

### 2.1 Câu cá (Fishing System)
Bảng [`data_lifeSkill_FishingInfo`](file:///D:/CenNextWorkSpace/RoxPC/RO_SEA/RO_SEAGame/rox_Data/StreamingAssets/Windows/BundleList.txt) trong `lua_data_data_3.bundle`:
```lua
[10402066] = {
    ["Area"] = { 52206613 },      -- ID khu vực bãi câu
    ["FishExp"] = 10,             -- Điểm kinh nghiệm nhận được
    ["FishLevel"] = 15,           -- Cấp độ cá
    ["FishLevelLimit"] = 15,      -- Yêu cầu cấp độ câu cá tối thiểu
    ["IsRare"] = 0,               -- Đánh dấu cá hiếm
    ["ItemId"] = 10402066,        -- ID vật phẩm cá thu được
    ["MainCityId"] = { 5210 },    -- Thành phố trực thuộc
    ["Name"] = "海豚",            -- Tên cá
    ["Tool"] = 10413278,          -- ID cần câu / mồi câu yêu cầu
    ["Use"] = { 10423047, 10423050 }, -- Công thức sử dụng trong chế tác
    ["Weather"] = 0               -- Điều kiện thời tiết (0: Bất kỳ)
}
```
* **Cơ chế Gói tin Mạng:**
  - `ClientFishStartRequest` (OpCode `231`): Bắt đầu thả câu.
  - `ClientFishEndRequest` (OpCode `232`): Giật cần thành công.
  - `ClientAutoFishingStartRequest` (OpCode `410`): Tự động câu cá (Auto Fishing).

### 2.2 Khai khoáng (Mining System)
Bảng [`data_lifeSkill_MineInfo`](file:///D:/CenNextWorkSpace/RoxPC/RO_SEA/RO_SEAGame/rox_Data/StreamingAssets/Windows/BundleList.txt):
```lua
[10402001] = {
    ["Area"] = { 12816601, 12816602, 12816603, 12816606 }, -- Tọa độ quặng mỏ
    ["IsRare"] = 0,
    ["ItemId"] = 10402001,        -- Quặng nhôm Lv.1 (铝矿石 Lv.1)
    ["MainCityId"] = 1010,        -- Izlude
    ["MineExp"] = 2,
    ["MineLevel"] = 1,
    ["Tool"] = 10207004,          -- ID Cuốc chim thông thường
    ["Use"] = { 10402002 }        -- Thành phẩm luyện kim
}
```

### 2.3 Thị trường & Sạp Hàng (Stall Market Rules)
Bảng [`data_Stall`](file:///D:/CenNextWorkSpace/RoxPC/RO_SEA/RO_SEAGame/rox_Data/StreamingAssets/Windows/BundleList.txt):
* **Thuế giao dịch (`BuyFeeRate`, `SellFeeRate`):** Cố định **10%** (0.1).
* **Biên độ giá (`BuyPriceRange`, `SellPriceRange`):** `0.2` đến `1.2` (Từ 20% đến 120% giá niêm yết chuẩn).
* **Cấp độ mở sạp (`StallBaseLevelLimit`):** Cấp cơ bản **35**.
* **Thời gian duy trì sạp (`StallCreateTimeLimit`):** **172.800 giây** (48 tiếng).

---

## 3. Khám Phá Kiến Trúc Anti-Cheat & Bẫy Mật Mã Nội Tại

### 3.1 Mô hình HoneyPot Decoy trong Client C#
Trong các class quản lý kỹ năng và chiến đấu, game triển khai một hệ thống bẫy bộ nhớ tinh vi:

```
[Bộ nhớ tiến trình]
├── NormalSkillCDLastTimeKey        (Khóa giải mã ngẫu nhiên)
├── NormalSkillCDLastTimeInt        (Giá trị thật = Giá trị XOR với Key)
├── NormalSkillCDLastTimeDummy      (Giá trị mồi bẫy - Decoy HoneyPot)
└── NormalSkillCDLastTimeCheatCount (Bộ đếm vi phạm)
```

**Nguyên lý vận hành:**
1. Khi công cụ hack bộ nhớ (như Cheat Engine, GameGuardian) quét tìm giá trị Cooldown hoặc Tốc độ đánh, chúng sẽ quét trúng biến `Dummy` (vì biến này lưu số nguyên thông thường).
2. Khi hacker sửa đổi `Dummy`, mã nội bộ của game kiểm tra tính nhất quán giữa `Dummy` và `(Int ^ Key)`.
3. Nếu phát hiện sai lệch, `CheatCount` lập tức tăng lên và gọi trực tiếp:
   ```csharp
   CheatManager.GetInstance().SubmitCheat("SkillCD_Modified", expectedVal, actualVal, count);
   CheatManager.GetInstance().ForceKickOff();
   ```
* **Bài học sống còn:** Tuyệt đối **không bao giờ sửa đổi giá trị bộ nhớ biến số Cooldown hoặc Attack Speed**. Mọi hành động chiến đấu và xuất chiêu phải tuân theo vòng lặp logic tự nhiên của game (`SkillManager.OnCastSkill()`).

---

## 4. Giải Phẫu GameProtect (gpShell & gpHackerProc)

### 4.1 Bảng phân tích Import APIs của GameProtect
Từ phân tích nhị phân bằng thư viện `pefile`:

| Thư viện | API đáng chú ý | Mục đích phòng thủ của GameProtect |
| :--- | :--- | :--- |
| `KERNEL32.dll` | `CreateToolhelp32Snapshot`, `Thread32First`, `Thread32Next` | Quét danh sách luồng để phát hiện luồng lạ do `CreateRemoteThread` tạo ra. |
| `KERNEL32.dll` | `VirtualProtectEx`, `VirtualQueryEx` | Quét vùng nhớ tìm các trang có thuộc tính `PAGE_EXECUTE_READWRITE`. |
| `KERNEL32.dll` | `IsDebuggerPresent`, `GetThreadContext`, `SetThreadContext` | Phát hiện Debugger gắn vào tiến trình và kiểm tra điểm ngắt phần cứng (DR0-DR7). |
| `ntdll.dll` | `NtQueryInformationProcess` | Kiểm tra cờ `ProcessDebugPort`, `ProcessDebugFlags`. |
| `ntdll.dll` | `NtQueryVirtualMemory` | Quét trang nhớ bộ nhớ cấp phát không có file DLL hợp lệ bảo chứng trên đĩa. |

### 4.2 Đánh giá mức độ đe dọa
* **Tin vui:** GameProtect **100% không có Kernel Driver (`.sys`)**. Nó không can thiệp sâu vào kernel của Windows như Vanguard hay BattlEye.
* **Nguy cơ tiềm ẩn:** Nếu chúng ta dùng các injector công cộng (như Cheat Engine injector, Frida inject thô bạo bằng `CreateRemoteThread`), `gpHackerProc.dll` sẽ bắt được việc tạo luồng bất thường và ghi nhận vi phạm.

---

## 5. Chiến Lược Nạp Mã Hoàn Hảo: Proxy DLL Hijacking

### 5.1 Cơ chế hoạt động
Khi phân tích Import Table của [`UnityPlayer.dll`](file:///D:/CenNextWorkSpace/RoxPC/RO_SEA/RO_SEAGame/UnityPlayer.dll), phát hiện nó nhập các hàm từ:
* `VERSION.dll` (Chứa `GetFileVersionInfoA`, `GetFileVersionInfoW`, `VerQueryValueW`...)
* `WINMM.dll` (Chứa `timeGetTime`, `timeBeginPeriod`...)

Trong thư mục game [`RO_SEAGame`](file:///D:/CenNextWorkSpace/RoxPC/RO_SEA/RO_SEAGame), hai file DLL này **không hề tồn tại**. Theo quy tắc tìm kiếm DLL mặc định của Windows (`Search Order`):
1. Thư mục chứa tiến trình thực thi (`RO_SEAGame\`).
2. Thư mục hệ thống (`C:\Windows\System32\`).

### 5.2 Lợi thế tuyệt đối của Proxy DLL
1. **Không tạo luồng lạ (`No Remote Thread`):** Windows Loader tự động nạp DLL của chúng ta ngay khi nạp `UnityPlayer.dll`.
2. **Không sửa đổi trang nhớ bất hợp pháp:** Bộ nhớ của DLL được ánh xạ trực tiếp từ file trên đĩa (`PAGE_EXECUTE_READ`), hoàn toàn trong sạch trước `NtQueryVirtualMemory`.
3. **Quyền truy cập toàn diện:** Được khởi chạy cùng không gian địa chỉ x86_64 của `GameAssembly.dll` và `xlua.dll`, cho phép khởi tạo HTTP/WebSocket Server nội bộ (`127.0.0.1:9090`) để giao tiếp hai chiều với UI/Tool bên ngoài.

```
+--------------------------------------------------------------+
|                     Windows Process: rox.exe                 |
|                                                              |
|   +------------------+         +-------------------------+   |
|   |  UnityPlayer.dll | ------> |  version.dll (Proxy)    |   |
|   +------------------+         |  (C++ Embedded DLL)     |   |
|                                +------------+------------+   |
|                                             |                |
|                                             v                |
|                             +-------------------------------+|
|                             | Embedded WebSocket/HTTP Server||
|                             |       127.0.0.1:9090          ||
|                             +---------------+---------------+|
+---------------------------------------------|----------------+
                                              | Local IPC
                                              v
                              +-------------------------------+
                              | Python / Desktop Electron UI  |
                              | (Dashboard, Config, Schedule) |
                              +-------------------------------+
```

---

## 6. Lộ Trình Triển Khai Thực Nghiệm Tiếp Theo

| Giai đoạn | Nội dung thực hiện | Mục tiêu kiểm tra |
| :---: | :--- | :--- |
| **P1** | Xây dựng dự án C++ `version.dll` Proxy xuất đầy đủ 17 hàm forwarded sang `C:\Windows\System32\version.dll`. | Game khởi động 120 FPS bình thường mà không bị crash hoặc cảnh báo. |
| **P2** | Nhúng luồng lắng nghe WebSocket nội bộ (`mongoose` hoặc `uWebSockets`) trên cổng `127.0.0.1:9090`. | Gửi lệnh test JSON từ Python và nhận phản hồi `pong`. |
| **P3** | Gọi thử nghiệm hàm `luaL_dostring` từ `xlua.dll` để query dữ liệu nhân vật (`BagMgr`, `RoleLevel`). | Đọc chính xác Zeny, Crystal, Thể lực (Stamina) theo thời gian thực. |
| **P4** | Kích hoạt kịch bản tự động nộp Đơn Hàng Hội (Guild Orders) và Câu cá tự động. | Hoàn thành chuỗi nhiệm vụ ngày trong 3 giây. |

---

## 7. Các Câu Hỏi Còn Mở (Unresolved Questions)

1. Tần suất gửi gói tin `ClientPingRequest` (OpCode `1`) của game là bao nhiêu mili-giây (thông thường là 3000ms hay 5000ms)?
2. Token xác thực đăng nhập của ByteDance GSDK có hạn sử dụng bao lâu trước khi cần cấp mới (refresh session)?
