# Module 04: Các Phân Hệ Gameplay Cốt Lõi (Gameplay Subsystems)

Tài liệu chi tiết về các phân hệ trò chơi được định nghĩa trong `Cc.Thedream.Mmo.Protocal.*` và các controller trong `lua_lua.bundle`.

---

## 1. Phân Hệ Câu Cá (Fishing Subsystem)

### A. Luồng Gói Tin Mạng
1. **Bắt đầu câu:** Client gửi `ClientFishStartRequest (231)` kèm `spot_id` (vị trí bãi câu) và `bait_id` (loại mồi).
2. **Server xác nhận:** Server phản hồi `ToClientFishStartResponse (2457)`.
3. **Thu cần:** Sau khi mini-game kết thúc (hoặc bot canh đủ thời gian), client gửi `ClientFishEndRequest (232)`.
4. **Server trả thưởng:** Server gửi thông báo nhận vật phẩm cá/nguyên liệu vào túi đồ.

### B. Chế Độ Auto Câu Cá (Auto Fishing)
* Kích hoạt bằng `ClientAutoFishingStartRequest (410)`.
* Tự động gửi gói tin đổi mồi khi hết mồi: `ClientAutoFishingChangeBaitRequest (411)`.
* Server định kỳ gửi thông báo thời gian nhận cá tiếp theo: `ToClientNextAutoFishingRewardTimestampNotify (2557)`.
* Khi hết thể lực hoặc dừng câu: `ToClientAutoFishingFinishNotify (2558)`.

---

## 2. Phân Hệ Sàn Đấu Giá & Sạp Hàng (Economy & Market Subsystem)

### A. Sàn Đấu Giá (Auction / Exchange)
* **Tra cứu danh mục:** `ClientAuctionGetProductsSummaryRequest (42)`.
* **Xem chi tiết sản phẩm:** `ClientAuctionGetProductDetailRequest (41)`.
* **Mua ngay:** `ClientAuctionBuyRequest (43)`.
* **Đăng bán:** `ClientAuctionSellRequest (45)`.
* **Rút tiền bán hàng:** `ClientAuctionTakeTradeRecordMoneyRequest (53)`.

### B. Sạp Hàng Cá Nhân (Player Stalls)
* **Tra cứu giá thị trường sạp hàng:** `ClientSearchStallPriceRequest (319)`.
* **Mở sạp hàng:** `ClientStallOpenRequest (291)`.
* **Giao dịch mua hàng tại sạp:** `ClientStallTradeRequest (288)`.
* **Nhận doanh thu sạp:** `ClientStallGetTradeRewardRequest (289)`.

---

## 3. Phân Hệ Chiến Đấu & Quái Vật (Combat & AOI Entity System)

* **Class quản lý:** `Dream.Game.AvatarBattleManager`, `Dream.Game.BattleMapAOISystem`, `Dream.Game.BattleMapEntityManager`.
* **Cơ chế AOI (Area of Interest):**
  * Bản đồ game được chia thành các ô lưới (Grid cells).
  * Khi người chơi hoặc quái vật bước vào vùng quan sát (AOI radius), server phát gói tin thông báo xuất hiện: `ToClientEnterBattleNotify`.
  * Khi rời vùng: `ToClientLeaveBattleNotify`.
* **Tấn công & Kỹ năng:**
  * Client gửi `ClientCastSkillRequest (9)` kèm `skill_id`, `target_uid`, và `cast_position (X, Y, Z)`.
  * Server kiểm tra tầm đánh (Range check) và Cooldown trước khi phát gói tin sát thương.

---

## 4. Phân Hệ Nhiệm Vụ (Quest & Task Subsystem)

* **Bảng nhiệm vụ (Mission Board / Tavern Orders):**
  * Nhận nhiệm vụ: `ClientTaskAccept (15)` kèm `task_id`.
  * Cập nhật tiến độ: `ClientTaskUpdateStep (36)`.
  * Trả nhiệm vụ lấy thưởng: `ClientTaskFinish (16)`.
  * Hủy nhiệm vụ: `ClientTaskDiscard (35)`.
