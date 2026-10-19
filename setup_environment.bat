@echo off
chcp 65001 >nul
title Cài đặt môi trường 3D Hologram Math
echo ======================================================================
echo   DỰ ÁN: 3D HOLOGRAM GENERATOR & TOUCHLESS GESTURE CONTROL
echo   Tự động khởi tạo môi trường và cài đặt toàn bộ thư viện...
echo ======================================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [LỖI] Không tìm thấy Python trên máy tính này!
    echo.
    echo Vui lòng cài đặt Python (khuyến nghị phiên bản 3.10 hoặc 3.11 - 64 bit):
    echo https://www.python.org/downloads/
    echo.
    echo QUAN TRỌNG: Hãy tích chọn vào ô [x] "Add python.exe to PATH" khi cài!
    echo.
    pause
    exit /b 1
)

echo [1/3] Đang tạo môi trường ảo Python (venv)...
if not exist "venv" (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [LỖI] Không thể tạo môi trường ảo venv!
        pause
        exit /b 1
    )
    echo -> Tạo venv thành công!
) else (
    echo -> Môi trường venv đã tồn tại sẵn.
)

echo.
echo [2/3] Đang kích hoạt môi trường venv và nâng cấp pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip

echo.
echo [3/3] Đang cài đặt các thư viện cần thiết (PyQt6, OpenGL, OpenCV, MediaPipe)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo [CẢNH BÁO] Quá trình cài đặt gặp lỗi!
    echo Hãy kiểm tra kết nối mạng Internet hoặc chắc chắn bạn dùng Python 3.9 - 3.11 (64-bit).
    pause
    exit /b 1
)

echo.
echo ======================================================================
echo   CHÚC MỪNG: CÀI ĐẶT THÀNH CÔNG 100%!
echo   Bây giờ bạn chỉ cần nháy đúp chuột vào file "run_app.bat" để chạy phần mềm.
echo ======================================================================
pause
