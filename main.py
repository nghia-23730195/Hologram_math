# -*- coding: utf-8 -*-
"""
main.py
-------
Điểm khởi chạy ứng dụng (Main Entry Point) cho Phần mềm Trình chiếu 3D Hologram 
kết hợp Tương tác Không chạm MediaPipe.

Tác giả: Senior Software Engineer & Computer Graphics Expert
Dự án: Hologram 4-Side Pyramid Renderer & Touchless Gesture Control
"""

import sys
import os

# Cấu hình UTF-8 cho Windows Console để tránh lỗi font hoặc crash charmap
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Tắt log cảnh báo rác của OpenCV C++ VideoIO
os.environ["OPENCV_LOG_LEVEL"] = "FATAL"
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

# Thêm thư mục hiện tại vào sys.path để import các module local
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import HologramMainWindow


def main():
    """Khởi tạo và khởi chạy ứng dụng Hologram 3D."""
    print("=" * 65)
    print("🚀 HOLOGRAM MATH 3D - PHIÊN BẢN V2.3 (MỚI NHẤT)")
    print("✨ TỰ ĐỘNG THÍCH ỨNG MÀN HÌNH HIGH-DPI & TRÀN TOÀN BỘ MÀN HÌNH 16:9")
    print("✨ CỬ CHỈ MỞ HỘP 2D: 👍 Giơ ngón cái (0.35s) Bật / Tạm dừng")
    print("=" * 65)

    # Khởi tạo QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("3D Hologram Generator & MediaPipe Touchless Control")
    app.setOrganizationName("Hologram Computer Graphics")
    if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # Thiết lập giao diện màu tối chuẩn (Dark Theme)
    window = HologramMainWindow()
    window.show()

    # Vòng lặp sự kiện chính của ứng dụng PyQt6
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
