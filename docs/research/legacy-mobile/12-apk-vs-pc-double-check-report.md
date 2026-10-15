# 12 — Báo Cáo Double-Check & Đối Chiếu Mã Nguồn: Bản Android APK vs Bản PC 120 FPS

> **Dự án:** Ragnarok X: Next Generation  
> **Ngày lập:** 2026-10-09  
> **Mục tiêu:** Ánh xạ mã nguồn C# từ `GameAssembly.dll` + `global-metadata.dat` (PC 120 FPS) và đối chiếu chéo (Double-check) với bản Android APK (`Assembly-CSharp.dll` tại `D:\CenNextWorkSpace\Rox`).

---

## 1. Kết Quả Ánh Xạ Mã Nguồn Bản PC 120 FPS

* **Kho mã nguồn mới trích xuất:** 👉 [`D:\CenNextWorkSpace\RoxPC\decompiled\`](file:///D:/CenNextWorkSpace/RoxPC/decompiled/) (Xem [README.md](file:///D:/CenNextWorkSpace/RoxPC/decompiled/README.md)).
* **Tổng số tệp C# đã sinh:** **3.973 classes (.cs)** phân bố trên **73 Namespaces**.
* **Cơ chế bóc tách:** Trích xuất trực tiếp từ 15.764 bản ghi `Il2CppTypeDefinition` trong `global-metadata.dat` v24 nguyên bản (Magic `0xfab11baf`).

---

## 2. Bảng Đối Chiếu Chéo (Double-Check Matrix)

| Hạng mục đối chiếu | Bản Android APK (`D:\CenNextWorkSpace\Rox`) | Bản PC 120 FPS (`D:\CenNextWorkSpace\RoxPC`) | Kết luận đối chiếu |
| :--- | :---: | :---: | :---: |
| **Giao thức Mạng (`NetworkManager`)** | `Dream.Game.NetworkManager` (Token `0x020007e5`) | `Dream.Game.NetworkManager` (Token `0x020007e7`) | **KHỚP 100%** (Cùng 51 methods, 21 fields) |
| **Mã hóa AES (`AESUtil`)** | `Crypt.AESUtil` (Token `0x02000553`) | `Crypt.AESUtil` (Token `0x02000555`) | **KHỚP 100%** (Cùng 3 methods) |
| **Bắt tay RSA (`RSAUtil`)** | `Crypt.RSAUtil` (Token `0x02000554`) | `Crypt.RSAUtil` (Token `0x02000556`) | **KHỚP 100%** (Cùng 3 methods, 1 field) |
| **Danh mục OpCodes (`MessageId`)** | `Cc.Thedream.Mmo.Protocal.MessageId` | `Cc.Thedream.Mmo.Protocal.MessageId` | **KHỚP 100%** (Trùng khớp 2.434+ OpCodes) |
| **Tổng số lớp Protobuf** | **257 lớp** trong `Cc.Thedream.Mmo.Protocal` | **257 lớp** trong `Cc.Thedream.Mmo.Protocal` | **KHỚP TUYỆT ĐỐI 257/257 LỚP** |
| **Tổng số lớp Thực thể Game** | **209 lớp** trong `Cc.Thedream.Mmo.Data` | **209 lớp** trong `Cc.Thedream.Mmo.Data` | **KHỚP TUYỆT ĐỐI 209/209 LỚP** |
| **Cầu nối xLua (`CSObjectWrap`)** | Có sẵn | **424 lớp Wrap** C# sang Lua | **ĐẦY ĐỦ 100%** |

---

## 3. So Sánh Chi Tiết Lớp Điều Khiển Mạng: `NetworkManager.cs`

Đối chiếu từng trường và từng phương thức của [`Dream.Game.NetworkManager.cs`](file:///D:/CenNextWorkSpace/RoxPC/decompiled/Dream/Game/NetworkManager.cs) giữa 2 phiên bản:

### 3.1 Khớp 21/21 Fields:
Cả hai bản đều chứa chính xác 21 biến trường dữ liệu theo cùng thứ tự:
1. `OnReceiveData`
2. `m_Authed`
3. `OnMessageAction`
4. `gameServer`
5. `m_GameCheckVersion`
6. `m_HostList`
7. `m_Connected`
8. `m_AESKey` *(Mảng byte khóa phiên AES)*
9. `requestId`
10. `sequenceId` *(Bộ đếm chống Replay ulong)*
11. `ActionMap`
12. `pack` *(Envelope gói tin Protobuf)*
13. `m_SendWithResponseQueue`
14. `msgPool`
15. `sendingTcpRequest`
16. `m_GameReconnect`
17. `m_NetTimeOut`
18. `m_NetMsgQueue`
19. `m_NetAuthTimeOut`
20. `token`
21. `serverTimestamp`

### 3.2 Khớp 51/51 Methods:
Các hàm gửi nhận cốt lõi đều giống hệt nhau:
* `AESKeyRequest()`: Gửi bắt tay RSA chứa khóa AES.
* `AuthRequest()`: Gửi xác thực token.
* `Send(int msgId)`: Gửi opcode.
* `Send(Struct_3552 msgId, Type_1441 body)`: Gửi kèm Protobuf payload (tự động đóng gói và mã hóa AES).
* `OnReceive(Type_3480 pack)`: Nhận và giải mã AES từ server.
* `processLuaCallback(Type_3480 pack)`: Bắn sự kiện sang máy ảo xLua.

---

## 4. Ý Nghĩa Đối Với Kỹ Thuật Tự Động Hóa (Automation Takeaways)

1. **Tính Tương Thích Hoàn Hảo (100% Code Reuse):**
   * Do cấu trúc Protobuf (257 classes), cấu trúc dữ liệu game (209 classes) và lớp mạng (`NetworkManager`) giữa Android và PC giống nhau 100%, **toàn bộ logic, OpCode, và script tự động hóa nhiệm vụ đã nghiên cứu trên bản Android APK đều áp dụng được nguyên vẹn 100% cho bản PC 120 FPS!**
2. **Không Cần Viết Lại Giao Thức:**
   * Không có bất kỳ thay đổi nào về giao thức mạng hay cấu trúc đóng gói gói tin giữa 2 nền tảng.
3. **Lợi Thế Tuyệt Đối Của Bản PC:**
   * Thay vì phải chạy trong môi trường giả lập Android nặng nề, ta dùng chính các hàm C#/Lua đã đối chiếu này để gọi trực tiếp trong tiến trình Windows x64 với tốc độ xử lý 120 FPS mượt mà.
