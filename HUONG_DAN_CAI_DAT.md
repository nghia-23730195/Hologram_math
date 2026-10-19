# HƯỚNG DẪN CÀI ĐẶT VÀ SỬ DỤNG HỆ THỐNG 3D HOLOGRAM MATH (PHIÊN BẢN V2.3)

Tài liệu hướng dẫn chi tiết từng bước cài đặt môi trường, cấu hình và vận hành phần mềm Mô phỏng 3D Hologram kết hợp Điều khiển Cử chỉ AI MediaPipe.

---

## 1. YÊU CẦU HỆ THỐNG (SYSTEM REQUIREMENTS)

- **Hệ điều hành:** Windows 10 hoặc Windows 11 (64-bit).
- **Python:** Khuyến nghị **Python 3.10** hoặc **Python 3.11** (64-bit).  
  *(Lưu ý: MediaPipe tương thích ổn định nhất trên Python 3.10 / 3.11. Tránh dùng Python 3.12+ do một số bản phân phối MediaPipe chưa hỗ trợ đầy đủ).*
- **Phần cứng:** 
  - Webcam laptop hoặc camera rời kết nối cổng USB.
  - Màn hình hỗ trợ độ phân giải Full HD (1920x1080) hoặc tương đương (phần mềm tự động thích ứng với Windows Display Scaling 125%, 150%).
  - Thiết bị chiếu: Kính Hologram 4 mặt (Pyramid) hoặc Hộp kính nghiêng 45 độ (Pepper's Ghost Box).

---

## 2. CÁCH CÀI ĐẶT NHANH (KHUYÊN DÙNG - TỰ ĐỘNG 100%)

Nếu bạn cài đặt trên một máy tính mới chưa có môi trường:

1. **Bước 1: Tải và cài đặt Python (nếu máy chưa có):**
   - Truy cập trang chủ Python: https://www.python.org/downloads/
   - Tải bản Python 3.10 hoặc 3.11 (64-bit).
   - **QUAN TRỌNG:** Trong lúc cài đặt, hãy tích chọn vào ô vuông **`[x] Add python.exe to PATH`** ở màn hình đầu tiên trước khi nhấn *Install Now*.

2. **Bước 2: Chạy cài đặt tự động:**
   - Mở thư mục phần mềm `Hologram_Math_V2_MOI_NHAT_CHEP_MAY_MOI`.
   - Nháy đúp chuột vào file:
     ```text
     setup_environment.bat
     ```
   - Hệ thống sẽ tự động tạo môi trường ảo `venv` và cài đặt đầy đủ 5 thư viện cần thiết:
     - `PyQt6` (Giao diện người dùng đồ họa hiện đại)
     - `PyOpenGL` (Dựng hình không gian 3D phần cứng)
     - `opencv-python` (Xử lý khung hình camera thời gian thực)
     - `mediapipe` (Nhận diện khớp bàn tay và ngón tay bằng AI)
     - `numpy` (Tính toán ma trận và góc không gian)
   - Khi màn hình hiển thị: `CHÚC MỪNG: CÀI ĐẶT THÀNH CÔNG 100%!`, bạn bấm phím bất kỳ để đóng cửa sổ.

3. **Bước 3: Khởi chạy phần mềm:**
   - Nháy đúp chuột vào file:
     ```text
     run_app.bat
     ```
   - Ứng dụng sẽ tự động mở lên với đầy đủ tính năng!

---

## 3. CÁCH CÀI ĐẶT BẰNG DÒNG LỆNH (CHO LẬP TRÌNH VIÊN)

Nếu bạn muốn cài đặt bằng Terminal / PowerShell:

```bash
# 1. Di chuyển vào thư mục dự án
cd /d "D:\SMLab\HOLOGRAM MATH\Hologram_Math\Hologram_Math_V2_MOI_NHAT"

# 2. Tạo môi trường ảo
python -m venv venv

# 3. Kích hoạt môi trường ảo
# Trên Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Hoặc trên Command Prompt (cmd):
call venv\Scripts\activate.bat

# 4. Nâng cấp pip và cài đặt thư viện
python -m pip install --upgrade pip
pip install -r requirements.txt

# 5. Khởi chạy ứng dụng
python main.py
```

---

## 4. BẢNG PHÍM TẮT THAO TÁC NHANH TRÊN BÀN PHÍM

| Phím tắt | Chức năng | Mô tả chi tiết |
| :--- | :--- | :--- |
| **`F11`** | **Toàn màn hình (Fullscreen)** | Bật/tắt chế độ toàn màn hình, tự động ẩn thanh Taskbar Windows. |
| **`F`** | **Fit / Fill thông minh** | Bấm để chuyển đổi giữa **Vừa khít (85%)** và **Tràn màn hình (Fill 100%)**. |
| **`Shift + F`** | **Tràn toàn màn hình 100%** | Phóng to hình khối chạm sát 2 mép trái/phải màn hình 16:9, không viền đen. |
| **`+`** hoặc **`Z`** | **Phóng to (Zoom In)** | Phóng to quang học thêm 15% mỗi lần bấm. |
| **`-`** hoặc **`X`** | **Thu nhỏ (Zoom Out)** | Thu nhỏ quang học bớt 15% mỗi lần bấm. |
| **`H`** | **Chế độ Hộp Hologram** | Nền đen tuyền tuyệt đối (Pitch Black), ẩn sạch mọi khung viền Cyan và chữ. |
| **`M`** | **Lật gương quang học** | Lật ngược chữ theo trục X để khử hiện tượng đảo chữ qua kính nghiêng 45°. |
| **`R`** | **Đặt lại góc nhìn (Reset)** | Đưa hình khối về góc xoay và khoảng cách zoom chuẩn 100%. |
| **`U`** hoặc **`Space`** | **Hoạt hình Mở hộp 2D** | Bật / Tạm dừng hoạt hình trải phẳng hình khối thành mạng 2D. |
| **`[`** và **`]`** | **Điều chỉnh độ mở phẳng** | Giảm / Tăng 10% tiến độ trải phẳng hình khối. |
| **`C`** | **Ẩn/Hiện Camera** | Ẩn hoặc hiện khung hình webcam nhỏ góc phải khi đang ở Toàn màn hình. |
| **`G`** | **Bảng hướng dẫn cử chỉ** | Bật/tắt bảng hướng dẫn cử chỉ tay khi đang ở chế độ Toàn màn hình. |
| **`Esc`** | **Thoát Toàn màn hình** | Trở về giao diện cửa sổ điều khiển thông thường. |

---

## 5. BẢNG CỬ CHỈ TAY AI (TOUCHLESS CONTROL)

| Cử chỉ bàn tay | Hành động kích hoạt | Cách thực hiện |
| :--- | :--- | :--- |
| 👍 **Giơ ngón cái (Thumbs-Up)** | **Mở hộp 2D / Gập lại 3D** | Nắm bàn tay và chĩa thẳng ngón cái lên trên trong 0.35 giây. |
| 👐 **2 Bàn tay tách xa / lại gần** | **Phóng to / Thu nhỏ (Zoom)** | Đưa 2 bàn tay lên trước camera, tách xa để phóng to, kéo lại gần để thu nhỏ. |
| 👌 **Ngón cái + Ngón trỏ chụm** | **Xoay vật thể 3D (Rotate)** | Chụm ngón cái và ngón trỏ của 1 bàn tay, di chuyển bàn tay để xoay đa hướng. |
| ☝️ **Chỉ ngón trỏ (1 ngón)** | **Air Laser Pointer / Cắt 3D** | Giơ duy nhất ngón trỏ để điều khiển tia ngắm Laser hoặc trượt cao độ mặt phẳng cắt 3D. |
| 🖐️ **Xòe cả bàn tay** | **Trạng thái chờ / Hover** | Di chuyển tự do trong không gian mà không làm thay đổi thông số hình. |

---

## 6. XỬ LÝ SỰ CỐ THƯỜNG GẶP (TROUBLESHOOTING)

1. **Lỗi `'python' is not recognized as an internal or external command`:**
   - Nguyên nhân: Khi cài Python chưa tích chọn `Add python.exe to PATH`.
   - Cách sửa: Cài đặt lại Python và nhớ tích vào ô vuông `Add python.exe to PATH`.

2. **Lỗi `ModuleNotFoundError: No module named 'mediapipe'`:**
   - Nguyên nhân: Chưa kích hoạt môi trường `venv` hoặc cài thư viện vào sai bản Python.
   - Cách sửa: Nháy đúp vào `setup_environment.bat` để script tự động cài lại vào đúng thư mục `venv`.

3. **Webcam không hiển thị hoặc báo `[Camera Error]`:**
   - Kiểm tra xem webcam có đang bị phần mềm khác (như Zoom, Google Meet, Zalo, Camera app) chiếm dụng không.
   - Vào Windows Settings -> Privacy & Security -> Camera -> Bật *Let desktop apps access your camera*.
   - Trong bảng điều khiển bên trái phần mềm, thử đổi cổng camera từ `0` sang `1` hoặc `2`.

4. **Chữ trên màn hình bị ngược (`mo 0.01 = s`):**
   - Bạn chỉ cần bấm phím **`M`** trên bàn phím để chuyển đổi lại chiều chữ bình thường.
