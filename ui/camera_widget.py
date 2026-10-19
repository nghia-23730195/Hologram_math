# -*- coding: utf-8 -*-
"""
ui/camera_widget.py
-------------------
Widget hiển thị luồng video từ Webcam kèm chỉ báo nhận diện bàn tay MediaPipe,
khoảng cách Pinch và trạng thái tương tác thời gian thực.
"""

import cv2
import numpy as np
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QFrame
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import Qt


class CameraPreviewWidget(QFrame):
    """Widget xem trước Webcam & Trạng thái Cử chỉ."""
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #12141c;
                border: 1px solid #2a2e3d;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # Tiêu đề Widget
        self.title_label = QLabel("📹 Live Webcam & Hand Tracker")
        self.title_label.setStyleSheet("color: #00f0ff; font-weight: bold; font-size: 14px; border: none; padding-bottom: 2px;")
        layout.addWidget(self.title_label)

        # Nhãn hiển thị khung hình OpenCV (Image Label)
        self.image_label = QLabel()
        self.image_label.setFixedSize(320, 240)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("border: 1.5px solid #233247; background-color: #000; border-radius: 6px;")
        layout.addWidget(self.image_label)

        # Nhãn báo trạng thái cử chỉ (Badge pill hiện đại)
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._set_status_badge("⏳ Khởi động Webcam...", "#121824", "#2a3b59", "#94a3b8")
        layout.addWidget(self.status_label)

        # Bảng hướng dẫn cử chỉ AI (Trình bày dạng bảng thẻ trực quan, tương phản cao)
        self.gesture_help = QLabel(
            "<div style='margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1.5px solid #232d3f;'>"
            "  <span style='color: #00f0ff; font-weight: bold; font-size: 13px; letter-spacing: 0.5px;'>"
            "    🎮 BẢNG CỬ CHỈ ĐIỀU KHIỂN (AI)"
            "  </span>"
            "</div>"
            "<table width='100%' cellpadding='4' cellspacing='0' style='margin-bottom: 2px;'>"
            "  <tr>"
            "    <td style='color: #4ade80; font-weight: bold; font-size: 13px; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      👌 Chụm Cái + Trỏ"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 13px; font-weight: 500; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      Xoay khối 3D"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #fde047; font-weight: bold; font-size: 13px; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      👍 Giơ ngón cái (0.35s)"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 13px; font-weight: 500; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      Bật/Tắt mở hộp 2D"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #00f0ff; font-weight: bold; font-size: 13px; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      👆 Chỉ 1 ngón trỏ"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 13px; font-weight: 500; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      Tia Laser 3D / Cắt lát"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #e879f9; font-weight: bold; font-size: 13px; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      🤟 3 Ngón tay"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 13px; font-weight: 500; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      Đổi mặt cắt (Ngang/Dọc/Xiên)"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #38bdf8; font-weight: bold; font-size: 13px; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      👐 2 Bàn tay (Xa / Gần)"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 13px; font-weight: 500; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      Thu phóng (Zoom 3D)"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #fb923c; font-weight: bold; font-size: 13px; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      🖐️ Lướt Trái / Phải"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 13px; font-weight: 500; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      Đổi khối hình học"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #f472b6; font-weight: bold; font-size: 13px; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      ✊ Nắm bàn tay"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 13px; font-weight: 500; padding: 5px 2px; border-bottom: 1px solid #182030;'>"
            "      Bật / Tắt xoay 360°"
            "    </td>"
            "  </tr>"
            "  <tr>"
            "    <td style='color: #a5b4fc; font-weight: bold; font-size: 13px; padding: 5px 2px;'>"
            "      ✌️ Chữ V (2 ngón)"
            "    </td>"
            "    <td style='color: #f8fafc; text-align: right; font-size: 13px; font-weight: 500; padding: 5px 2px;'>"
            "      Đặt lại góc nhìn chuẩn"
            "    </td>"
            "  </tr>"
            "</table>"
            "<div style='margin-top: 8px; padding-top: 6px; border-top: 1.5px solid #1f2737; color: #cbd5e1; font-size: 12px; text-align: center;'>"
            "  🖱️ <b>Chuột:</b> Kéo trái: Xoay &nbsp;|&nbsp; Con lăn: Zoom"
            "</div>"
        )
        self.gesture_help.setWordWrap(True)
        self.gesture_help.setStyleSheet(
            "QLabel {"
            "  background-color: #0b0e14;"
            "  border: 1.5px solid #232b3b;"
            "  border-radius: 8px;"
            "  padding: 10px 14px;"
            "}"
        )
        layout.addWidget(self.gesture_help)

    def _set_status_badge(self, text: str, bg_color: str, border_color: str, text_color: str):
        """Thiết lập nhãn trạng thái theo phong cách pill badge hiện đại với độ tương phản cao."""
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                border: 1.5px solid {border_color};
                color: {text_color};
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                padding: 8px 12px;
            }}
        """)

    def update_frame(self, frame_bgr: np.ndarray, gesture_data: dict):
        """Cập nhật ảnh khung hình và hiển thị dữ liệu cử chỉ."""
        # Chuyển đổi BGR OpenCV sang RGB QImage
        h, w, ch = frame_bgr.shape
        bytes_per_line = ch * w
        rgb_image = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        q_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888).copy()

        # Scale vừa vặn QLabel 320x240
        pixmap = QPixmap.fromImage(q_img).scaled(
            self.image_label.width(), self.image_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(pixmap)

        # Cập nhật nhãn trạng thái cử chỉ (Status Indicator Badge)
        if gesture_data.get('gesture_name') == "CAMERA OFFLINE":
            self._set_status_badge("⚠️ Camera Offline (Đổi Camera 1 / Cấp quyền Win)", "#3b1219", "#991b1b", "#fca5a5")
        elif not gesture_data.get('hand_detected', False):
            self._set_status_badge("🖐️ Chưa phát hiện bàn tay", "#2b1117", "#85222b", "#ff7b82")
        else:
            g_name = gesture_data.get('gesture_name', '')
            if gesture_data.get('toggle_unfold', False):
                self._set_status_badge("📦 ĐÃ BẬT/TẮT MỞ HỘP 2D", "#164e63", "#06b6d4", "#67e8f9")
            elif "GIỮ NGÓN CÁI" in g_name or "GIỮ XÒE TAY" in g_name or "NGÓN CÁI" in g_name:
                self._set_status_badge(g_name, "#0c4a6e", "#0284c7", "#7dd3fc")
            elif gesture_data.get('is_two_hand_zoom', False):
                delta = gesture_data.get('delta_zoom', 0.0)
                sign = "+" if delta >= 0 else ""
                self._set_status_badge(f"🔍 ZOOM 2 TAY | Δ: {sign}{delta:.2f}", "#082b33", "#0e7490", "#22d3ee")
            elif gesture_data.get('is_pointing', False):
                sl = gesture_data.get('slice_offset', 0.0)
                self._set_status_badge(f"👆 AIR POINTER | CẮT LÁT: {sl:+.2f}", "#062e36", "#06b6d4", "#67e8f9")
            elif gesture_data.get('cycle_slice_type', False):
                self._set_status_badge("🤟 3 NGÓN: ĐỔI MẶT CẮT", "#2e1045", "#9333ea", "#e9d5ff")
            elif gesture_data.get('is_pinching', False):
                dist = gesture_data.get('pinch_distance', 0.0)
                self._set_status_badge(f"👌 ĐANG XOAY 3D (Dist: {dist:.3f})", "#0d2b1a", "#15803d", "#4ade80")

            elif gesture_data.get('swipe_direction'):
                direction = "TIẾP THEO (TRÁI)" if gesture_data['swipe_direction'] == 'left' else "TRƯỚC ĐÓ (PHẢI)"
                self._set_status_badge(f"🖐️ LƯỚT TAY: {direction}", "#331c0a", "#c2410c", "#fb923c")
            elif gesture_data.get('toggle_auto_rotate'):
                self._set_status_badge("✊ NẮM TAY: ĐẢO XOAY 360°", "#331024", "#be185d", "#f472b6")
            elif gesture_data.get('reset_view'):
                self._set_status_badge("✌️ CHỮ V: ĐẶT LẠI GÓC NHÌN", "#141c38", "#2563eb", "#a5b4fc")
            else:
                display_name = g_name if g_name else "SẴN SÀNG"
                self._set_status_badge(f"✋ {display_name}", "#0d2238", "#1d4ed8", "#38bdf8")
