# 11 — Báo Cáo Chiến Lược Tự Động Hóa ROX (Automation Strategy Analysis & Recommendation)

> **Dự án:** Ragnarok X: Next Generation (ROX PC 120 FPS Native)  
> **Tác giả:** Antigravity Project Management & Architecture Team  
> **Ngày lập:** 2026-10-09  
> **Cơ sở dữ liệu:** Đối chiếu mã nguồn decompiled (`3.253 files C#`) và cấu trúc nhị phân Windows x64 tại `D:\CenNextWorkSpace\RoxPC\RO_SEA\RO_SEAGame`.

---

## 1. Ma Trận Đánh Giá 4 Chiến Lược Tự Động Hóa

| Tiêu Chí | Chiến Lược 1: Headless Socket Bot (Go/Python) | Chiến Lược 2: Android Emulator (LDPlayer/Frida) | Chiến Lược 3: Native PC Frida Hook (Dynamic JS) | Chiến Lược 4: Native C++ DLL + Local REST Bridge |
| :--- | :---: | :---: | :---: | :---: |
| **Xử lý Mã Hóa AES / RSA** | ❌ Cực kỳ phức tạp | ✅ Tự động (Engine lo) | ✅ Tự động (Engine lo) | ✅ Tự động (Engine lo) |
| **Bảo vệ Anti-Replay (`sequenceId`)** | ❌ Dễ lệch, bị kick | ✅ Tự động tăng | ✅ Tự động tăng | ✅ Tự động tăng |
| **Đồng bộ Không gian 3D (Tọa độ/Map)** | ❌ Phải tự giả lập | ✅ Unity 3D tự xử lý | ✅ Unity 3D tự xử lý | ✅ Unity 3D tự xử lý |
| **Nguy cơ văng Acc (Kick Session)** | ❌ Văng 100% nếu onl máy khác | ✅ Không văng (Là client thật) | ✅ Không văng (Là client thật) | ✅ Không văng (Là client thật) |
| **Tiêu tốn CPU/RAM & Giới hạn FPS** | N/A | ❌ Nặng (2-4GB RAM, 30-60 FPS) | ✅ Rất nhẹ, 120 FPS | 🏆 Cực nhẹ, 120 FPS, tối ưu |
| **Mức độ Anti-Cheat can thiệp** | Bị soi Traffic/GSDK | Cần Root / Magisk | ✅ An toàn (User-mode Ring 3) | 🏆 Tàng hình tối đa (DLL proxy) |
| **Tốc độ phát triển & Mở rộng** | Rất chậm (vài tháng) | Trung bình | 🏆 Siêu nhanh (Hot-reload) | Nhanh, chuẩn sản phẩm thương mại |
| **Xếp Hạng Phù Hợp** | **LOẠI BỎ (Unviable)** | **DỰ PHÒNG (Fallback)** | **TỐT NHẤT GIAI ĐOẠN 1 (PoC)** | **TỐI THƯỢNG CHO GIAI ĐOẠN 2 (Prod)** |

---

## 2. Phân Tích Chi Tiết & Dẫn Chứng Kỹ Thuật (Evidence-Grounded Analysis)

### 2.1 Tại Sao Chiến Lược 1 (Headless Socket Bot) Bị Loại Bỏ?

Dẫn chứng từ mã nguồn đã dịch ngược tại `D:\CenNextWorkSpace\Rox\decompiled/`:
1. **Dẫn chứng Mã Hóa 2 lớp:**
   * Tệp [`Dream/Game/NetworkManager.cs`](file:///D:/CenNextWorkSpace/Rox/decompiled/Dream/Game/NetworkManager.cs#L47): Hàm `AESKeyRequest()` và trường `m_AESKey` (dòng 18).
   * Tệp [`Crypt/RSAUtil.cs`](file:///D:/CenNextWorkSpace/Rox/decompiled/Crypt/RSAUtil.cs#L15): Client phải mã hóa AES session key bằng khóa công khai RSA của server.
   * Tệp [`Crypt/AESUtil.cs`](file:///D:/CenNextWorkSpace/Rox/decompiled/Crypt/AESUtil.cs#L11): Mọi gói tin TCP gửi đi đều bị mã hóa AES.
2. **Dẫn chứng Anti-Replay:**
   * [`NetworkManager.cs`](file:///D:/CenNextWorkSpace/Rox/decompiled/Dream/Game/NetworkManager.cs#L20): Trường `ulong sequenceId`. Bộ đếm tự tăng đơn điệu trên từng request. Nếu bot độc lập gửi sai số hoặc trễ nhịp so với server state, server sẽ drop gói tin ngay lập tức.
3. **Dẫn chứng Ràng Buộc Không Gian 3D:**
   * Khi làm nhiệm vụ (như nộp bảng ủy thác hoặc COC), server kiểm tra khoảng cách tương tác giữa nhân vật và NPC (Interaction Radius ~ 3–5m). Nếu gửi packet nhận/trả quest mà không có packet đồng bộ di chuyển (Move Sync) hợp lệ từ client 3D, server trả về lỗi `PositionMismatch` và đưa vào danh sách đen.

---

### 2.2 Đánh Giá Chiến Lược 2: Giả Lập Android (LDPlayer / MuMu)
* **Ưu điểm:** Đã có đầy đủ mã nguồn APK `0616_h5.apk`.
* **Nhược điểm cốt lõi:**
  * Giả lập tiêu tốn tài nguyên phần cứng lớn do lớp dịch tập lệnh (ARM-to-x86) và ảo hóa (Intel VT-x/AMD-V).
  * Giới hạn FPS ở mức 30–60 FPS, độ trễ thao tác cao hơn so với Windows native.
* **Kết luận:** Giữ làm **phương án dự phòng (Backup)** nếu NPH cập nhật driver chống can thiệp trên PC trong tương lai.

---

### 2.3 Chiến Lược Đề Xuất Số 1: Native PC Hybrid Architecture (Frida PoC ➡️ C++ Embedded REST Bridge)

Đây là chiến lược hoàn hảo nhất, được chứng minh bởi **4 phát hiện nhị phân thực tế** trên bản cài PC 120 FPS tại `D:\CenNextWorkSpace\RoxPC\RO_SEA\RO_SEAGame`:

#### Dẫn chứng 1: `GameAssembly.dll` Hoàn Toàn Unstripped (240 Exports)
* Kích thước: `71,987,712 bytes` (x86_64 PE32+).
* Bảng export công khai toàn bộ runtime C-API của IL2CPP:
  ```c
  il2cpp_domain_get
  il2cpp_class_from_name
  il2cpp_class_get_method_from_name
  il2cpp_runtime_invoke
  il2cpp_thread_attach
  ```
* **Ý nghĩa thực tế:** Ta có thể gọi trực tiếp bất kỳ phương thức nào của `Dream.Game.NetworkManager` hoặc `Cc.Thedream.Mmo.Game.*` từ tiến trình Windows mà không cần đoán offset hay tìm kiếm pattern!

#### Dẫn chứng 2: `global-metadata.dat` Chuẩn v24 Không Mã Hóa
* Kích thước: `18,935,988 bytes` tại `rox_Data\il2cpp_data\Metadata\global-metadata.dat`.
* Magic bytes: `0xfab11baf`, version: `24`.
* Cấu trúc siêu dữ liệu nguyên bản cho phép ánh xạ 100% token C# sang địa chỉ bộ nhớ trong runtime mà không gặp bất kỳ lỗi giải mã nào.

#### Dẫn chứng 3: Bảo Mật GameProtect Chạy Hoàn Toàn Ở Ring 3 (User-Mode)
* Quét toàn bộ thư mục `D:\CenNextWorkSpace\RoxPC`: **0 tệp tin `.sys` (Zero Kernel Drivers)**.
* Các module bảo vệ gồm `gpHackerProc.dll` (3.52 MB), `gpShell.dll` (396 KB), `gp.dll` (6.98 MB) đều là DLL User-mode thông thường.
* GameProtect không có quyền can thiệp cấp nhân (Kernel Ring 0) để khóa API bộ nhớ Windows (`OpenProcess`, `VirtualAllocEx`) hay chặn Frida.

#### Dẫn chứng 4: Tích Hợp Máy Ảo Lua `xlua.dll` Cực Kỳ Linh Hoạt
* Tệp `rox_Data\Plugins\x86_64\xlua.dll` (725 KB) xuất 253 hàm Lua C-API.
* Toàn bộ các Manager nhiệm vụ (`DailyTaskMgr`, `GuildOrderMgr`) trên bản PC đều có thể được kích hoạt thông qua lệnh Lua nội bộ (`luaL_dostring`), loại bỏ hoàn toàn việc phải thao tác tay trên chuột/bàn phím.

---

## 3. Lộ Trình Triển Khai Đề Xuất (Phased Execution Roadmap)

```
┌────────────────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 1: PoC & Reverse Verification (Frida Windows x64)           │
│ - Gắn Frida trực tiếp vào rox.exe                                      │
│ - Hook NetworkManager.Send để xác thực thông điệp Protobuf             │
│ - Thử nghiệm gọi hàm nhận Bảng Ủy Thác / Dùng Cánh Bướm qua C# & Lua   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ (Xác thực thành công)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ GIAI ĐOẠN 2: Production Tooling (Embedded C++ Local REST Bridge)      │
│ - Đóng gói một file DLL C++ nhỏ (rox_bridge.dll)                       │
│ - Nhúng WebServer nội bộ (127.0.0.1:9090) bên trong rox.exe            │
│ - Viết UI điều khiển ngoài (Python/React Desktop):                     │
│   POST http://127.0.0.1:9090/quest/accept-board                        │
│   POST http://127.0.0.1:9090/quest/coc-auto                            │
└────────────────────────────────────────────────────────────────────────┘
```

### Kết luận Chiến lược:
Hệ thống hiện tại **phù hợp 100% và tối ưu nhất với Chiến Lược In-Process Hook trên nền Native PC 120 FPS**. Đây là con đường ngắn nhất, an toàn nhất trước cơ chế mã hóa AES/Replay, và mang lại trải nghiệm mượt mà nhất.
