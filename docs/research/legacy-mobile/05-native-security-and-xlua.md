# Module 05: Tầng Native, Bảo Mật & Máy Ảo xLua (Native Security & xLua)

Tài liệu phân tích cấu trúc nhị phân của các thư viện native trích xuất từ APK.

---

## 1. Cấu Trúc Nhị Phân `libil2cpp.so` (ARM64 ELF)

* **Kích thước:** 121,785,096 bytes (~121.8 MB).
* **Kiến trúc:** AArch64 (ARM 64-bit Little Endian, ELF Class 2).
* **Bảng Ký Hiệu Động (`.dynsym`):**
  * **HOÀN TOÀN UNSTRIPPED** đối với các API xuất khẩu của Unity IL2CPP!
  * Chứa **231 API symbols `il2cpp_*`**, cho phép can thiệp hook hoặc reflection native cực kỳ dễ dàng:
    * `il2cpp_init` tại offset `0x1F82B1C`
    * `il2cpp_domain_get` tại offset `0x1F83278`
    * `il2cpp_domain_assembly_open` tại offset `0x1F8327C`
    * `il2cpp_assembly_get_image` tại offset `0x1F82C58`
    * `il2cpp_image_get_name` tại offset `0x1F8381C`
    * `il2cpp_class_from_name` tại offset `0x1F82C84`
    * `il2cpp_class_get_methods` tại offset `0x1F82CA8`
    * `il2cpp_runtime_invoke` tại offset `0x1F835E4`
    * `il2cpp_string_new` tại offset `0x1F83614`
    * `il2cpp_thread_attach` tại offset `0x1F83630`

---

## 2. Cấu Trúc `global-metadata.dat` (19.4 MB)

* **Vị trí trong APK:** `assets/bin/Data/Managed/Metadata/global-metadata.dat`.
* **Header Analysis:**
  * **8-byte Custom Prefix:** `56 BE F0 89 C2 53 89 F0` (Được nhà phát triển chèn thêm vào đầu file nhằm ngăn chặn các tool dump mặc định đọc trực tiếp ở offset 0).
  * **Magic Number tại offset 8:** `AF 1B B1 FA` (`0xFAB11BAF`) $\rightarrow$ Chuẩn Magic Number của Unity IL2CPP.
  * **Phiên bản tại offset 12:** `24` $\rightarrow$ Chuẩn cấu trúc **IL2CPP Version 24** (Unity 2019.4 LTS).
  * **Nội dung chuỗi:** Toàn bộ bảng chuỗi (Strings) từ offset `286064` là **Plaintext UTF-8 không mã hóa**.
* **Cách khắc phục để dump:**
  * Chỉ cần cắt bỏ đúng 8 byte đầu tiên (`Trim first 8 bytes`), file metadata sẽ trở thành file chuẩn và có thể nạp trực tiếp vào **Il2CppDumper** hoặc **Ghidra/IDA** để đổi tên toàn bộ hàm trong `libil2cpp.so`.

---

## 3. Máy Ảo Tencent xLua (`libxlua.so`)

* **Kích thước:** 3,650,624 bytes.
* **Chức năng:** Cung cấp môi trường thực thi Lua 5.3 nhúng trong game.
* **Cầu nối C# ⇄ Lua:**
  * Các class C# được bọc (wrapped) trong namespace `XLua.CSObjectWrap.*`:
    * `DreamGameNetworkManagerWrap`: Cho phép script Lua gọi trực tiếp các hàm gửi nhận gói tin mạng.
    * `DreamXXTableWrap`: Cho phép script Lua truy xuất các bảng dữ liệu cấu hình.
* **Ý nghĩa:** Logic điều khiển của game có thể được mở rộng hoặc can thiệp thông qua máy ảo Lua này.

---

## 4. Hệ Thống Bảo Mật & Anti-Cheat (ByteDance GameProtect)

* **Thư viện chính:** `libhhld-rt.so` (1.63 MB) và `libEncryptor.so` (83.9 KB).
* **Nhận diện thành phần:**
  * Gói bảo vệ: `com/bytedance/gameprotect/GameProtect`.
  * Hook Engine: Nhúng `bytehook` và `shadowhook` để giám sát các lời gọi hàm JNI (`JNI_OnLoad_Interceptor`).
  * Mã hóa toàn vẹn: Tích hợp thư viện Crypto++ (`N8CryptoPP`) với hàm băm SHA1 để kiểm tra chữ ký và tính toàn vẹn của file APK lúc khởi chạy.
