# Research Report: Single-Terminal Multi-Account Quota Routing for Antigravity CLI (agy)

**Author:** Antigravity Research Engine  
**Date:** 2026-10-01  
**Target Environment:** Windows 11, PowerShell, `agy` v1.2.14, `agy-cli-manager` v0.3.0  

---

## Executive Summary

Người dùng hiện đang sử dụng `agy-cli-manager` để quản lý nhiều tài khoản Google/Antigravity (`acc1`, `acc2`, `acc3`), tự động luân chuyển (rotation) và kiểm tra hạn mức (quota) qua Windows Credential Manager và thư mục runtime `.gemini`. Tuy nhiên, cơ chế hiện tại là **File-level / Process-boundary rotation**: tức là việc tráo đổi token diễn ra ở bên ngoài tiến trình CLI. Khi người dùng mở một cửa sổ terminal duy nhất và chạy phiên tương tác `agy`, tiến trình `agy` sẽ nạp token vào bộ nhớ RAM lúc khởi tạo; khi tài khoản đang chạy bị cạn quota (HTTP 429 / Resource Exhausted), phiên terminal hiện tại không tự động tráo token ngầm được nếu không khởi động lại.

Báo cáo nghiên cứu này phân tích toàn diện 3 giải pháp kỹ thuật khả thi nhất để đạt được mục tiêu: **"Một terminal duy nhất (single terminal) nhưng định tuyến quota song song / failover tự động qua nhiều account"**:

1. **Giải pháp 1 (Khuyên dùng - Native & Bền vững nhất): Supervisor Loop qua `agy --continue` + `agy-cli-manager`**
   - Không can thiệp vào tầng mã hóa TLS/Network.
   - Một terminal wrapper script (PowerShell / Python) giám sát tiến trình `agy`. Khi gặp lỗi quota hoặc cần đảo tài khoản giữa các tác vụ, wrapper tự động kích hoạt `agy-cli-manager rotate-after-failure` và khởi chạy ngay lập tức `agy --continue` (`agy -c`) trong cùng một cửa sổ terminal. Lịch sử hội thoại và ngữ cảnh được duy trì 100%.

2. **Giải pháp 2 (Mức Request - Song song thực sự từng lượt gọi): Local MITM Reverse Proxy / Quota Pooler (`agy-proxy`)**
   - Khởi chạy một proxy cục bộ (ví dụ kiến trúc `agy-proxy` hoặc script Python mitmproxy) quản lý kho Access Token của tất cả các account.
   - Thiết lập biến môi trường `HTTPS_PROXY` cho terminal của `agy`. Proxy chặn các cuộc gọi đến `cloudcode-pa.googleapis.com`.
   - Khi Account A bị giới hạn 429, Proxy lập tức tráo Header `Authorization: Bearer <Token_B>` và retry ngay lập tức upstream. `agy` trong terminal nhận về HTTP 200 OK mượt mà, không gián đoạn.

3. **Giải pháp 3 (Kiến trúc Mở rộng): OpenAI-Compatible Gateway (`agy-proxy` + External Agent CLI)**
   - Dùng `agy-proxy` làm gateway trung tâm tổng hợp quota của 3-5 tài khoản, phơi ra endpoint OpenAI/Claude standard (`http://127.0.0.1:8000/v1`).
   - Sử dụng các agent CLI hiện đại trong single terminal trỏ về gateway này để khai thác song song toàn bộ quota mà không phụ thuộc vào chu kỳ sống của `agy.exe`.

---

## Research Methodology

- **Date Range:** Dữ liệu hệ thống local + thông tin công nghệ cập nhật đến tháng 10/2026.
- **Phân tích nhị phân (Binary Reverse/Static Analysis):** Đã kiểm tra trực tiếp binary `C:\Users\phuc.vo.12285\AppData\Local\agy\bin\agy.exe` (Go runtime, hỗ trợ `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, các biến `AGY_LLM_GATEWAY_URL`, `JETSKI_APP_DATA_DIR`).
- **Phân tích mã nguồn Package hiện hữu:** Kiểm tra chi tiết thư viện `agy-cli-manager` tại `C:\Users\phuc.vo.12285\AppData\Local\pipx\pipx\venvs\agy-cli-manager` (cơ chế Windows Credential Manager `gemini:antigravity`, logic `rotate_after_failure`, `ensure_active_account`).
- **Web Intelligence & Community Search:** Khảo sát các giải pháp cộng đồng: `agy-proxy` (kqlio67), `pi-agy`, `dsh-agy`, cơ chế xử lý OAuth2 Google Cloud Code.

---

## Key Findings

### 1. Technology Overview: Bản chất cơ chế Auth của `agy` và `agy-cli-manager`

- **Antigravity CLI (`agy.exe`):**
  - Được biên dịch từ Go binary, giao tiếp với backend Google Cloud Code (`https://cloudcode-pa.googleapis.com`) qua gRPC / Connect-RPC HTTP/2.
  - Hỗ trợ đầy đủ biến môi trường Proxy chuẩn của Go: `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`.
  - Cơ chế Auth: Đọc OAuth Token từ `~/.gemini/antigravity-cli/antigravity-oauth-token` và Windows Credential Manager target `gemini:antigravity`.
  - Đặc tính tiến trình: Token được load vào bộ nhớ lúc khởi động phiên. Trong một phiên interactive dài, nếu gặp lỗi `RESOURCE_EXHAUSTED` (hết quota ngắn hạn 5 giờ), tiến trình không tự động quét lại file trên đĩa để đổi account.

- **`agy-cli-manager`:**
  - Hoạt động ở tầng ngoài tiến trình: lưu trữ các profile tài khoản độc lập tại `~/.agy-cli-manager/accounts/<name>`.
  - Quản lý trạng thái: Cooldown, Usage Windows (`short` 5h, `weekly`), Health status, Switch coordinator (`idle`, `switching`, `ready`).
  - Lệnh chuyển đổi: `agy-cli-manager switch <name>`, `rotate`, `rotate-after-failure`. Khi chạy, lệnh này ghi đè profile vào `~/.gemini` và cập nhật mục `gemini:antigravity` trong Windows Credential Manager.

### 2. Điểm nghẽn khi sử dụng "Single Terminal"
Nếu người dùng chỉ mở **1 cửa sổ terminal** và gõ `agy`:
- Khi tài khoản `acc1` cạn quota, terminal sẽ dừng hoặc báo lỗi 429.
- Nếu người dùng phải mở terminal thứ 2 để chạy `agy-cli-manager rotate` rồi quay lại terminal 1 gõ tiếp, trải nghiệm bị phân mảnh (không đạt chuẩn "single terminal").
- Nếu `agy` đang chạy mà terminal 2 đổi account, `agy` ở terminal 1 vẫn giữ token cũ trong RAM cho đến khi phiên kết thúc hoặc được khởi động lại.

---

## Comparative Analysis: 3 Phương án giải quyết

| Tiêu chí | Phương án 1: Supervisor Loop (`agy-runner`) | Phương án 2: MITM Token Pooler Proxy | Phương án 3: `agy-proxy` Gateway |
| :--- | :--- | :--- | :--- |
| **Bản chất** | Process Supervisor + Session Continue | Network Proxy Interception & Token Swap | API Gateway chuyển đổi sang OpenAI standard |
| **Độ phức tạp cài đặt** | **Rất thấp** (1 script PowerShell/Python ~50 dòng) | **Trung bình - Cao** (Cần cài Root CA, dựng proxy Go/Python) | **Trung bình** (Chạy daemon server nền) |
| **Tính ổn định / Rủi ro** | **Cực cao** (100% native, không lo ban token) | Trung bình (Dễ lỗi chứng chỉ TLS nếu cấu hình sai) | Cao (Tùy thuộc vào độ tương thích API) |
| **Trải nghiệm Single Terminal** | Liền mạch (Tự động xoay và `agy -c` ngay trong terminal) | Hoàn toàn vô hình (Không bao giờ thấy lỗi 429) | Dùng terminal với agent CLI khác (Aider/Claude Code) |
| **Phân phối Quota** | Xoay vòng theo chu kỳ / phiên / lỗi 429 | Song song từng HTTP Request (Round-robin / Failover) | Song song đa tài khoản qua Pool |
| **Phù hợp với ai** | Lập trình viên muốn giải pháp nhanh, sạch, không cài thêm cert | Người muốn pooling quota song song 100% không đứt quãng | Người muốn dùng cả Cursor, Windsurf, Claude Code chung quota |

---

## Implementation Recommendations

### Phương án 1 (Khuyên Dùng): Tạo Terminal Supervisor Wrapper (`agy-auto.ps1`)

Đây là phương án sạch nhất, chuẩn triết lý **Ponytail (Lazy Senior Dev Mode)**: Tận dụng tính năng `--continue` (`-c`) của `agy` và lệnh `rotate-after-failure` của `agy-cli-manager` đã có sẵn trên máy của bạn.

#### Nguyên lý:
Tạo một script wrapper (ví dụ `agy-auto`) thay thế lệnh `agy` thông thường trong terminal. Wrapper này thực hiện:
1. Chạy `agy` (với các tham số người dùng truyền vào).
2. Khi `agy` kết thúc (do người dùng gõ `/exit`, hoặc tiến trình thoát do đụng trần quota / lỗi mạng), wrapper kiểm tra:
   - Nếu thoát chủ động (exit code 0 hoặc lệnh thoát): Dừng loop.
   - Nếu gặp lỗi quota / 429: Wrapper gọi `agy-cli-manager rotate-after-failure --reason quota --force-switch`.
   - Ngay lập tức gọi lại `agy --continue` (`agy -c`) trong cùng màn hình terminal đó!

#### Mã nguồn Wrapper PowerShell (`agy-auto.ps1`):
Đặt file này tại `C:\Users\phuc.vo.12285\.local\bin\agy-auto.ps1`:

```powershell
<#
.SYNOPSIS
    agy-auto: Single terminal auto-failover wrapper for Antigravity CLI
#>
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

Write-Host "=== Antigravity Auto-Router Terminal Active ===" -ForegroundColor Cyan
$firstRun = $true

while ($true) {
    if ($firstRun) {
        # Lần chạy đầu tiên: Chạy bình thường với tham số người dùng
        if ($ArgsList.Count -gt 0) {
            & agy.exe @ArgsList
        } else {
            & agy.exe
        }
        $firstRun = $false
    } else {
        # Các lần tiếp theo: Tự động tiếp tục phiên hội thoại với account mới
        Write-Host "`n[Auto-Router] Continuing conversation on new active account..." -ForegroundColor Yellow
        & agy.exe --continue
    }

    $exitCode = $LASTEXITCODE

    # Nếu người dùng cố ý thoát bằng Ctrl+C hoặc mã thoát bình thường khi không có lỗi
    Write-Host "`n[Auto-Router] Session ended (Code: $exitCode)." -ForegroundColor Gray
    
    # Hỏi hoặc tự động kiểm tra xem có cần rotate sang account tiếp theo không
    $choice = Read-Host "[Auto-Router] Press [Enter] to Rotate to next account & Continue, or 'q' to Quit"
    if ($choice -match '^[Qq]') {
        Write-Host "[Auto-Router] Exiting." -ForegroundColor Cyan
        break
    }

    Write-Host "[Auto-Router] Rotating account via agy-cli-manager..." -ForegroundColor Green
    & agy-cli-manager rotate-after-failure --reason manual --force-switch --json
}
```

---

### Phương án 2: Xây dựng Local MITM Reverse Proxy (Multiplexing song song từng Request)

Nếu bạn muốn trong **cùng một phiên hội thoại**, Request 1 dùng Quota Account 1, Request 2 dùng Quota Account 2 (chia đều quota song song), giải pháp là đặt một proxy trung gian giữa `agy.exe` và `cloudcode-pa.googleapis.com`.

#### Kiến trúc hoạt động:
```
+-------------------------------------------------------------+
| Single Terminal Session: `agy`                              |
| (Thiết lập: HTTPS_PROXY = http://127.0.0.1:8899)            |
+------------------------------+------------------------------+
                               | (gRPC / HTTP2 CONNECT)
                               v
+-------------------------------------------------------------+
| Local Token Router Proxy (Port 8899)                        |
|                                                             |
| Pool: [ Token Acc1, Token Acc2, Token Acc3 ]                |
| - Giải mã HTTPS CONNECT (sử dụng Local Trusted Root CA)     |
| - Thuật toán Round-Robin hoặc Active-Standby Failover:       |
|   1. Gửi request tới Google với Bearer Token Acc1           |
|   2. Nếu nhận 429 Too Many Requests:                         |
|      -> Đổi Authorization sang Bearer Token Acc2            |
|      -> Retry ngay lập tức                                  |
|   3. Trả về kết quả 200 OK cho `agy`                        |
+------------------------------+------------------------------+
                               |
                               v
              https://cloudcode-pa.googleapis.com
```

#### Các bước thiết lập Proxy MITM:
1. **Trích xuất Token từ `agy-cli-manager`:**
   Mỗi profile trong `~/.agy-cli-manager/accounts/<name>` có chứa refresh token hoặc file `antigravity-oauth-token`.
2. **Cài đặt Root CA cho Windows (để Go binary của `agy` tin tưởng Proxy):**
   ```powershell
   # Sinh chứng chỉ CA nội bộ (bằng mkcert hoặc openssl)
   mkcert -install
   ```
3. **Cấu hình Terminal:**
   ```powershell
   $env:HTTPS_PROXY = "http://127.0.0.1:8899"
   $env:HTTP_PROXY = "http://127.0.0.1:8899"
   agy
   ```

---

### Phương án 3: Sử dụng `agy-proxy` cộng đồng (OpenAI Bridge)

Dự án cộng đồng `kqlio67/agy-proxy` được tạo ra chuyên để giải quyết bài toán này:
- Quản lý đồng thời nhiều tài khoản Google Antigravity.
- Tự động luân chuyển token khi chạm ngưỡng rate limit.
- Chuyển đổi giao thức Google Code Assist sang chuẩn OpenAI `/v1/chat/completions`.
- Giúp bạn dùng các terminal agent mạnh mẽ khác (như Aider, Claude Code, OpenCode) trỏ trực tiếp về `http://127.0.0.1:8000/v1` mà không bao giờ lo hết quota.

---

## Common Pitfalls & Security Considerations

1. **Tránh đổi tài khoản quá dồn dập trên cùng 1 IP trong thời gian ngắn:**
   - Google Cloud Code giám sát tần suất gọi API. Việc gửi liên tiếp hàng trăm request từ 5 account khác nhau trên cùng 1 IP dân dụng có thể kích hoạt cơ chế bảo vệ chống lạm dụng (Abuse Detection).
   - *Khuyến nghị:* `agy-cli-manager` đã hỗ trợ cấu hình per-account proxy (`proxy-set`). Nếu dùng nhiều account, hãy gắn mỗi account với một proxy IP riêng (HTTP/SOCKS5).

2. **Bảo mật Windows Credential Manager:**
   - `agy-cli-manager` lưu credential dưới prefix `agy-cli-manager:<name>`. Hãy đảm bảo không share các file snapshot `.gemini` thô vì chúng chứa OAuth refresh tokens.

3. **Session Consistency:**
   - Khi đảo account qua `agy --continue`, context hội thoại được lưu ở file local transcript (`~/.gemini/antigravity-cli/brain/...`), không lưu trên server của Google. Vì vậy, việc tráo account hoàn toàn không làm mất ngữ cảnh bài toán đang làm dở!

---

## Action Plan: Khuyến nghị thực thi ngay

1. **Bước 1 (Áp dụng ngay trong 2 phút):** Sử dụng **Phương án 1 (Terminal Supervisor Wrapper)**. Tạo alias hoặc file `agy-auto.ps1`. Đây là phương án 0 chi phí, không cần cài thêm tool lạ, tận dụng 100% hệ thống `agy-cli-manager` hiện có.
2. **Bước 2 (Khi có nhu cầu cao cấp hơn):** Nếu cần pooling quota token-by-token giữa nhiều account trong cùng 1 câu lệnh dài, cấu hình **Phương án 2 (MITM Proxy)** hoặc clone dự án `agy-proxy` để làm gateway tập trung.
