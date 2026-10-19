@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
title 3D Hologram Pyramid & AI Gesture Control
cd /d "%~dp0"

echo ======================================================================
echo   ĐANG KHỞI CHẠY HỆ THỐNG 3D HOLOGRAM & AI GESTURE CONTROL...
echo ======================================================================
echo.

if exist "venv\Scripts\python.exe" (
    call venv\Scripts\activate.bat
    python main.py
) else (
    where python >nul 2>nul
    if %errorlevel% equ 0 (
        python main.py
    ) else (
        echo ==========================================================
        echo [LỖI] Chưa tìm thấy môi trường Python!
        echo Hãy nháy đúp chuột vào file "setup_environment.bat" trước.
        echo ==========================================================
        pause
        exit /b 1
    )
)

if %errorlevel% neq 0 (
    echo.
    echo ==========================================================
    echo Ứng dụng đã kết thúc hoặc gặp lỗi (Mã: %errorlevel%).
    echo Nếu thiếu thư viện, hãy chạy file "setup_environment.bat".
    echo ==========================================================
    pause
)
