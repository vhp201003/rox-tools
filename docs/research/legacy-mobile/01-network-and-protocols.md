# Module 01: Tầng Mạng & Bản Đồ Gói Tin (Network Protocol & OpCodes)

## 1. Tổng Quan Kiến Trúc Mạng
ROX kết hợp giữa **HTTPS REST (cho Xác thực & Thanh toán)** và **TCP Socket Thời gian thực (cho Gameplay)**.

* **Thư viện Socket:** `BGHotFix.Scripts.Core.AsyncSocketClient`, `NetClient`.
* **Cơ chế Hàng đợi:** `NetMsgRevQueue`, `NetGuardTimer`.
* **Cầu nối Scripting:** `XLua.CSObjectWrap.DreamGameNetworkManagerWrap`.
* **Serialization:** **Google Protocol Buffers (Protobuf)** thuộc namespace `Cc.Thedream.Mmo.Protocal.*`.

---

## 2. Luồng Xác Thực (Authentication Flow)
1. **Bước 1 (GSDK Login):** Client gửi request HTTPS tới ByteDance GSDK Gateway:
   * URL: `https://login-sg.bytegsdk.com/` (Singapore Gateway) hoặc `https://gsdk-sg.bytegsdk.com/`
   * Nhận về: `session_token`, `uid`, `server_gateway_ip`, `server_gateway_port`.
2. **Bước 2 (Socket Handshake):** Client mở kết nối TCP Socket tới `server_gateway_ip:port`.
3. **Bước 3 (Game Login):** Client gửi gói tin đăng nhập:
   * **OpCode:** `ClientLoginRequest = 2`
   * Server xác thực và trả về: `ToClientLoginResponse` kèm toàn bộ dữ liệu nhân vật.

---

## 3. Bản Đồ OpCodes Chính (Trích từ Master Enum `MessageId` - 2.434 Gói tin)

### A. Hệ thống & Kết nối (Core System)
| OpCode ID | Tên Packet | Hướng | Mô tả |
| :---: | :--- | :---: | :--- |
| **`1`** | `ClientPingRequest` | C $\rightarrow$ S | Gói tin nhịp tim (Keep-alive ping) |
| **`2`** | `ClientLoginRequest` | C $\rightarrow$ S | Đăng nhập session vào game server |
| **`4`** | `ClientRoleDataInitRequest` | C $\rightarrow$ S | Khởi tạo thông tin nhân vật |
| **`11`** | `ClientScenePrepareRequest` | C $\rightarrow$ S | Chuẩn bị tải dữ liệu bản đồ |
| **`17`** | `ClientRoleRevive` | C $\rightarrow$ S | Hồi sinh nhân vật tại chỗ hoặc về thành |
| **`34`** | `ClientRoleAttrRequest` | C $\rightarrow$ S | Truy vấn bảng chỉ số nhân vật |

### B. Di chuyển & Chiến đấu (Movement & Battle)
| OpCode ID | Tên Packet | Hướng | Mô tả |
| :---: | :--- | :---: | :--- |
| **`5`** | `ClientStartMoveRequest` | C $\rightarrow$ S | Bắt đầu di chuyển tới tọa độ đích |
| **`6`** | `ClientStopMoveRequest` | C $\rightarrow$ S | Dừng di chuyển tại tọa độ hiện tại |
| **`8`** | `ClientStopAttackRequest` | C $\rightarrow$ S | Dừng tự động tấn công |
| **`9`** | `ClientCastSkillRequest` | C $\rightarrow$ S | Tung chiêu thức / Đánh thường |
| **`10`** | `ClientCancelSkillRequest` | C $\rightarrow$ S | Hủy bỏ kỹ năng đang vận niệm |
| **`19`** | `ClientJumpRequest` | C $\rightarrow$ S | Hành động nhảy / né tránh |
| **`20`** | `ClientOnTeleporterRequest` | C $\rightarrow$ S | Bước vào cổng dịch chuyển bản đồ |

### C. Câu cá & Kỹ năng sống (Life Skills & Fishing)
| OpCode ID | Tên Packet | Hướng | Mô tả |
| :---: | :--- | :---: | :--- |
| **`231`** | `ClientFishStartRequest` | C $\rightarrow$ S | Bắt đầu thả cần câu tại bãi câu |
| **`232`** | `ClientFishEndRequest` | C $\rightarrow$ S | Thu cần câu / Hoàn tất mini-game |
| **`410`** | `ClientAutoFishingStartRequest` | C $\rightarrow$ S | Kích hoạt chế độ tự động câu cá |
| **`411`** | `ClientAutoFishingChangeBaitRequest` | C $\rightarrow$ S | Thay đổi loại mồi câu |
| **`412`** | `ClientAutoFishingEndRequest` | C $\rightarrow$ S | Dừng tự động câu cá |
| **`2457`** | `ToClientFishStartResponse` | S $\rightarrow$ C | Server chấp thuận bắt đầu câu |
| **`2557`** | `ToClientNextAutoFishingRewardTimestampNotify` | S $\rightarrow$ C | Thông báo thời điểm nhận cá tiếp theo |
| **`2558`** | `ToClientAutoFishingFinishNotify` | S $\rightarrow$ C | Kết thúc lượt câu cá tự động |

### D. Kinh tế, Sàn đấu giá & Sạp hàng (Economy & Market)
| OpCode ID | Tên Packet | Hướng | Mô tả |
| :---: | :--- | :---: | :--- |
| **`41`** | `ClientAuctionGetProductDetailRequest` | C $\rightarrow$ S | Xem chi tiết 1 vật phẩm trên sàn |
| **`42`** | `ClientAuctionGetProductsSummaryRequest` | C $\rightarrow$ S | Xem bảng tóm tắt hàng hóa trên sàn |
| **`43`** | `ClientAuctionBuyRequest` | C $\rightarrow$ S | Mua ngay vật phẩm trên sàn đấu giá |
| **`45`** | `ClientAuctionSellRequest` | C $\rightarrow$ S | Đăng bán vật phẩm lên sàn |
| **`46`** | `ClientAuctionCancelSellRequest` | C $\rightarrow$ S | Hủy niêm yết bán |
| **`288`** | `ClientStallTradeRequest` | C $\rightarrow$ S | Mua bán tại Sạp Hàng người chơi |
| **`291`** | `ClientStallOpenRequest` | C $\rightarrow$ S | Mở sạp hàng cá nhân |
| **`319`** | `ClientSearchStallPriceRequest` | C $\rightarrow$ S | Quét tra cứu giá thị trường sạp hàng |

### E. Tinh luyện & Phụ ma (Refine & Enchant)
| OpCode ID | Tên Packet | Hướng | Mô tả |
| :---: | :--- | :---: | :--- |
| **`39`** | `ClientEquipmentSlotStrengthenRequest` | C $\rightarrow$ S | Cường hóa ô trang bị |
| **`131`** | `ClientEquipmentRefineRequest` | C $\rightarrow$ S | Yêu cầu Tinh luyện trang bị |
| **`132`** | `ClientEquipmentRefineLevelSwapRequest` | C $\rightarrow$ S | Đổi cấp Tinh luyện giữa 2 trang bị |
| **`209`** | `ClientEnchantRequest` | C $\rightarrow$ S | Yêu cầu Phụ ma trang bị |
| **`210`** | `ClientEnchantmentLevelUpRequest` | C $\rightarrow$ S | Nâng cấp bậc dòng Phụ ma |
| **`216`** | `ClientUseBackupEnchantmentRequest` | C $\rightarrow$ S | Sử dụng bộ phụ ma dự phòng |
| **`2092`** | `ToClientEquipmentRefineResponse` | S $\rightarrow$ C | Server trả về kết quả Tinh luyện |
| **`2449`** | `ToClientEnchantResponse` | S $\rightarrow$ C | Server trả về kết quả Phụ ma |
| **`2487`** | `ToClientEquipRefineAoiResultNotify` | S $\rightarrow$ C | Broadcast kết quả tinh luyện xung quanh |

### F. Nhiệm vụ & Tổ đội (Quests & Parties)
| OpCode ID | Tên Packet | Hướng | Mô tả |
| :---: | :--- | :---: | :--- |
| **`15`** | `ClientTaskAccept` | C $\rightarrow$ S | Nhận nhiệm vụ mới |
| **`16`** | `ClientTaskFinish` | C $\rightarrow$ S | Hoàn thành và nhận thưởng nhiệm vụ |
| **`35`** | `ClientTaskDiscard` | C $\rightarrow$ S | Hủy nhiệm vụ |
| **`36`** | `ClientTaskUpdateStep` | C $\rightarrow$ S | Cập nhật bước tiến độ nhiệm vụ |
| **`21`** | `ClientCreateTeamRequest` | C $\rightarrow$ S | Tạo tổ đội mới |
| **`22`** | `ClientApplyForJoinTeamRequest` | C $\rightarrow$ S | Xin gia nhập tổ đội |
| **`24`** | `ClientLeaveTeamRequest` | C $\rightarrow$ S | Rời tổ đội |
| **`25`** | `ClientKickTeamMember` | C $\rightarrow$ S | Kích thành viên khỏi đội |
