# -*- coding: utf-8 -*-
"""
ui/main_window.py
-----------------
Cửa sổ chính (Main Application Window) kết nối tất cả các phân hệ:
1. UI Control Panel Sidebar (Quản lý hình học, cm, màu sắc).
2. OpenGL 3D Render Canvas (Pitch Black Hologram viewport).
3. Live Camera Preview (MediaPipe 21 Hand Landmarks & Touchless Pinch interaction).
"""

import os
import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter,
    QStatusBar, QLabel, QScrollArea, QDialog, QFormLayout, QComboBox,
    QLineEdit, QPushButton, QMessageBox, QToolBar
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence, QAction, QImage, QPixmap

from graphics.gl_widget import HologramGLWidget
from ui.control_panel import ControlPanelWidget
from ui.camera_widget import CameraPreviewWidget
from vision.camera_thread import CameraThread


class HologramMainWindow(QMainWindow):
    def __init__(self, camera_source=0):
        super().__init__()

        self.setWindowTitle("HOLOGRAM TOÁN HỌC 3D [V2.2 MỚI NHẤT] | [Mở 2D: Thumbs-Up | Xoay 3D: Pinch | Zoom: 2 Tay | F11: Fullscreen]")
        self.resize(1366, 768)
        self.is_3d_fullscreen = False

        # Style sheet tổng thể cho ứng dụng
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0c10;
            }
            QStatusBar {
                background-color: #12141c;
                color: #00f0ff;
                font-weight: bold;
                font-size: 12px;
                border-top: 1px solid #2a2e3d;
                padding: 4px 8px;
            }
            QScrollArea {
                border: none;
                background-color: #12141c;
            }
            QScrollBar:vertical {
                border: none;
                background: #0f141f;
                width: 7px;
                margin: 0px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #283a54;
                min-height: 24px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: #00e5ff;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
        """)

        # Khởi tạo các Widget phân hệ chính
        self.gl_widget = HologramGLWidget(self)

        # Các Widget lớp phủ (Overlay) khi vào chế độ toàn màn hình 3D:
        # 1. Khung Webcam mini góc trên bên phải
        self.stream_camera_overlay = QLabel(self.gl_widget)
        self.stream_camera_overlay.setFixedSize(280, 200)
        self.stream_camera_overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stream_camera_overlay.setStyleSheet("background:#05070a; border:2px solid #00eaff; border-radius:8px;")
        self.stream_camera_overlay.hide()

        # 2. Huy hiệu trạng thái cử chỉ trực tiếp (Live Status Badge)
        self.stream_status_badge = QLabel(self.gl_widget)
        self.stream_status_badge.setFixedSize(280, 32)
        self.stream_status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stream_status_badge.setStyleSheet("""
            QLabel {
                background-color: #121824;
                border: 1.5px solid #2a3b59;
                color: #94a3b8;
                font-size: 11px;
                font-weight: bold;
                border-radius: 6px;
                padding: 4px 6px;
            }
        """)
        self.stream_status_badge.setText("⏳ Chờ cử chỉ...")
        self.stream_status_badge.hide()

        # 3. Bảng cử chỉ điều khiển AI toàn màn hình (Gesture Guide Card)
        self.stream_gesture_guide = QLabel(self.gl_widget)
        self.stream_gesture_guide.setFixedWidth(280)
        self.stream_gesture_guide.setWordWrap(True)
        self.stream_gesture_guide.setStyleSheet("""
            QLabel {
                background-color: rgba(9, 12, 18, 230);
                border: 1.5px solid #00eaff;
                border-radius: 8px;
                padding: 8px 10px;
            }
        """)
        self.stream_gesture_guide.setText(self._get_gesture_guide_html())
        self.stream_gesture_guide.hide()

        self.control_panel = ControlPanelWidget(self)
        self.camera_widget = CameraPreviewWidget(self)

        # QThread thu webcam & nhận diện bàn tay (mặc định Camera 0 Laptop/USB)
        if camera_source is not None:
            self.camera_thread = CameraThread(camera_source=camera_source, parent=self)
        else:
            self.camera_thread = None

        self._setup_layout()
        self._connect_signals()

        # Khóa chống kích hoạt chéo giữa các hành động rời rạc (Global Action Lock)
        self.last_discrete_action_time = 0.0
        self.discrete_action_cooldown = 0.50

        # Phím tắt toàn cửa sổ, hoạt động dù focus đang ở camera/OpenGL/control panel.
        self.fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        self.fullscreen_shortcut.activated.connect(self._toggle_3d_fullscreen)
        self.exit_fullscreen_shortcut = QShortcut(QKeySequence("Escape"), self)
        self.exit_fullscreen_shortcut.activated.connect(self._exit_fullscreen)
        self.guide_shortcut = QShortcut(QKeySequence("G"), self)
        self.guide_shortcut.activated.connect(self._toggle_fullscreen_gesture_guide)
        self.mirror_shortcut = QShortcut(QKeySequence("M"), self)
        self.mirror_shortcut.activated.connect(self._toggle_mirror_mode)
        self.box_mode_shortcut = QShortcut(QKeySequence("H"), self)
        self.box_mode_shortcut.activated.connect(self._toggle_hologram_box_mode)

        # Ẩn thanh MenuBar truyền thống để dùng Toolbar Cyberpunk hiện đại
        self.menuBar().hide()

        # Thanh công cụ Top Toolbar hiện đại, tương phản cao
        self.toolbar = self.addToolBar("QuickAccessToolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #0d1017;
                border-bottom: 1.5px solid #1e2638;
                padding: 6px 10px;
                spacing: 10px;
            }
            QToolButton {
                background-color: #141c2b;
                border: 1.5px solid #233247;
                border-radius: 6px;
                color: #38bdf8;
                font-size: 13px;
                font-weight: bold;
                padding: 7px 16px;
            }
            QToolButton:hover {
                background-color: #1e2a42;
                border-color: #00f0ff;
                color: #ffffff;
            }
            QToolButton:pressed {
                background-color: #0284c7;
                color: #ffffff;
            }
        """)

        fullscreen_action = QAction("[F11] Phóng to vùng 3D", self)
        fullscreen_action.triggered.connect(self._toggle_3d_fullscreen)
        self.toolbar.addAction(fullscreen_action)

        self.action_fill = QAction("[⛶] Tràn màn hình 100%", self)
        self.action_fill.setToolTip("Phóng to khối hình tràn ngập 100% toàn bộ màn hình 16:9 (Phím tắt: Shift+F hoặc F)")
        self.action_fill.triggered.connect(self.gl_widget.fill_screen)
        self.toolbar.addAction(self.action_fill)

        self.action_mirror = QAction("[M] Lật gương (Kính 45°)", self)
        self.action_mirror.setCheckable(True)
        self.action_mirror.triggered.connect(self._toggle_mirror_mode)
        self.toolbar.addAction(self.action_mirror)

        self.action_box_mode = QAction("[H] Hộp chiếu Hologram", self)
        self.action_box_mode.setCheckable(True)
        self.action_box_mode.triggered.connect(self._toggle_hologram_box_mode)
        self.toolbar.addAction(self.action_box_mode)

        self.action_slice = QAction("[✂] Mặt cắt không gian 3D", self)
        self.action_slice.setCheckable(True)
        self.action_slice.triggered.connect(self._toggle_slicing_from_toolbar)
        self.toolbar.addAction(self.action_slice)

        self.action_unfold = QAction("[U] Mở hộp trải phẳng 2D", self)
        self.action_unfold.triggered.connect(self._toggle_unfold_animation)
        self.toolbar.addAction(self.action_unfold)

        reset_action = QAction("[↺] Đặt lại góc nhìn (Reset)", self)
        reset_action.triggered.connect(self.gl_widget.reset_view)
        self.toolbar.addAction(reset_action)

        test_action = QAction("[★] Kiểm tra công thức toán", self)
        test_action.triggered.connect(self.open_area_volume_test)
        self.toolbar.addAction(test_action)

        # Khởi chạy Thread Webcam nếu có
        if self.camera_thread is not None:
            self.camera_thread.start()

    def showEvent(self, event):
        super().showEvent(event)
        # Đảm bảo bảng điều khiển bên trái luôn bắt đầu cuộn từ trên cùng
        if hasattr(self, 'scroll_control'):
            self.scroll_control.verticalScrollBar().setValue(0)

    def keyPressEvent(self, event):
        """Phím tắt hiển thị: F11 bật/tắt toàn màn hình, Esc để thoát, M lật gương, H hộp chiếu, G bảng cử chỉ."""
        if event.key() == Qt.Key.Key_F11:
            self._toggle_3d_fullscreen()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape and self.is_3d_fullscreen:
            self._toggle_3d_fullscreen()
            event.accept()
            return
        if event.key() == Qt.Key.Key_M:
            self._toggle_mirror_mode()
            event.accept()
            return
        if event.key() == Qt.Key.Key_H:
            self._toggle_hologram_box_mode()
            event.accept()
            return
        if event.key() == Qt.Key.Key_R:
            self.gl_widget.reset_view()
            self.gl_widget.show_toast("ĐÃ ĐẶT LẠI GÓC NHÌN CHUẨN (RESET)", "↺", 1500)
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Right, Qt.Key.Key_PageDown):
            shape_name = self.control_panel.next_shape()
            self.gl_widget.show_toast(f"ĐÃ ĐỔI: {shape_name}", "✨")
            self.lbl_status_info.setText(f"👉 Phím Mũi tên Phải: Đổi sang {shape_name}")
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_PageUp):
            shape_name = self.control_panel.prev_shape()
            self.gl_widget.show_toast(f"ĐÃ ĐỔI: {shape_name}", "✨")
            self.lbl_status_info.setText(f"👈 Phím Mũi tên Trái: Quay lại {shape_name}")
            event.accept()
            return
        if event.key() == Qt.Key.Key_F:
            if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) or self.gl_widget.zoom_factor < 3.0:
                self.gl_widget.fill_screen()
            else:
                self.gl_widget.fit_to_screen()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Plus, Qt.Key.Key_Equal, Qt.Key.Key_Z):
            self.gl_widget.zoom_in()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_Minus, Qt.Key.Key_Underscore, Qt.Key.Key_X):
            self.gl_widget.zoom_out()
            event.accept()
            return
        if event.key() == Qt.Key.Key_C and self.is_3d_fullscreen:
            is_vis = self.stream_camera_overlay.isVisible()
            self.stream_camera_overlay.setVisible(not is_vis)
            self.stream_status_badge.setVisible(not is_vis)
            self.gl_widget.show_toast("ĐÃ ẨN CAMERA" if is_vis else "ĐÃ HIỆN CAMERA", "📹", 1200)
            event.accept()
            return
        if event.key() == Qt.Key.Key_G and self.is_3d_fullscreen:
            self._toggle_fullscreen_gesture_guide()
            event.accept()
            return
        if event.key() in (Qt.Key.Key_U, Qt.Key.Key_Space):
            self._toggle_unfold_animation()
            event.accept()
            return
        if event.key() == Qt.Key.Key_BracketLeft:
            new_val = max(0, self.control_panel.slider_unfold.value() - 10)
            self.control_panel.slider_unfold.setValue(new_val)
            self.gl_widget.show_toast(f"TRẢI PHẲNG: {new_val}%", "📦")
            event.accept()
            return
        if event.key() == Qt.Key.Key_BracketRight:
            new_val = min(100, self.control_panel.slider_unfold.value() + 10)
            self.control_panel.slider_unfold.setValue(new_val)
            self.gl_widget.show_toast(f"TRẢI PHẲNG: {new_val}%", "📦")
            event.accept()
            return
        super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.is_3d_fullscreen:
            self._reposition_fullscreen_overlays()

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.lbl_status_info.setText("Đã thoát chế độ toàn màn hình")
        else:
            self.showFullScreen()
            self.lbl_status_info.setText("Toàn màn hình | F11/Esc để thoát")

    def _exit_fullscreen(self):
        if self.is_3d_fullscreen:
            self._toggle_3d_fullscreen()

    def _toggle_fullscreen_gesture_guide(self):
        """Bật/tắt hiển thị Bảng cử chỉ AI trong chế độ toàn màn hình 3D (Phím G)."""
        if not self.is_3d_fullscreen:
            return
        is_visible = self.stream_gesture_guide.isVisible()
        self.stream_gesture_guide.setVisible(not is_visible)
        self.stream_status_badge.setVisible(not is_visible)
        msg = "ĐÃ HIỆN BẢNG CỬ CHỈ" if not is_visible else "ĐÃ ẨN BẢNG CỬ CHỈ (BẤM 'G' ĐỂ MỞ LẠI)"
        self.gl_widget.show_toast(msg, "🎮")

    def _reposition_fullscreen_overlays(self):
        """Định vị các widget lớp phủ trên màn hình 3D toàn màn hình."""
        if not self.is_3d_fullscreen:
            return
        w = self.gl_widget.width()
        h = self.gl_widget.height()
        card_w = 280
        pos_x = 24 if getattr(self.gl_widget, 'mirror_mode', False) else max(16, w - card_w - 20)

        # 1. Khung xem Webcam mini
        self.stream_camera_overlay.setGeometry(pos_x, 48, card_w, 200)

        # 2. Huy hiệu trạng thái cử chỉ trực tiếp
        self.stream_status_badge.setGeometry(pos_x, 256, card_w, 32)

        # 3. Bảng hướng dẫn cử chỉ AI (tự động căn chỉnh chiều cao tối ưu)
        guide_y = 296
        self.stream_gesture_guide.setFixedWidth(card_w)
        self.stream_gesture_guide.adjustSize()
        opt_h = max(315, self.stream_gesture_guide.sizeHint().height())
        guide_h = min(opt_h, max(220, h - guide_y - 20))
        self.stream_gesture_guide.setGeometry(pos_x, guide_y, card_w, guide_h)

    def _update_stream_status_badge(self, text: str, bg_color: str, border_color: str, text_color: str):
        """Cập nhật huy hiệu trạng thái cử chỉ trên giao diện toàn màn hình."""
        if hasattr(self, 'stream_status_badge'):
            self.stream_status_badge.setText(text)
            self.stream_status_badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg_color};
                    border: 1.5px solid {border_color};
                    color: {text_color};
                    font-size: 11px;
                    font-weight: bold;
                    border-radius: 6px;
                    padding: 4px 6px;
                }}
            """)

    @staticmethod
    def _get_gesture_guide_html():
        """Bảng hướng dẫn cử chỉ AI định dạng HTML tương phản cao cho Fullscreen."""
        return (
            "<table width='100%' cellpadding='0' cellspacing='0' style='margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1.5px solid #232d3f;'>"
            "  <tr>"
            "    <td style='color: #00f0ff; font-weight: bold; font-size: 11px; white-space: nowrap;'>"
            "      🎮 BẢNG CỬ CHỈ (V2.2 MỚI NHẤT)"
            "    </td>"
            "    <td style='color: #64748b; font-size: 10px; text-align: right; white-space: nowrap; font-weight: normal;'>"
            "      [Phím G: Ẩn/Hiện]"
            "    </td>"
            "  </tr>"
            "</table>"
            "<table width='100%' cellpadding='2' cellspacing='0' style='margin-bottom: 2px;'>"
            "  <tr>"
            "    <td style='color: #4ade80; font-weight: bold; font-size: 11px; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      👌 Chụm Cái + Trỏ"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 11px; font-weight: 500; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      Xoay khối 3D"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #fde047; font-weight: bold; font-size: 11px; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      👍 Giơ ngón cái (0.35s)"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 11px; font-weight: 500; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      Bật/Tắt mở hộp 2D"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #00f0ff; font-weight: bold; font-size: 11px; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      👆 Chỉ 1 ngón trỏ"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 11px; font-weight: 500; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      Tia Laser / Cắt lát"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #e879f9; font-weight: bold; font-size: 11px; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      🤟 3 Ngón tay"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 11px; font-weight: 500; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      Đổi kiểu mặt cắt"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #38bdf8; font-weight: bold; font-size: 11px; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      👐 2 Bàn tay (Xa / Gần)"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 11px; font-weight: 500; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      Thu phóng (Zoom 3D)"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #fb923c; font-weight: bold; font-size: 11px; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      🖐️ Lướt Trái / Phải"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 11px; font-weight: 500; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      Đổi khối hình học"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #f472b6; font-weight: bold; font-size: 11px; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      ✊ Nắm bàn tay"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 11px; font-weight: 500; padding: 3px 2px; border-bottom: 1px solid #182030;'>"
            "      Bật / Tắt xoay 360°"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #a5b4fc; font-weight: bold; font-size: 11px; padding: 3px 2px;'>"
            "      ✌️ Chữ V (2 ngón)"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 11px; font-weight: 500; padding: 3px 2px;'>"
            "      Đặt lại góc nhìn chuẩn"
            "    </td>"
            "  </tr>"
            "</table>"
            "<div style='margin-top: 5px; padding-top: 4px; border-top: 1.5px solid #1f2737; color: #cbd5e1; font-size: 10px; text-align: center;'>"
            "  🖱️ <b>Chuột:</b> Kéo: Xoay | Cuộn: Zoom &nbsp;|&nbsp; ⌨️ <b>Phím:</b> ← / →: Đổi hình"
            "</div>"
        )

    def _toggle_3d_fullscreen(self):
        self.is_3d_fullscreen = not self.is_3d_fullscreen
        self.scroll_control.setVisible(not self.is_3d_fullscreen)
        self.right_sidebar.setVisible(not self.is_3d_fullscreen)
        if hasattr(self, 'toolbar'):
            self.toolbar.setVisible(not self.is_3d_fullscreen)
        self.splitter.setSizes([0, max(800, self.width()), 0] if self.is_3d_fullscreen else [380, 720, 360])
        self.gl_widget.stream_overlay = self.is_3d_fullscreen

        if self.is_3d_fullscreen:
            if self.centralWidget() and self.centralWidget().layout():
                self.centralWidget().layout().setContentsMargins(0, 0, 0, 0)
                self.centralWidget().layout().setSpacing(0)
            if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
                self.showFullScreen()
            if hasattr(self, 'status_bar') and self.status_bar:
                self.status_bar.hide()
        else:
            if self.centralWidget() and self.centralWidget().layout():
                self.centralWidget().layout().setContentsMargins(4, 4, 4, 4)
                self.centralWidget().layout().setSpacing(4)
            if os.environ.get("QT_QPA_PLATFORM") != "offscreen":
                self.showNormal()
            if hasattr(self, 'status_bar') and self.status_bar:
                self.status_bar.show()

        hide_overlays = self.is_3d_fullscreen and getattr(self.gl_widget, 'hologram_box_mode', False)
        self.stream_camera_overlay.setVisible(self.is_3d_fullscreen and not hide_overlays)
        self.stream_status_badge.setVisible(self.is_3d_fullscreen and not hide_overlays)
        self.stream_gesture_guide.setVisible(self.is_3d_fullscreen and not hide_overlays)
        self._reposition_fullscreen_overlays()

        if self.is_3d_fullscreen:
            self.gl_widget.show_toast("F11: TOÀN MÀN HÌNH | Phím F: Fit/Fill | Phím H: Ẩn/Hiện khung | Phím R: Reset", "🖥️", 2500)

        self.lbl_status_info.setText(
            "Vùng 3D toàn màn hình | F11/Esc: Thoát | Phím G: Bảng cử chỉ | M: Lật gương | H: Hộp chiếu"
            if self.is_3d_fullscreen else "Đã trở lại giao diện đầy đủ"
        )
        self.gl_widget.setFocus()
        self.gl_widget.update()

    def _setup_layout(self):
        """Thiết lập bố cục giao diện (Splitter Layout)."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # ScrollArea chứa Bảng điều khiển thông số bên trái
        scroll_control = QScrollArea()
        scroll_control.setWidgetResizable(True)
        scroll_control.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_control.setWidget(self.control_panel)
        scroll_control.setMinimumWidth(380)
        scroll_control.setMaximumWidth(440)
        self.scroll_control = scroll_control

        # Sidebar bên phải chứa Camera Preview Widget
        right_sidebar = QWidget()
        right_layout = QVBoxLayout(right_sidebar)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.addWidget(self.camera_widget)
        right_layout.addStretch()
        right_sidebar.setMinimumWidth(350)
        right_sidebar.setMaximumWidth(390)
        self.right_sidebar = right_sidebar

        # Main Splitter phân chia (Left Controls | Center OpenGL | Right Webcam)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(scroll_control)
        splitter.addWidget(self.gl_widget)
        splitter.addWidget(right_sidebar)

        # Tỷ lệ kích thước mặc định: Controls (Left) | OpenGL (Center) | Camera (Right)
        splitter.setSizes([390, 710, 360])
        self.splitter = splitter

        main_layout.addWidget(splitter)

        # Thanh trạng thái Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.lbl_status_info = QLabel("HOLOGRAM V2.2 (BẢN MỚI NHẤT) | [Lướt tay / ← →]: Đổi hình | [Thumbs-Up]: Mở hộp 2D | [Pinch]: Xoay 3D | [F11]: Toàn Màn Hình")
        self.status_bar.addWidget(self.lbl_status_info)

    def _connect_signals(self):
        """Tích hợp các tín hiệu (Signals & Slots) giữa các phân hệ."""
        # 1. Từ Control Panel tới OpenGL Widget
        self.control_panel.shape_changed.connect(self.gl_widget.set_shape)
        self.control_panel.dimension_changed.connect(self._on_dimension_changed)
        self.control_panel.scale_factor_changed.connect(self.gl_widget.set_scale_factor)
        self.control_panel.color_changed.connect(self.gl_widget.set_color)
        self.control_panel.wireframe_changed.connect(self.gl_widget.set_wireframe)
        self.control_panel.dimension_lines_changed.connect(self.gl_widget.set_dimension_lines)
        self.control_panel.view_mode_changed.connect(self._on_view_mode_changed)
        self.control_panel.auto_rotate_changed.connect(lambda enable: setattr(self.gl_widget, 'auto_rotate', enable))
        if self.camera_thread is not None:
            self.control_panel.sensitivity_changed.connect(lambda sens: setattr(self.camera_thread.tracker, 'sensitivity', sens))
            self.control_panel.camera_source_changed.connect(self.camera_thread.set_camera_source)
        self.control_panel.formula_test_requested.connect(self.open_area_volume_test)

        # Định dạng hiển thị Hologram (Lật gương & Hộp chiếu)
        self.control_panel.mirror_toggled.connect(self._on_mirror_toggled)
        self.control_panel.hologram_box_toggled.connect(self._on_hologram_box_toggled)
        self.control_panel.fit_screen_requested.connect(self.gl_widget.fit_to_screen)
        self.control_panel.fill_screen_requested.connect(self.gl_widget.fill_screen)

        # Kết nối Công cụ Sư phạm 3D (Mặt cắt & Trải phẳng)
        self.control_panel.slicing_toggled.connect(self._on_slicing_toggled)
        self.control_panel.slice_type_changed.connect(self.gl_widget.set_slice_type)
        self.control_panel.slice_offset_changed.connect(self.gl_widget.set_slice_offset)
        self.control_panel.unfold_progress_changed.connect(self.gl_widget.set_unfold_progress)
        self.control_panel.unfold_animate_requested.connect(self._toggle_unfold_animation)
        self.gl_widget.unfold_progress_updated.connect(self._on_unfold_progress_updated)

        # 2. Từ Camera Thread tới Camera Widget & OpenGL Widget (Xử lý tương tác cử chỉ Pinch & stream)
        if self.camera_thread is not None:
            self.camera_thread.frame_processed.connect(self._on_camera_frame_processed)
            self.camera_thread.camera_error.connect(self._on_camera_error)
            self.camera_thread.camera_connected.connect(lambda msg: self.lbl_status_info.setText(f"[Camera] {msg}"))
    def _toggle_mirror_mode(self):
        new_state = self.gl_widget.toggle_mirror_mode()
        self.control_panel.chk_mirror.blockSignals(True)
        self.control_panel.chk_mirror.setChecked(new_state)
        self.control_panel.chk_mirror.blockSignals(False)
        if hasattr(self, 'action_mirror'):
            self.action_mirror.setChecked(new_state)
        toast_msg = "LẬT GƯƠNG ẢNH (DÙNG CHO HỘP CHIẾU 45°)" if new_state else "CHẾ ĐỘ HIỂN THỊ THƯỜNG"
        self.gl_widget.show_toast(toast_msg, "🪞")
        self.lbl_status_info.setText(f"Chế độ Lật gương: {'BẬT (Khử đảo ngược kính 45°)' if new_state else 'TẮT'}")
        if self.is_3d_fullscreen:
            self._reposition_fullscreen_overlays()

    def _on_mirror_toggled(self, checked: bool):
        self.gl_widget.set_mirror_mode(checked)
        if hasattr(self, 'action_mirror'):
            self.action_mirror.setChecked(checked)
        toast_msg = "LẬT GƯƠNG ẢNH (DÙNG CHO HỘP CHIẾU 45°)" if checked else "CHẾ ĐỘ HIỂN THỊ THƯỜNG"
        self.gl_widget.show_toast(toast_msg, "🪞")
        if self.is_3d_fullscreen:
            self._reposition_fullscreen_overlays()

    def _toggle_hologram_box_mode(self):
        new_state = self.gl_widget.toggle_hologram_box_mode()
        self.control_panel.chk_box_mode.blockSignals(True)
        self.control_panel.chk_box_mode.setChecked(new_state)
        self.control_panel.chk_box_mode.blockSignals(False)
        if hasattr(self, 'action_box_mode'):
            self.action_box_mode.setChecked(new_state)
        if self.is_3d_fullscreen:
            self.stream_camera_overlay.setVisible(not new_state)
            self.stream_status_badge.setVisible(not new_state)
            self.stream_gesture_guide.setVisible(not new_state)
        toast_msg = "HOLOGRAM TOÀN MÀN HÌNH: ĐÃ ẨN SẠCH KHUNG VIỀN (BẤM 'H' ĐỂ HIỆN LẠI)" if new_state else "CHẾ ĐỘ ĐẦY ĐỦ: ĐÃ HIỆN LẠI CÁC KHUNG VÀ THẺ CỬ CHỈ"
        self.gl_widget.show_toast(toast_msg, "🌌", 2200)
        self.lbl_status_info.setText(f"Chế độ Hộp chiếu Hologram: {'BẬT (Nền đen tuyền, không viền sáng)' if new_state else 'TẮT'}")

    def _on_hologram_box_toggled(self, checked: bool):
        self.gl_widget.set_hologram_box_mode(checked)
        if hasattr(self, 'action_box_mode'):
            self.action_box_mode.setChecked(checked)
        if self.is_3d_fullscreen:
            self.stream_camera_overlay.setVisible(not checked)
            self.stream_status_badge.setVisible(not checked)
            self.stream_gesture_guide.setVisible(not checked)
        toast_msg = "HOLOGRAM TOÀN MÀN HÌNH: ĐÃ ẨN SẠCH KHUNG VIỀN (BẤM 'H' ĐỂ HIỆN LẠI)" if checked else "CHẾ ĐỘ ĐẦY ĐỦ: ĐÃ HIỆN LẠI CÁC KHUNG VÀ THẺ CỬ CHỈ"
        self.gl_widget.show_toast(toast_msg, "🌌", 2200)

    def _on_slicing_toggled(self, checked: bool):
        self.gl_widget.set_slicing(checked)
        if hasattr(self, 'action_slice') and self.action_slice.isChecked() != checked:
            self.action_slice.setChecked(checked)
        if checked:
            self.lbl_status_info.setText("✂️ Đã kích hoạt chế độ Mặt cắt Không gian 3D")
        else:
            self.lbl_status_info.setText("✨ Đã tắt chế độ Mặt cắt 3D")

    def _toggle_slicing_from_toolbar(self, checked: bool):
        self.control_panel.chk_slicing.setChecked(checked)

    def _toggle_unfold_animation(self):
        is_animating = self.gl_widget.toggle_unfold_animation()
        curr_p = self.gl_widget.unfold_progress
        curr_pct = int(curr_p * 100)

        if is_animating:
            direction_str = "MỞ RA" if self.gl_widget.unfold_direction > 0 else "GẬP LẠI"
            self.lbl_status_info.setText(f"📦 Đang {direction_str} Hoạt hình Trải phẳng 2D ({curr_pct}%)...")
            self.control_panel.btn_unfold_play.setText("⏸ Tạm dừng")
            self.control_panel.btn_unfold_play.setStyleSheet(
                "background-color: #854d0e; border: 1.5px solid #eab308; color: #fde047; font-weight: bold; padding: 7px 12px; border-radius: 6px;"
            )
            self.gl_widget.show_toast(f"MỞ HỘP 2D: ĐANG {direction_str} ({curr_pct}%)", "📦", 1800)
        else:
            self.lbl_status_info.setText(f"✨ Đã tạm dừng Hoạt hình Trải phẳng tại {curr_pct}%")
            btn_text = "▶ Gập lại thành 3D" if curr_p >= 0.999 else ("▶ Mở bung 2D" if curr_p <= 0.001 else "▶ Tiếp tục chạy")
            self.control_panel.btn_unfold_play.setText(btn_text)
            self.control_panel.btn_unfold_play.setStyleSheet(
                "background-color: #0c4a6e; border: 1.5px solid #0284c7; color: #38bdf8; font-weight: bold; padding: 7px 12px; border-radius: 6px;"
            )
            self.gl_widget.show_toast(f"MỞ HỘP 2D: TẠM DỪNG TẠI {curr_pct}%", "⏸️", 1800)

    def _on_unfold_progress_updated(self, progress: float):
        self.control_panel.slider_unfold.blockSignals(True)
        self.control_panel.slider_unfold.setValue(int(progress * 100))
        self.control_panel.lbl_unfold_val.setText(f"{int(progress * 100)}%")
        self.control_panel.slider_unfold.blockSignals(False)

        # Cập nhật trạng thái nút bấm khi hoàn thành mở/gập
        if not self.gl_widget.unfold_animating:
            btn_text = "▶ Gập lại thành 3D" if progress >= 0.999 else "▶ Chạy Hoạt hình Trải phẳng"
            self.control_panel.btn_unfold_play.setText(btn_text)
            self.control_panel.btn_unfold_play.setStyleSheet(
                "background-color: #0c4a6e; border: 1.5px solid #0284c7; color: #38bdf8; font-weight: bold; padding: 7px 12px; border-radius: 6px;"
            )
            if progress >= 0.999:
                self.lbl_status_info.setText("📐 Đã trải phẳng 2D hoàn toàn (100%) | 👍 Giơ ngón cái để gập lại 3D")
            elif progress <= 0.001:
                self.lbl_status_info.setText("🧊 Đã gập lại thành khối 3D (0%) | 👍 Giơ ngón cái để mở bung 2D")

    def open_formula_test(self):
        d=QDialog(self); d.setWindowTitle("Sinh hình từ thông số"); d.resize(430,250)
        form=QFormLayout(d); combo=QComboBox()
        items=[("Khối lập phương","cube"),("Hình chóp","pyramid"),("Khối cầu","sphere"),("Hình trụ","cylinder"),("Hình nón","cone"),("Hình hộp chữ nhật","rectangular_prism")]
        for n,k in items: combo.addItem(n,k)
        form.addRow("Chọn khối hình:",combo)
        size=QLineEdit("10"); height=QLineEdit("12")
        form.addRow("Cạnh / bán kính (cm):",size); form.addRow("Chiều cao (cm):",height)
        formula=QLabel(); formula.setStyleSheet("color:#ffe45c;font-size:18px;font-weight:bold;padding:6px 0;"); form.addRow("Công thức:",formula)
        formulas={"cube":"V = a³","pyramid":"V = ⅓ · a² · h","sphere":"V = ⁴⁄₃πR³","cylinder":"V = πR²h","cone":"V = ⅓πR²h","rectangular_prism":"V = abc"}
        def update(): formula.setText(formulas[combo.currentData()])
        combo.currentIndexChanged.connect(update); update()
        btn=QPushButton("✨ Tạo hình từ thông số"); form.addRow(btn)
        def generate():
            try: a=float(size.text().replace(',','.')); h=float(height.text().replace(',','.'))
            except ValueError: QMessageBox.warning(d,"Lỗi","Vui lòng nhập kích thước bằng số."); return
            self.gl_widget.set_shape(combo.currentData()); self._on_dimension_changed(a,h); d.accept()
        btn.clicked.connect(generate); d.exec()

    def open_area_volume_test(self):
        d=QDialog(self); d.setWindowTitle("Kiểm thử diện tích và thể tích"); d.resize(560,430)
        d.setStyleSheet("""
            QDialog { background:#111827; color:#e5e7eb; }
            QLabel { color:#dbeafe; font-size:14px; }
            QLineEdit, QComboBox { background:#1f2937; color:#ffffff; border:1px solid #4b5563; border-radius:6px; padding:8px; font-size:15px; }
            QComboBox QAbstractItemView { background:#1f2937; color:#ffffff; selection-background-color:#0e7490; selection-color:#ffffff; border:1px solid #22d3ee; padding:4px; }
            QLineEdit:focus, QComboBox:focus { border:2px solid #22d3ee; }
            QPushButton { background:#164e63; color:white; border:1px solid #22d3ee; border-radius:7px; padding:9px; font-size:14px; font-weight:bold; }
            QPushButton:hover { background:#0891b2; }
        """)
        form=QFormLayout(d); form.setContentsMargins(22,20,22,20); form.setVerticalSpacing(13); combo=QComboBox(); items=[("Khối lập phương","cube"),("Hình chóp","pyramid"),("Khối cầu","sphere"),("Hình trụ","cylinder"),("Hình nón","cone"),("Hình hộp chữ nhật","rectangular_prism")]
        for n,k in items: combo.addItem(n,k)
        form.addRow("Chọn khối hình:",combo)
        size=QLineEdit("10"); width=QLineEdit("8"); height=QLineEdit("12")
        label_size=QLabel("Cạnh / bán kính (cm):")
        label_width=QLabel("Chiều rộng (cm):")
        label_height=QLabel("Chiều cao (cm):")
        form.addRow(label_size, size)
        form.addRow(label_width, width)
        form.addRow(label_height, height)
        formula=QLabel(); formula.setWordWrap(True); formula.setStyleSheet("color:#39e75f;font-size:18px;font-weight:bold;background:#052e2b;border:1px solid #22c55e;border-radius:6px;padding:9px"); form.addRow("Công thức:",formula)
        area=QLineEdit(); volume=QLineEdit(); form.addRow("Diện tích em tính:",area); form.addRow("Thể tích em tính:",volume)
        result=QLabel(); result.setWordWrap(True); form.addRow("Kết quả:",result)
        buttons=QHBoxLayout(); check=QPushButton("✅ Kiểm tra"); generate=QPushButton("✨ Tạo hình 3D"); buttons.addWidget(check); buttons.addWidget(generate); form.addRow(buttons)
        import math
        def values():
            a=float(size.text().replace(',','.')); h=float(height.text().replace(',','.')); k=combo.currentData()
            if k=='cube': return 'S=6a² | V=a³',6*a*a,a**3
            if k=='pyramid':
                l=math.sqrt(h*h+(a/2)**2); return 'Sđ=a²; Sxq=2al; V=⅓a²h',a*a+2*a*l,a*a*h/3
            if k=='sphere': return 'S=4πR² | V=⁴⁄₃πR³',4*math.pi*a*a,4*math.pi*a**3/3
            if k=='cylinder': return 'Stp=2πR(R+h) | V=πR²h',2*math.pi*a*(a+h),math.pi*a*a*h
            if k=='cone':
                l=math.sqrt(a*a+h*h); return 'Stp=πR(R+l) | V=⅓πR²h',math.pi*a*(a+l),math.pi*a*a*h/3
            b=float(width.text().replace(',','.')); return 'Stp=2(ab+bc+ca) | V=abc',2*(a*b+b*h+a*h),a*b*h
        def update():
            k=combo.currentData(); formula.setText(values()[0].replace(' | ', '\n'))
            is_box = k == 'rectangular_prism'
            label_width.setVisible(is_box); width.setVisible(is_box)
            has_height = k not in ('cube','sphere')
            label_height.setVisible(has_height); height.setVisible(has_height)
            label_size.setText({'cube':'Cạnh a (cm):','sphere':'Bán kính R (cm):','rectangular_prism':'Chiều dài (cm):'}.get(k,'Cạnh / bán kính (cm):'))
        combo.currentIndexChanged.connect(update); update()
        def do_check():
            try:
                _,s,v=values(); sa=float(area.text().replace(',','.')); sv=float(volume.text().replace(',','.')); ok1=abs(sa-s)<=max(.1,s*.01); ok2=abs(sv-v)<=max(.1,v*.01); result.setText(f"Diện tích: {'ĐÚNG' if ok1 else 'SAI'} | Đáp án {s:.2f} cm²\nThể tích: {'ĐÚNG' if ok2 else 'SAI'} | Đáp án {v:.2f} cm³")
            except ValueError: result.setText('Vui lòng nhập số hợp lệ.')
        def do_generate():
            try: a=float(size.text().replace(',','.')); h=float(height.text().replace(',','.'))
            except ValueError: result.setText('Kích thước phải là số.'); return
            self.gl_widget.set_shape(combo.currentData()); self._on_dimension_changed(a,h)
            geom = self.gl_widget.get_current_geometry()
            if hasattr(geom, 'width_cm'):
                geom.width_cm = float(width.text().replace(',', '.'))
            d.accept()
        check.clicked.connect(do_check); generate.clicked.connect(do_generate); d.exec()

    def _on_dimension_changed(self, size_cm: float, height_cm: float):
        """Cập nhật kích thước thực tế cho đối tượng 3D hiện tại."""
        geom = self.gl_widget.get_current_geometry()
        
        if hasattr(geom, 'side_length_cm'):
            geom.side_length_cm = size_cm
        if hasattr(geom, 'base_size_cm'):
            geom.base_size_cm = size_cm
        if hasattr(geom, 'radius_cm'):
            geom.radius_cm = size_cm
        if hasattr(geom, 'height_cm'):
            geom.height_cm = height_cm
        if hasattr(geom, 'major_radius_cm'):
            geom.major_radius_cm = size_cm
            geom.minor_radius_cm = size_cm * 0.3
        if hasattr(geom, 'length_cm'):
            geom.length_cm = size_cm
        if hasattr(geom, 'width_cm'):
            geom.width_cm = size_cm * 0.7

        self.gl_widget.update()

    def _on_view_mode_changed(self, mode: str):
        """Thay đổi chế độ xem Single View vs 4-View Hologram Pyramid."""
        self.gl_widget.view_mode = mode
        self.gl_widget.update()
        
        mode_str = "4-View Pyramid Hologram Cross" if mode == 'pyramid' else "Single 3D Preview"
        self.lbl_status_info.setText(f"Chế độ hiển thị: {mode_str}")

    def _on_camera_frame_processed(self, frame: np.ndarray, gesture_data: dict):
        """Slot nhận khung hình webcam & dữ liệu tương tác bàn tay từ QThread."""
        now = time.time()

        # 1. Cập nhật giao diện camera preview widget
        self.camera_widget.update_frame(frame, gesture_data)

        # Cập nhật huy hiệu trạng thái cử chỉ trên giao diện Fullscreen
        if gesture_data.get('gesture_name') == "CAMERA OFFLINE":
            self._update_stream_status_badge("⚠️ CAMERA OFFLINE", "#3b1219", "#991b1b", "#fca5a5")
        elif not gesture_data.get('hand_detected', False):
            self._update_stream_status_badge("🖐️ Chưa phát hiện bàn tay", "#2b1117", "#85222b", "#ff7b82")
        else:
            g_name = gesture_data.get('gesture_name', '')
            if gesture_data.get('toggle_unfold', False):
                self._update_stream_status_badge("📦 ĐÃ BẬT/TẮT MỞ HỘP 2D", "#164e63", "#06b6d4", "#67e8f9")
            elif "GIỮ NGÓN CÁI" in g_name or "GIỮ XÒE TAY" in g_name or "NGÓN CÁI" in g_name:
                self._update_stream_status_badge(g_name, "#0c4a6e", "#0284c7", "#7dd3fc")
            elif gesture_data.get('is_two_hand_zoom', False):
                delta = gesture_data.get('delta_zoom', 0.0)
                sign = "+" if delta >= 0 else ""
                self._update_stream_status_badge(f"🔍 ZOOM 2 TAY | Δ: {sign}{delta:.2f}", "#082b33", "#0e7490", "#22d3ee")
            elif gesture_data.get('is_pointing', False):
                sl = gesture_data.get('slice_offset', 0.0)
                self._update_stream_status_badge(f"👆 AIR POINTER | CẮT: {sl:+.2f}", "#062e36", "#06b6d4", "#67e8f9")
            elif gesture_data.get('cycle_slice_type', False):
                self._update_stream_status_badge("🤟 3 NGÓN: ĐỔI MẶT CẮT", "#2e1045", "#9333ea", "#e9d5ff")
            elif gesture_data.get('is_pinching', False):
                self._update_stream_status_badge("👌 ĐANG XOAY 3D", "#0d2b1a", "#15803d", "#4ade80")
            elif gesture_data.get('swipe_direction'):
                direction = "TIẾP THEO" if gesture_data['swipe_direction'] == 'left' else "TRƯỚC ĐÓ"
                self._update_stream_status_badge(f"🖐️ LƯỚT TAY: {direction}", "#331c0a", "#c2410c", "#fb923c")
            elif gesture_data.get('toggle_auto_rotate'):
                self._update_stream_status_badge("✊ NẮM TAY: ĐẢO XOAY 360°", "#331024", "#be185d", "#f472b6")
            elif gesture_data.get('reset_view'):
                self._update_stream_status_badge("✌️ CHỮ V: ĐẶT LẠI GÓC NHÌN", "#141c38", "#2563eb", "#a5b4fc")
            else:
                display_name = g_name if g_name else "SẴN SÀNG"
                self._update_stream_status_badge(f"✋ {display_name}", "#0d2238", "#1d4ed8", "#38bdf8")

        # Cập nhật webcam mini trong khung stream 3D.
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        image = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(image).scaled(
            self.stream_camera_overlay.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.stream_camera_overlay.setPixmap(pixmap)

        primary_gesture = gesture_data.get('primary_gesture', 'none')

        # 2. Xử lý cử chỉ PHÓNG TO / THU NHỎ (Zoom 2 tay)
        if primary_gesture == 'zoom_2hand' or gesture_data.get('is_two_hand_zoom', False):
            delta_zoom = gesture_data.get('delta_zoom', 0.0)
            if abs(delta_zoom) > 0.001:
                self.gl_widget.update_zoom(delta_zoom)
            self.gl_widget.clear_pointer()
            return

        # 3. Cử chỉ XOAY 3D (Ngón cái + Ngón trỏ) -> Xoay Yaw & Pitch
        if primary_gesture == 'pinch_rotate' or gesture_data.get('is_pinching', False):
            delta_yaw = gesture_data.get('delta_yaw', 0.0)
            delta_pitch = gesture_data.get('delta_pitch', 0.0)
            if abs(delta_yaw) > 0.001 or abs(delta_pitch) > 0.001:
                self.gl_widget.update_rotation(delta_yaw, delta_pitch)
            self.gl_widget.clear_pointer()
            return

        # 4. Cử chỉ CHỈ TAY (3D Air Laser Pointer & Air Slice Offset)
        if primary_gesture == 'pointing' or gesture_data.get('is_pointing', False):
            norm_pos = gesture_data.get('pointer_pos')
            if norm_pos:
                self.gl_widget.set_pointer(norm_pos[0], norm_pos[1])

            # Nếu đang bật chế độ Mặt cắt 3D, điều khiển vị trí mặt cắt theo độ cao ngón trỏ
            if self.gl_widget.slicing_enabled and gesture_data.get('is_slicing_gesture', False):
                slice_offset = gesture_data.get('slice_offset', 0.0)
                self.gl_widget.set_slice_offset(slice_offset)
                self.control_panel.slider_slice_offset.blockSignals(True)
                self.control_panel.slider_slice_offset.setValue(int(slice_offset * 100))
                self.control_panel.lbl_slice_offset_val.setText(f"{slice_offset:+.2f}")
                self.control_panel.slider_slice_offset.blockSignals(False)
        else:
            self.gl_widget.clear_pointer()

        # =========================================================
        # XỬ LÝ CÁC HÀNH ĐỘNG RỜI RẠC (DISCRETE ACTIONS) ĐỘC QUYỀN
        # Có khóa đệm toàn cục (Global Action Lock) chống kích hoạt chéo
        # =========================================================
        if now - self.last_discrete_action_time < self.discrete_action_cooldown:
            return

        # 5. Cử chỉ MỞ HỘP 2D (👍 Giơ ngón cái giữ 0.35s)
        if gesture_data.get('toggle_unfold', False):
            self.last_discrete_action_time = now
            self._toggle_unfold_animation()

        # 6. Cử chỉ 3 NGÓN TAY (Chuyển kiểu Mặt cắt: Ngang -> Dọc -> Xiên)
        elif gesture_data.get('cycle_slice_type', False):
            self.last_discrete_action_time = now
            if not self.control_panel.chk_slicing.isChecked():
                self.control_panel.chk_slicing.setChecked(True)
            curr_idx = self.control_panel.combo_slice_type.currentIndex()
            next_idx = (curr_idx + 1) % self.control_panel.combo_slice_type.count()
            self.control_panel.combo_slice_type.setCurrentIndex(next_idx)
            slice_name = self.control_panel.combo_slice_type.currentText()
            self.gl_widget.show_toast(f"MẶT CẮT: {slice_name}", "🔪")
            self.lbl_status_info.setText(f"🤟 Cử chỉ 3 Ngón: Đổi mặt cắt sang {slice_name}")

        # 7. Cử chỉ LƯỚT TAY (Swipe Left / Right -> Đổi khối hình học)
        elif gesture_data.get('swipe_direction'):
            self.last_discrete_action_time = now
            swipe = gesture_data.get('swipe_direction')
            if swipe == 'left':
                shape_name = self.control_panel.next_shape()
                self.gl_widget.show_toast(f"ĐÃ ĐỔI: {shape_name}", "✨")
                self.lbl_status_info.setText(f"🖐️ Cử chỉ Lướt tay Trái: Đổi sang {shape_name}")
            elif swipe == 'right':
                shape_name = self.control_panel.prev_shape()
                self.gl_widget.show_toast(f"ĐÃ ĐỔI: {shape_name}", "✨")
                self.lbl_status_info.setText(f"🖐️ Cử chỉ Lướt tay Phải: Quay lại {shape_name}")

        # 8. Cử chỉ NẮM TAY (Fist -> Bật / Tắt Tự động xoay 360°)
        elif gesture_data.get('toggle_auto_rotate', False):
            self.last_discrete_action_time = now
            is_rotating = self.control_panel.toggle_auto_rotate()
            status_str = "BẬT" if is_rotating else "TẮT"
            self.gl_widget.show_toast(f"TỰ ĐỘNG XOAY: {status_str}", "🔄" if is_rotating else "⏸️")
            self.lbl_status_info.setText(f"✊ Cử chỉ Nắm tay: Tự động xoay 360° {status_str}")

        # 9. Cử chỉ CHỮ V (Peace Sign ✌️ -> Đặt lại góc nhìn chuẩn)
        elif gesture_data.get('reset_view', False):
            self.last_discrete_action_time = now
            self.gl_widget.reset_view()
            self.gl_widget.show_toast("ĐẶT LẠI GÓC NHÌN CHUẨN", "🎯")
            self.lbl_status_info.setText("✌️ Cử chỉ Chữ V: Đặt lại góc nhìn mặc định")

    def _on_camera_error(self, err_msg: str):
        """Xử lý sự cố kết nối Webcam."""
        self.lbl_status_info.setText(f"⚠️ {err_msg}")

    def closeEvent(self, event):
        """Dừng Thread camera an toàn khi đóng ứng dụng."""
        if self.camera_thread is not None:
            self.camera_thread.stop()
        event.accept()
