# 09 — Research Report: ROX 120 FPS PC 2.0 Client (Native Launcher & Architecture)

> **Date:** 2026-10-09  
> **Topic:** Bóc tách bản nâng cấp ROX 120 FPS PC 2.0 (Native Windows Launcher), nguyên nhân lỗi tải trang chủ và link tải trực tiếp (Direct CDN Link).

---

## 1. Executive Summary & Đính Chính Kỹ Thuật

* **Lịch sử phiên bản:**
  * **Giai đoạn trước (2023 – đầu 2025):** Bản "PC Client" đời đầu của ROX đúng là một OEM Android Emulator Wrapper (được đóng gói từ engine giả lập Android chạy ngầm).
  * **Giai đoạn hiện tại (ROX 120 FPS PC 2.0):** Nhà phát hành Nuverse / ByteDance đã chính thức nâng cấp và phát hành bộ cài **PC Launcher 2.0** chuyên dụng hỗ trợ **120 FPS Native**, mở khóa toàn màn hình thực thụ, khử răng cưa và tùy biến phím bấm PC.
* **Nguyên nhân chính xác không tải được từ Web:**
  * Nút "Download" trên trang `ragnarokx.com/windows` không phải là link tải tĩnh thông thường mà được điều khiển qua chuỗi API React động.
  * Nếu trình duyệt bật AdBlock, chặn Pop-up, hoặc chặn các script theo dõi (Facebook Pixel `fbq`, Google Analytics `gtag`), sự kiện tải file sẽ bị hủy ngang (*silent return*).
* **Link Tải Trực Tiếp (Direct CDN Link - Đã kiểm chứng 100%):**
  * **URL:** `https://lf16-ga18cdn-alisg.bytedgame.com/obj/lf-game-alisg/ga18/ROX_PC_Launcher.exe`
  * **Tệp:** `ROX_PC_Launcher.exe`
  * **Dung lượng:** 100,549,824 bytes (~95.89 MB)
  * **Trạng thái:** HTTP 200 OK (Akamai / ByteDance Cloud CDN SG)

---

## 2. Bóc Tách Cơ Chế Tải Của Trang Chủ `ragnarokx.com/windows`

Phân tích mã nguồn JavaScript `index.ce902b56.js` và `762.35c81870.js` của trang chủ ROX:

```javascript
// Chu trình kích hoạt tải file khi bấm nút 'Download' trên web:
1. Gọi API lấy link động:
   GET https://act.nvsgames.com/site/api/v2/picture/search?app_id=3402&language=en-US&website=85&channel=2&page=1&block=1
   => Trả về: url = "https://lf16-ga18cdn-alisg.bytedgame.com/obj/lf-game-alisg/ga18/ROX_PC_Launcher.exe"

2. Kích hoạt Tracking & Sự kiện DOM:
   window.fbq("track", "AddToWishlist");
   window.gtag("event", "click_download");
   var n = "RO_SEALauncher-wid-" + window.web_id + ".exe";
   var t = T + "?download=true&filename=" + n;
   var r = document.createElement("a");
   r.href = t;
   r.download = n;
   r.click();
```

### Tại sao người dùng thường bị lỗi đứng im khi bấm nút?
1. **Lỗi chặn Tracker:** Khi người dùng cài AdBlock/Brave Shields, các hàm `window.fbq` hoặc `window.gtag` ném ra lỗi hoặc bị chặn khiến hàm `click()` tải file không bao giờ được gọi.
2. **Lỗi chặn Pop-up (Chrome/Edge):** Trình duyệt hiện đại chặn các thẻ `<a download>` được tạo động bằng JavaScript nếu không có thao tác click trực tiếp từ người dùng.

---

## 3. Kiến Trúc Của Bản ROX 120 FPS PC 2.0

* **Tên Launcher:** `RO_SEALauncher.exe` / `ROX_PC_Launcher.exe`.
* **Cơ chế hoạt động:**
  * File launcher (~95.8 MB) sau khi tải về sẽ tiến hành tải toàn bộ gói tài nguyên game Windows (~10 GB - 36 GB theo khuyến nghị của NPH).
  * Bản 2.0 được tối ưu hóa đồ họa Direct3D / Vulkan giúp đạt mượt mà 120 FPS trên PC mà không bị giật lag khung hình do ảo hóa.
* **Khả năng can thiệp Automation (In-Process Hook trên PC 2.0):**
  * Với bản PC Launcher này, game chạy trực tiếp trong không gian bộ nhớ của Windows x64.
  * Ta có thể sử dụng Frida trên Windows:
    ```powershell
    frida -n "RO_SEALauncher.exe" -l hook.js
    # hoặc gắn trực tiếp vào tiến trình game chính sau khi launcher mở game
    ```
  * Hoặc sử dụng các thư viện hook native C++ (MinHook, EasyHook) để can thiệp trực tiếp mà không cần lớp trung gian ADB giả lập.
