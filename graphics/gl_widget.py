"""
graphics/gl_widget.py
---------------------
QOpenGLWidget chuyên dụng hiển thị không gian 3D Hologram.
Hỗ trợ 2 chế độ hiển thị:
1. Single View: Xem thử 1 camera góc nhìn trực diện.
2. 4-View Hologram Pyramid: Chia thành 4 viewport tạo hình chữ thập (Cross Layout)
   được thiết kế chuẩn cho thiết bị chiếu Kim tự tháp Hologram 4 mặt.

Đặc tính quan trọng:
- Background mặc định: Pitch Black (#000000).
- Alpha Blending: Hỗ trợ vật thể bán trong suốt.
- Nhận giá trị Pitch & Yaw từ cử chỉ MediaPipe thời gian thực.
"""

import time
import math
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt6.QtGui import QMouseEvent, QWheelEvent, QPainter, QColor, QFont, QPen
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective, gluLookAt, gluProject

from graphics.geometry import (
    CubeGeometry, PyramidGeometry, SphereGeometry, CylinderGeometry, TorusGeometry, ConeGeometry, RectangularPrismGeometry, SphericalSectionGeometry
)
from graphics.lighting import setup_hologram_lighting


class HologramGLWidget(QOpenGLWidget):
    """OpenGL Render Widget cho màn hình chiếu Hologram."""
    unfold_progress_updated = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Chế độ hiển thị: 'single' (1 góc nhìn) hoặc 'pyramid' (4 góc nhìn chữ thập)
        self.view_mode = 'pyramid'

        # Danh sách các khối hình 3D khởi tạo sẵn
        self.geometries = {
            'cube': CubeGeometry(side_length_cm=10.0),
            'pyramid': PyramidGeometry(base_size_cm=10.0, height_cm=12.0),
            'sphere': SphereGeometry(radius_cm=6.0),
            'cylinder': CylinderGeometry(radius_cm=5.0, height_cm=10.0),
            'torus': TorusGeometry(major_radius_cm=6.0, minor_radius_cm=2.0)
            , 'cone': ConeGeometry()
            , 'rectangular_prism': RectangularPrismGeometry()
            , 'spherical_section': SphericalSectionGeometry()
        }
        self.current_shape_key = 'cube'
        self.stream_overlay = False

        # Chế độ Mặt cắt Không gian 3D (Interactive Slicing Plane)
        self.slicing_enabled = False
        self.slice_type = 'horizontal'  # 'horizontal', 'axial', 'oblique'
        self.slice_offset = 0.0          # -1.0 đến 1.0

        # Chế độ Hoạt hình Trải phẳng 2D (Unfolding Net Animation)
        self.unfold_progress = 0.0       # 0.0 (3D) -> 1.0 (2D phẳng)
        self.unfold_animating = False
        self.unfold_direction = 1        # 1: mở ra, -1: gập lại
        self.unfold_timer = QTimer(self)
        self.unfold_timer.timeout.connect(self._step_unfold_animation)

        # Ma trận biến đổi phục vụ chiếu nhãn kích thước động
        self.last_modelview = None
        self.last_projection = None
        self.last_viewport = None

        # Góc xoay của vật thể (Pitch: quanh trục X, Yaw: quanh trục Y, Roll: quanh trục Z)
        self.pitch = 15.0
        self.yaw = 30.0
        self.roll = 0.0

        # Xoay tự động (Auto-rotation toggle)
        self.auto_rotate = False
        self.auto_rotate_speed = 0.8

        # Optical FOV Zoom & Khoảng cách Camera (Thu phóng quang học không giới hạn)
        self.camera_distance = 6.0       # Vị trí camera an toàn cố định ngoài vật thể
        self.zoom_factor = 1.0           # 1.0x (chuẩn), 2.2x (fit 85%), 4.5x (fill 100% màn hình 16:9)
        self.zoom_min = 0.2              # Thu nhỏ tối đa (0.2x)
        self.zoom_max = 10.0             # Phóng to cực đại (10.0x)
        self.zoom_sensitivity = 0.02     # Độ nhạy zoom cử chỉ bàn tay

        # Mouse interaction backup
        self.last_mouse_pos = None

        # Toast HUD Notification
        self.toast_message = ""
        self.toast_icon = ""
        self.toast_expire = 0.0

        # Cyberpunk 3D Air Laser Pointer
        self.pointer_pos = None      # (norm_x, norm_y) hoặc None
        self.pointer_active = False
        self.pointer_last_time = 0.0

        # Chế độ Chiếu Hộp Hologram (Pepper's Ghost 45° Box & Lật gương)
        self.mirror_mode = False          # True: Lật gương trục X cho phản xạ kính 45°
        self.hologram_box_mode = False    # True: Ẩn viền Cyan ngoài, đen tuyền Pitch Black

        # Timer cập nhật frame (60 FPS)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(16)

    def set_pointer(self, norm_x: float, norm_y: float):
        """Cập nhật tọa độ con trỏ Laser Air Pointer (chuẩn hóa 0.0 -> 1.0)."""
        if norm_x is not None and norm_y is not None:
            self.pointer_pos = (norm_x, norm_y)
            self.pointer_active = True
            self.pointer_last_time = time.time()
        else:
            self.pointer_active = False
            self.pointer_pos = None
        self.update()

    def clear_pointer(self):
        """Ẩn con trỏ Air Laser Pointer."""
        self.pointer_active = False
        self.pointer_pos = None
        self.update()

    def set_shape(self, shape_key: str):
        """Thay đổi loại hình học đang hiển thị."""
        if shape_key in self.geometries:
            self.current_shape_key = shape_key
            self.update()

    def get_current_geometry(self):
        return self.geometries[self.current_shape_key]

    def set_color(self, r: float, g: float, b: float, a: float = 1.0):
        """Cấu hình màu sắc và độ trong suốt cho tất cả hình học."""
        for geom in self.geometries.values():
            geom.set_color(r, g, b, a)
        self.update()

    def set_zoom_factor(self, factor: float):
        """Đặt hệ số thu phóng quang học (0.2x đến 10.0x)."""
        self.zoom_factor = max(self.zoom_min, min(self.zoom_max, factor))
        self.camera_distance = 6.0 / max(0.01, self.zoom_factor)
        self.update()

    def reset_view(self):
        """Đặt lại góc nhìn và tỷ lệ zoom về chuẩn mặc định (100%)."""
        self.pitch = 15.0
        self.yaw = 30.0
        self.roll = 0.0
        self.set_zoom_factor(1.0)
        self.update()

    def fit_to_screen(self):
        """Căn chỉnh sao cho vật thể 3D to vừa vặn màn hình (chiếm ~85% chiều cao)."""
        self.pitch = 15.0
        self.yaw = 30.0
        self.roll = 0.0
        self.set_zoom_factor(2.2)
        self.show_toast("VỪA KHÍT MÀN HÌNH (FIT 85%)", "⛶", 1600)
        self.update()

    def fill_screen(self):
        """Phóng to cực đại tràn toàn màn hình 16:9 (chiếm 100% chiều ngang, tràn viền không viền đen)."""
        self.pitch = 0.0
        self.yaw = 0.0
        self.roll = 0.0
        self.set_zoom_factor(4.5)
        self.show_toast("TRÀN TOÀN BỘ MÀN HÌNH (FILL 100%)", "🔲", 1800)
        self.update()

    def zoom_in(self, step: float = 1.15):
        """Phóng to thêm một nấc."""
        self.set_zoom_factor(self.zoom_factor * step)
        pct = int(self.zoom_factor * 100)
        self.show_toast(f"PHÓNG TO: {pct}%", "🔍", 900)

    def zoom_out(self, step: float = 1.15):
        """Thu nhỏ bớt một nấc."""
        self.set_zoom_factor(self.zoom_factor / step)
        pct = int(self.zoom_factor * 100)
        self.show_toast(f"THU NHỎ: {pct}%", "🔎", 900)

    def toggle_mirror_mode(self) -> bool:
        """Đảo trạng thái lật gương hiển thị (cho hộp chiếu Hologram kính 45 độ)."""
        self.mirror_mode = not self.mirror_mode
        self.update()
        return self.mirror_mode

    def set_mirror_mode(self, enabled: bool):
        """Bật/tắt chế độ lật gương hiển thị."""
        self.mirror_mode = enabled
        self.update()

    def toggle_hologram_box_mode(self) -> bool:
        """Đảo trạng thái chế độ Hộp Hologram (nền đen tuyền không viền sáng)."""
        self.hologram_box_mode = not self.hologram_box_mode
        self.update()
        return self.hologram_box_mode

    def set_hologram_box_mode(self, enabled: bool):
        """Bật/tắt chế độ Hộp Hologram."""
        self.hologram_box_mode = enabled
        self.update()

    def toggle_auto_rotate(self) -> bool:
        """Đảo trạng thái tự động xoay 360 độ."""
        self.auto_rotate = not self.auto_rotate
        self.update()
        return self.auto_rotate

    def show_toast(self, message: str, icon: str = "", duration_ms: int = 1600):
        """Hiển thị thông báo Toast HUD phong cách Cyberpunk trên màn hình OpenGL."""
        self.toast_message = message
        self.toast_icon = icon
        self.toast_expire = time.time() + (duration_ms / 1000.0)
        self.update()

    def set_slicing(self, enable: bool):
        """Bật/tắt chế độ cắt mặt phẳng không gian 3D."""
        self.slicing_enabled = enable
        if enable and self.unfold_progress > 0:
            self.set_unfold_progress(0.0)
        self.update()

    def set_slice_type(self, slice_type: str):
        """Chọn kiểu mặt cắt: 'horizontal', 'axial', 'oblique'."""
        self.slice_type = slice_type
        self.update()

    def set_slice_offset(self, offset: float):
        """Điều chỉnh vị trí tịnh tiến của mặt phẳng cắt (-1.0 đến +1.0)."""
        self.slice_offset = max(-1.2, min(1.2, offset))
        self.update()

    def set_unfold_progress(self, val: float):
        """Cài đặt tiến độ trải phẳng (0.0 đến 1.0)."""
        self.unfold_progress = max(0.0, min(1.0, val))
        if self.unfold_progress > 0 and self.slicing_enabled:
            self.slicing_enabled = False
        self.update()

    def toggle_unfold_animation(self) -> bool:
        """Bật/tắt tự động chạy hoạt hình trải phẳng/gập lại."""
        if self.unfold_animating:
            self.unfold_animating = False
            self.unfold_timer.stop()
        else:
            self.unfold_animating = True
            if self.unfold_progress >= 0.999:
                self.unfold_direction = -1
            elif self.unfold_progress <= 0.001:
                self.unfold_direction = 1
            self.unfold_timer.start(25)
        return self.unfold_animating

    def _step_unfold_animation(self):
        """Mỗi bước frame cập nhật unfold_progress."""
        step = 0.015 * self.unfold_direction
        new_p = self.unfold_progress + step
        if new_p >= 1.0:
            new_p = 1.0
            self.unfold_direction = -1
            self.unfold_animating = False
            self.unfold_timer.stop()
            self.show_toast("ĐÃ TRẢI PHẲNG 2D HOÀN TOÀN (100%)", "📐", 2200)
        elif new_p <= 0.0:
            new_p = 0.0
            self.unfold_direction = 1
            self.unfold_animating = False
            self.unfold_timer.stop()
            self.show_toast("ĐÃ GẬP LẠI THÀNH KHỐI 3D (0%)", "🧊", 2200)

        self.unfold_progress = new_p
        self.unfold_progress_updated.emit(new_p)
        self.update()

    def _render_shape_with_slicing(self, geom):
        """Vẽ khối hình 3D kết hợp mặt phẳng cắt và tấm laser phát sáng."""
        if self.unfold_progress > 0.001:
            geom.draw_unfolded(self.unfold_progress)
            return

        if not self.slicing_enabled:
            geom.draw()
            return

        scale = getattr(geom, 'scale_factor', 0.2)
        h = 1.2
        r = 1.0
        if hasattr(geom, 'height_cm'):
            h = (geom.height_cm * scale) / 2.0
        if hasattr(geom, 'radius_cm'):
            r = geom.radius_cm * scale
        elif hasattr(geom, 'side_length_cm'):
            h = (geom.side_length_cm * scale) / 2.0
            r = h
        elif hasattr(geom, 'base_size_cm'):
            r = (geom.base_size_cm * scale) / 2.0

        world_offset = self.slice_offset * max(h, r)

        if self.slice_type == 'horizontal':
            plane_eq = [0.0, -1.0, 0.0, world_offset]
        elif self.slice_type == 'axial':
            plane_eq = [0.0, 0.0, -1.0, world_offset]
        else:  # oblique
            inv_sqrt2 = 0.70710678
            plane_eq = [0.0, -inv_sqrt2, -inv_sqrt2, world_offset]

        glClipPlane(GL_CLIP_PLANE0, plane_eq)
        glEnable(GL_CLIP_PLANE0)
        geom.draw()
        glDisable(GL_CLIP_PLANE0)

        # Vẽ tấm cắt Hologram phát sáng & đường bao thiết diện nổi bật
        self._draw_hologram_cutting_sheet(geom, world_offset, max(h, r) * 1.5)

    def _draw_hologram_cutting_sheet(self, geom, offset: float, sheet_size: float):
        """Vẽ tấm kính Hologram cắt trong suốt và viền đường giao tuyến thiết diện."""
        glDisable(GL_LIGHTING)
        glDepthMask(GL_FALSE)

        s = sheet_size

        glPushMatrix()
        if self.slice_type == 'horizontal':
            glTranslatef(0.0, offset, 0.0)
            glColor4f(0.0, 0.9, 1.0, 0.16)
            glBegin(GL_QUADS)
            glVertex3f(-s, 0.0, -s)
            glVertex3f(s, 0.0, -s)
            glVertex3f(s, 0.0, s)
            glVertex3f(-s, 0.0, s)
            glEnd()

            glColor4f(0.0, 0.95, 1.0, 0.85)
            glLineWidth(2.2)
            glBegin(GL_LINE_LOOP)
            glVertex3f(-s, 0.0, -s)
            glVertex3f(s, 0.0, -s)
            glVertex3f(s, 0.0, s)
            glVertex3f(-s, 0.0, s)
            glEnd()

            self._draw_horizontal_contour(geom, offset)

        elif self.slice_type == 'axial':
            glTranslatef(0.0, 0.0, offset)
            glColor4f(0.0, 0.9, 1.0, 0.16)
            glBegin(GL_QUADS)
            glVertex3f(-s, -s, 0.0)
            glVertex3f(s, -s, 0.0)
            glVertex3f(s, s, 0.0)
            glVertex3f(-s, s, 0.0)
            glEnd()

            glColor4f(0.0, 0.95, 1.0, 0.85)
            glLineWidth(2.2)
            glBegin(GL_LINE_LOOP)
            glVertex3f(-s, -s, 0.0)
            glVertex3f(s, -s, 0.0)
            glVertex3f(s, s, 0.0)
            glVertex3f(-s, s, 0.0)
            glEnd()

            self._draw_axial_contour(geom, offset)

        else:  # oblique
            inv_sqrt2 = 0.70710678
            glTranslatef(0.0, offset * inv_sqrt2, offset * inv_sqrt2)
            glRotatef(45.0, 1.0, 0.0, 0.0)
            glColor4f(0.0, 0.9, 1.0, 0.16)
            glBegin(GL_QUADS)
            glVertex3f(-s, -s, 0.0)
            glVertex3f(s, -s, 0.0)
            glVertex3f(s, s, 0.0)
            glVertex3f(-s, s, 0.0)
            glEnd()

            glColor4f(0.0, 0.95, 1.0, 0.85)
            glLineWidth(2.2)
            glBegin(GL_LINE_LOOP)
            glVertex3f(-s, -s, 0.0)
            glVertex3f(s, -s, 0.0)
            glVertex3f(s, s, 0.0)
            glVertex3f(-s, s, 0.0)
            glEnd()

        glDepthMask(GL_TRUE)
        glEnable(GL_LIGHTING)
        glPopMatrix()

    def _draw_horizontal_contour(self, geom, offset: float):
        """Vẽ đường viền thiết diện màu vàng neon khi cắt ngang tại y = offset."""
        scale = getattr(geom, 'scale_factor', 0.2)
        name = self.current_shape_key

        glColor4f(1.0, 0.85, 0.2, 0.95)
        glLineWidth(3.0)

        if name == 'cone':
            r = getattr(geom, 'radius_cm', 5.0) * scale
            h = (getattr(geom, 'height_cm', 10.0) * scale) / 2.0
            if -h <= offset <= h:
                t = (h - offset) / (2.0 * h)
                r_cut = r * t
                glBegin(GL_LINE_LOOP)
                for step in range(64):
                    ang = 2.0 * math.pi * step / 64
                    glVertex3f(math.cos(ang) * r_cut, 0.0, math.sin(ang) * r_cut)
                glEnd()
        elif name == 'cylinder':
            r = getattr(geom, 'radius_cm', 5.0) * scale
            h = (getattr(geom, 'height_cm', 10.0) * scale) / 2.0
            if -h <= offset <= h:
                glBegin(GL_LINE_LOOP)
                for step in range(64):
                    ang = 2.0 * math.pi * step / 64
                    glVertex3f(math.cos(ang) * r, 0.0, math.sin(ang) * r)
                glEnd()
        elif name == 'sphere':
            r = getattr(geom, 'radius_cm', 6.0) * scale
            if -r <= offset <= r:
                r_cut = math.sqrt(max(0.0, r * r - offset * offset))
                glBegin(GL_LINE_LOOP)
                for step in range(64):
                    ang = 2.0 * math.pi * step / 64
                    glVertex3f(math.cos(ang) * r_cut, 0.0, math.sin(ang) * r_cut)
                glEnd()
        elif name == 'pyramid':
            b = (getattr(geom, 'base_size_cm', 10.0) * scale) / 2.0
            h = (getattr(geom, 'height_cm', 12.0) * scale) / 2.0
            if -h <= offset <= h:
                t = (h - offset) / (2.0 * h)
                b_cut = b * t
                glBegin(GL_LINE_LOOP)
                glVertex3f(-b_cut, 0.0, -b_cut)
                glVertex3f(b_cut, 0.0, -b_cut)
                glVertex3f(b_cut, 0.0, b_cut)
                glVertex3f(-b_cut, 0.0, b_cut)
                glEnd()
        elif name == 'cube':
            s = (getattr(geom, 'side_length_cm', 10.0) * scale) / 2.0
            if -s <= offset <= s:
                glBegin(GL_LINE_LOOP)
                glVertex3f(-s, 0.0, -s)
                glVertex3f(s, 0.0, -s)
                glVertex3f(s, 0.0, s)
                glVertex3f(-s, 0.0, s)
                glEnd()
        elif name == 'rectangular_prism':
            x = (getattr(geom, 'length_cm', 12.0) * scale) / 2.0
            y = (getattr(geom, 'height_cm', 6.0) * scale) / 2.0
            z = (getattr(geom, 'width_cm', 8.0) * scale) / 2.0
            if -y <= offset <= y:
                glBegin(GL_LINE_LOOP)
                glVertex3f(-x, 0.0, -z)
                glVertex3f(x, 0.0, -z)
                glVertex3f(x, 0.0, z)
                glVertex3f(-x, 0.0, z)
                glEnd()

    def _draw_axial_contour(self, geom, offset: float):
        """Vẽ đường viền thiết diện màu vàng neon khi cắt dọc qua trục đối xứng tại z = offset."""
        scale = getattr(geom, 'scale_factor', 0.2)
        name = self.current_shape_key

        glColor4f(1.0, 0.85, 0.2, 0.95)
        glLineWidth(3.0)

        if name == 'cone':
            r = getattr(geom, 'radius_cm', 5.0) * scale
            h = (getattr(geom, 'height_cm', 10.0) * scale) / 2.0
            glBegin(GL_LINE_LOOP)
            glVertex3f(0.0, h, 0.0)
            glVertex3f(-r, -h, 0.0)
            glVertex3f(r, -h, 0.0)
            glEnd()
        elif name == 'cylinder':
            r = getattr(geom, 'radius_cm', 5.0) * scale
            h = (getattr(geom, 'height_cm', 10.0) * scale) / 2.0
            glBegin(GL_LINE_LOOP)
            glVertex3f(-r, -h, 0.0)
            glVertex3f(r, -h, 0.0)
            glVertex3f(r, h, 0.0)
            glVertex3f(-r, h, 0.0)
            glEnd()
        elif name == 'sphere':
            r = getattr(geom, 'radius_cm', 6.0) * scale
            glBegin(GL_LINE_LOOP)
            for step in range(64):
                ang = 2.0 * math.pi * step / 64
                glVertex3f(math.cos(ang) * r, math.sin(ang) * r, 0.0)
            glEnd()
        elif name == 'pyramid':
            b = (getattr(geom, 'base_size_cm', 10.0) * scale) / 2.0
            h = (getattr(geom, 'height_cm', 12.0) * scale) / 2.0
            glBegin(GL_LINE_LOOP)
            glVertex3f(0.0, h, 0.0)
            glVertex3f(-b, -h, 0.0)
            glVertex3f(b, -h, 0.0)
            glEnd()
        elif name == 'cube':
            s = (getattr(geom, 'side_length_cm', 10.0) * scale) / 2.0
            glBegin(GL_LINE_LOOP)
            glVertex3f(-s, -s, 0.0)
            glVertex3f(s, -s, 0.0)
            glVertex3f(s, s, 0.0)
            glVertex3f(-s, s, 0.0)
            glEnd()
        elif name == 'rectangular_prism':
            x = (getattr(geom, 'length_cm', 12.0) * scale) / 2.0
            y = (getattr(geom, 'height_cm', 6.0) * scale) / 2.0
            glBegin(GL_LINE_LOOP)
            glVertex3f(-x, -y, 0.0)
            glVertex3f(x, -y, 0.0)
            glVertex3f(x, y, 0.0)
            glVertex3f(-x, y, 0.0)
            glEnd()

    def set_wireframe(self, enable: bool):
        """Bật/tắt chế độ vẽ khung dây (Wireframe)."""
        for geom in self.geometries.values():
            geom.wireframe = enable
        self.update()

    def set_dimension_lines(self, enable: bool):
        """Bật/tắt hệ thống đường nét đứt đo kích thước đơn vị."""
        for geom in self.geometries.values():
            geom.show_dimension_lines = enable
        self.update()

    def set_scale_factor(self, factor: float):
        """Cấu hình tỷ lệ cm -> World Unit (1 cm = N units)."""
        for geom in self.geometries.values():
            geom.scale_factor = factor
        self.update()

    def update_rotation(self, delta_yaw: float, delta_pitch: float):
        """Cập nhật góc xoay nhận được từ MediaPipe hand tracking."""
        self.yaw += delta_yaw
        self.pitch += delta_pitch
        
        # Giới hạn góc Pitch để tránh xoay ngược lộn đầu quá đà nếu muốn (-90 đến 90 deg)
        self.pitch = max(-89.0, min(89.0, self.pitch))
        self.update()

    def update_zoom(self, delta_zoom: float):
        """
        Cập nhật zoom (phóng to/thu nhỏ) nhận từ cử chỉ 2 bàn tay hoặc cử chỉ ngón tay.
        delta_zoom > 0: Phóng to (Zoom In).
        delta_zoom < 0: Thu nhỏ (Zoom Out).
        """
        # delta_zoom thường dao động trong khoảng [-0.15, +0.15]
        rate = 1.0 + (delta_zoom * 0.12)
        # Giới hạn tỷ lệ thay đổi mỗi frame để siêu mượt và không bị giật
        rate = max(0.90, min(1.10, rate))
        self.set_zoom_factor(self.zoom_factor * rate)

    def update_frame(self):
        """Vòng lặp timer cập nhật tự động xoay nếu bật Auto Rotate."""
        if self.auto_rotate:
            self.yaw = (self.yaw + self.auto_rotate_speed) % 360.0
            self.update()

    def initializeGL(self):
        """Khởi tạo môi trường OpenGL."""
        # BẮT BUỘC: Clear background là màu Đen Tuyền (Pitch Black #000000)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        
        # Bật Depth Buffer cho hình thể 3D
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)

        # Bật Alpha Blending cho độ trong suốt
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Bật Smooth Shading
        glShadeModel(GL_SMOOTH)

        # Cấu hình ánh sáng Phong
        setup_hologram_lighting()

    def resizeGL(self, width: int, height: int):
        """Xử lý thay đổi kích thước cửa sổ (tương thích High-DPI 125%, 150%)."""
        dpr = self.devicePixelRatio()
        pw = int(width * dpr)
        ph = int(height * dpr)
        if ph <= 0:
            ph = 1
        glViewport(0, 0, pw, ph)

    def paintGL(self):
        """Vẽ khung hình OpenGL 3D."""
        # Xóa màn hình với màu Đen tuyền Pitch Black
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        w = self.width()
        h = self.height()

        # Quy đổi sang Physical Device Pixels cho OpenGL Framebuffer / glViewport
        # Khắc phục triệt để lỗi hình bị co cụm vào góc dưới-trái trên màn hình Windows High-DPI (125%, 150%)
        dpr = self.devicePixelRatio()
        pw = int(w * dpr)
        ph = int(h * dpr)

        if self.view_mode == 'single':
            self._render_single_view(pw, ph)
        else:
            self._render_4view_pyramid(pw, ph)

        # Lớp chú thích 2D nằm trên vùng OpenGL
        self._draw_math_annotations(w, h)
        if self.stream_overlay:
            self._draw_stream_overlay(w, h)
            self._draw_formula_overlay(w, h)
        self._draw_toast_notification(w, h)
        if self.pointer_active and self.pointer_pos is not None:
            self._draw_air_pointer(w, h)

    def _draw_air_pointer(self, width: int, height: int):
        """Vẽ con trỏ Laser Air Pointer phong cách Cyberpunk 3D."""
        if not self.pointer_active or self.pointer_pos is None:
            return

        now = time.time()
        # Tự động ẩn nếu không nhận được tọa độ mới sau 0.5 giây
        if now - self.pointer_last_time > 0.5:
            self.pointer_active = False
            return

        nx, ny = self.pointer_pos
        cx = int(nx * width)
        cy = int(ny * height)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.mirror_mode:
            painter.translate(width, 0)
            painter.scale(-1.0, 1.0)

        # 1. Tâm con trỏ (Lõi sáng trắng + vầng hào quang Cyan)
        painter.setBrush(QColor(0, 240, 255, 40))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - 36, cy - 36, 72, 72)

        painter.setBrush(QColor(0, 240, 255, 80))
        painter.drawEllipse(cx - 20, cy - 20, 40, 40)

        painter.setBrush(QColor(255, 255, 255, 240))
        painter.setPen(QPen(QColor(0, 255, 255), 2))
        painter.drawEllipse(cx - 5, cy - 5, 10, 10)

        # 2. Vòng tròn ngắm Target Ring (Vòng tròn nét đứt Cyberpunk)
        ring_pen = QPen(QColor(0, 240, 255, 210), 1)
        ring_pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(ring_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(cx - 26, cy - 26, 52, 52)

        # 3. 4 Tia chữ thập định tâm (Crosshairs)
        cross_pen = QPen(QColor(0, 255, 255, 220), 1)
        painter.setPen(cross_pen)
        # Ngang
        painter.drawLine(cx - 42, cy, cx - 14, cy)
        painter.drawLine(cx + 14, cy, cx + 42, cy)
        # Dọc
        painter.drawLine(cx, cy - 42, cx, cy - 14)
        painter.drawLine(cx, cy + 14, cx, cy + 42)

        # 4. Thẻ Pill hiển thị tọa độ và trạng thái Air Pointer
        pill_w = 175
        pill_h = 32
        pill_x = cx + 24
        pill_y = cy + 16

        # Đảm bảo pill không tràn khỏi mép màn hình
        if pill_x + pill_w > width - 10:
            pill_x = cx - pill_w - 24
        if pill_y + pill_h > height - 10:
            pill_y = cy - pill_h - 16

        # Hộp tọa độ bóng bẩy
        painter.setBrush(QColor(10, 16, 26, 220))
        painter.setPen(QPen(QColor(0, 240, 255, 180), 1))
        painter.drawRoundedRect(pill_x, pill_y, pill_w, pill_h, 6, 6)

        font = QFont("Segoe UI", 8)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(0, 240, 255))
        painter.drawText(pill_x + 8, pill_y + 14, "🎯 3D AIR POINTER")

        font_sub = QFont("Segoe UI", 7)
        painter.setFont(font_sub)
        if self.slicing_enabled:
            painter.setPen(QColor(50, 255, 150))
            painter.drawText(pill_x + 8, pill_y + 26, f"MẶT CẮT: {self.slice_offset:+.2f}")
        else:
            painter.setPen(QColor(200, 225, 245))
            painter.drawText(pill_x + 8, pill_y + 26, f"X:{nx:.2f}  Y:{ny:.2f}")

        painter.end()

    def _draw_toast_notification(self, width: int, height: int):
        """Vẽ banner Toast HUD thông báo cử chỉ tại đỉnh màn hình."""
        now = time.time()
        if now >= self.toast_expire or not self.toast_message:
            return

        remaining = self.toast_expire - now
        alpha = int(245 * min(1.0, remaining / 0.35)) if remaining < 0.35 else 245

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.mirror_mode:
            painter.translate(width, 0)
            painter.scale(-1.0, 1.0)

        text = f"{self.toast_icon} {self.toast_message}".strip()
        font = QFont("Segoe UI", 12)
        font.setBold(True)
        painter.setFont(font)

        fm = painter.fontMetrics()
        text_w = fm.horizontalAdvance(text)
        bw = max(240, text_w + 36)
        bh = 38
        bx = (width - bw) // 2
        by = 46  # Nằm ngay dưới thẻ tiêu đề, không đè tiêu đề

        bg_color = QColor(8, 18, 30, alpha)
        border_color = QColor(0, 240, 255, alpha)
        painter.setBrush(bg_color)
        pen = painter.pen()
        pen.setColor(border_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRoundedRect(bx, by, bw, bh, 8, 8)

        painter.setPen(QColor(0, 245, 255, alpha))
        painter.drawText(bx, by, bw, bh, Qt.AlignmentFlag.AlignCenter, text)
        painter.end()

    def _draw_formula_overlay(self, width, height):
        if self.hologram_box_mode:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.mirror_mode:
            painter.translate(width, 0)
            painter.scale(-1.0, 1.0)

        has_pedagogy = (self.unfold_progress > 0.001) or self.slicing_enabled
        x = 16
        y = 104 if has_pedagogy else 64
        bw, bh = 340, 124

        # Nền Dark Obsidian bo góc với viền Cyan Hologram
        painter.setBrush(QColor(10, 16, 28, 230))
        painter.setPen(QPen(QColor("#00f0ff"), 1))
        painter.drawRoundedRect(x, y, bw, bh, 8, 8)

        names = {
            'cube': 'KHỐI LẬP PHƯƠNG',
            'pyramid': 'HÌNH CHÓP TỨ GIÁC',
            'sphere': 'KHỐI CẦU',
            'cylinder': 'HÌNH TRỤ TRÒN XOAY',
            'cone': 'HÌNH NÓN TRÒN XOAY',
            'rectangular_prism': 'HÌNH HỘP CHỮ NHẬT',
            'torus': 'HÌNH XUYẾN',
            'spherical_section': 'HÌNH CẮT CẦU',
        }
        formulas = {
            'cube': ['Diện tích: S_tp = 6a²', 'Thể tích: V = a³'],
            'pyramid': ['Diện tích đáy: S_đ = a²', 'Thể tích: V = ⅓ · S_đ · h'],
            'sphere': ['Diện tích mặt: S = 4πR²', 'Thể tích: V = ⁴⁄₃πR³'],
            'cylinder': ['Diện tích xung quanh: S_xq = 2πRh', 'Thể tích: V = πR²h'],
            'cone': ['Diện tích xung quanh: S_xq = πRl', 'Thể tích: V = ⅓πR²h'],
            'rectangular_prism': ['Diện tích toàn phần: S_tp = 2(ab+bc+ca)', 'Thể tích: V = abc'],
            'torus': ['Diện tích mặt: S = 4π²Rr', 'Thể tích: V = 2π²Rr²'],
            'spherical_section': ['Diện tích xung quanh: S_xq = 2πRh', 'Thể tích: V = πh²(R - h/3)'],
        }

        # Header: Tên công thức
        painter.setPen(QColor('#00f0ff'))
        font_title = QFont('Segoe UI', 11)
        font_title.setBold(True)
        painter.setFont(font_title)
        title_text = f"📐 CÔNG THỨC {names.get(self.current_shape_key, 'HÌNH HỌC')}"
        painter.drawText(x + 16, y + 28, title_text)

        # Đường kẻ phân cách tinh tế
        painter.setPen(QPen(QColor(0, 240, 255, 70), 1))
        painter.drawLine(x + 16, y + 38, x + bw - 16, y + 38)

        # Dòng công thức
        font_formula = QFont('Segoe UI', 12)
        font_formula.setBold(True)
        painter.setFont(font_formula)

        shape_formulas = formulas.get(self.current_shape_key, ['Chưa có công thức'])
        for i, line in enumerate(shape_formulas):
            painter.setPen(QColor('#ffd700'))
            painter.drawText(x + 18, y + 68 + i * 30, f"• {line}")

        painter.end()

    def _draw_math_annotations(self, width: int, height: int):
        """Hiển thị nhãn trục và thông tin hình học cho bài học Toán."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.mirror_mode:
            painter.translate(width, 0)
            painter.scale(-1.0, 1.0)

        # Axis gizmo và Badge thông tin 2D: Chỉ vẽ khi KHÔNG ở chế độ Hộp Hologram
        geom = self.get_current_geometry()
        if not self.hologram_box_mode:
            font = QFont("Segoe UI", 10)
            font.setBold(True)
            painter.setFont(font)

            # Axis gizmo cố định ở góc dưới bên trái, độc lập với mô hình.
            ox, oy = 58, height - 48
            import math
            yaw = math.radians(self.yaw)
            pitch = math.radians(self.pitch)
            # Hướng chiếu 2D đơn giản của các trục sau khi mô hình xoay.
            x_end = (ox + 48 * math.cos(yaw), oy - 48 * math.sin(pitch) * math.sin(yaw))
            y_end = (ox + 38 * math.sin(yaw), oy - 52 * math.cos(pitch))
            z_end = (ox - 34 * math.sin(yaw), oy - 34 * math.cos(yaw) * math.cos(pitch))
            self._draw_axis_arrow(painter, ox, oy, *x_end, "X", "#ff3030")
            self._draw_axis_arrow(painter, ox, oy, *y_end, "Y", "#32e65f")
            self._draw_axis_arrow(painter, ox, oy, *z_end, "Z", "#2868ff")

            # Thông tin hình học góc trên bên trái của vùng OpenGL (HUD Glass Badge)
            if self.current_shape_key == "cube":
                s = getattr(geom, 'side_length_cm', 10.0)
                info = f"📦 Khối lập phương  |  cạnh: {s:.1f} cm"
            elif self.current_shape_key == "pyramid":
                b = getattr(geom, 'base_size_cm', 10.0)
                h = getattr(geom, 'height_cm', 12.0)
                info = f"🔺 Hình chóp  |  đáy: {b:.1f} cm  |  cao: {h:.1f} cm"
            elif self.current_shape_key == "sphere":
                r = getattr(geom, 'radius_cm', 6.0)
                info = f"⚽ Khối cầu  |  R: {r:.1f} cm  (D: {2*r:.1f} cm)"
            elif self.current_shape_key == "cylinder":
                r = getattr(geom, 'radius_cm', 5.0)
                h = getattr(geom, 'height_cm', 10.0)
                info = f"🛢️ Hình trụ  |  R: {r:.1f} cm  |  cao: {h:.1f} cm"
            elif self.current_shape_key == "torus":
                R = getattr(geom, 'major_radius_cm', 6.0)
                r = getattr(geom, 'minor_radius_cm', 2.0)
                info = f"🍩 Hình xuyến  |  R: {R:.1f} cm  |  r: {r:.1f} cm"
            elif self.current_shape_key == "cone":
                r = getattr(geom, 'radius_cm', 5.0)
                h = getattr(geom, 'height_cm', 10.0)
                info = f"🔻 Hình nón  |  R: {r:.1f} cm  |  cao: {h:.1f} cm"
            elif self.current_shape_key == "rectangular_prism":
                l = getattr(geom, 'length_cm', 12.0)
                w = getattr(geom, 'width_cm', 8.0)
                h = getattr(geom, 'height_cm', 6.0)
                info = f"▣ Hộp chữ nhật  |  {l:.1f} × {w:.1f} × {h:.1f} cm"
            elif self.current_shape_key == "spherical_section":
                r = getattr(geom, 'radius_cm', 6.0)
                info = f"◐ Hình cắt cầu  |  R: {r:.1f} cm"
            else:
                info = f"🧊 {self.current_shape_key}"

            font_hud = QFont("Segoe UI", 12)
            font_hud.setBold(True)
            painter.setFont(font_hud)
            metrics = painter.fontMetrics()
            txt_w = metrics.horizontalAdvance(info)
            badge_w = float(txt_w + 32)
            badge_h = float(metrics.height() + 14)
            bx, by = 16.0, 16.0

            # Nền Dark Glassmorphism bo góc
            painter.setBrush(QColor(10, 15, 26, 220))
            painter.setPen(QPen(QColor("#00e5ff"), 1))
            painter.drawRoundedRect(QRectF(bx, by, badge_w, badge_h), 8.0, 8.0)

            # Chữ sáng màu trắng ngọc
            painter.setPen(QColor("#ffffff"))
            painter.drawText(QRectF(bx, by, badge_w, badge_h), Qt.AlignmentFlag.AlignCenter, info)

            # Badge sư phạm bổ sung: Mặt cắt hoặc Trải phẳng 2D
            pedagogy_info = None
            pedagogy_color = "#ffd700"
            if self.unfold_progress > 0.001:
                pedagogy_info = self._get_unfold_info(geom)
                pedagogy_color = "#38bdf8"
            elif self.slicing_enabled:
                pedagogy_info = self._get_slicing_info(geom)
                pedagogy_color = "#ffd700"

            if pedagogy_info:
                p_txt_w = metrics.horizontalAdvance(pedagogy_info)
                p_badge_w = float(p_txt_w + 32)
                p_badge_h = float(metrics.height() + 14)
                p_bx = 16.0
                p_by = by + badge_h + 10.0

                painter.setBrush(QColor(10, 15, 26, 230))
                painter.setPen(QPen(QColor(pedagogy_color), 1))
                painter.drawRoundedRect(QRectF(p_bx, p_by, p_badge_w, p_badge_h), 8.0, 8.0)

                painter.setPen(QColor(pedagogy_color))
                painter.drawText(QRectF(p_bx, p_by, p_badge_w, p_badge_h), Qt.AlignmentFlag.AlignCenter, pedagogy_info)

        # Chiếu các nhãn kích thước động 3D lên màn hình 2D (Single View mode, khi không trải phẳng)
        if self.view_mode == 'single' and getattr(geom, 'show_dimension_lines', True) and self.unfold_progress <= 0.001:
            if self.last_modelview is not None and self.last_projection is not None and self.last_viewport is not None:
                annotations = geom.get_dimension_annotations()
                dpr = self.devicePixelRatio()
                for pos3d, text, color_hex in annotations:
                    try:
                        wx, wy, wz = gluProject(pos3d[0], pos3d[1], pos3d[2],
                                                self.last_modelview, self.last_projection, self.last_viewport)
                        if 0.0 <= wz <= 1.0:
                            # Chuyển đổi từ Physical pixels (OpenGL) sang Logical pixels (QPainter)
                            sx = float(wx) / dpr
                            sy = float(self.last_viewport[3] - wy) / dpr
                            if 0 <= sx <= width and 0 <= sy <= height:
                                self._draw_dimension_tag(painter, sx, sy, text, color_hex)
                    except Exception:
                        pass

        painter.end()

    def _get_slicing_info(self, geom):
        name = self.current_shape_key
        if self.slice_type == 'horizontal':
            if name == 'cone':
                r_cm = getattr(geom, 'radius_cm', 5.0)
                t = max(0.0, min(1.0, (1.0 - self.slice_offset) / 2.0))
                r_cut = r_cm * t
                s_cut = math.pi * (r_cut ** 2)
                return f"✂️ Mặt cắt ngang: Hình tròn  |  r = {r_cut:.1f} cm  |  S = πr² ≈ {s_cut:.1f} cm²"
            elif name == 'cylinder':
                r_cm = getattr(geom, 'radius_cm', 5.0)
                s_cut = math.pi * (r_cm ** 2)
                return f"✂️ Mặt cắt ngang: Hình tròn  |  r = {r_cm:.1f} cm  |  S = πr² ≈ {s_cut:.1f} cm²"
            elif name == 'sphere':
                r_cm = getattr(geom, 'radius_cm', 6.0)
                off_cm = self.slice_offset * r_cm
                r_cut = math.sqrt(max(0.0, r_cm**2 - off_cm**2))
                s_cut = math.pi * (r_cut ** 2)
                return f"✂️ Mặt cắt ngang: Hình tròn  |  r = {r_cut:.1f} cm  |  S = πr² ≈ {s_cut:.1f} cm²"
            elif name == 'pyramid':
                b_cm = getattr(geom, 'base_size_cm', 10.0)
                t = max(0.0, min(1.0, (1.0 - self.slice_offset) / 2.0))
                a_cut = b_cm * t
                s_cut = a_cut ** 2
                return f"✂️ Mặt cắt ngang: Hình vuông  |  cạnh = {a_cut:.1f} cm  |  S = a'² = {s_cut:.1f} cm²"
            elif name == 'cube':
                a_cm = getattr(geom, 'side_length_cm', 10.0)
                s_cut = a_cm ** 2
                return f"✂️ Mặt cắt ngang: Hình vuông  |  a = {a_cm:.1f} cm  |  S = a² = {s_cut:.1f} cm²"
            elif name == 'rectangular_prism':
                l = getattr(geom, 'length_cm', 12.0)
                w = getattr(geom, 'width_cm', 8.0)
                return f"✂️ Mặt cắt ngang: Hình chữ nhật  |  {l:.1f} × {w:.1f} cm  |  S = {l*w:.1f} cm²"
            else:
                return "✂️ Chế độ Mặt cắt Ngang 3D"
        elif self.slice_type == 'axial':
            if name == 'cone':
                r_cm = getattr(geom, 'radius_cm', 5.0)
                h_cm = getattr(geom, 'height_cm', 10.0)
                s_tri = r_cm * h_cm
                return f"✂️ Thiết diện qua trục: Tam giác cân  |  đáy 2R = {2*r_cm:.1f} cm, h = {h_cm:.1f} cm  |  S = R·h = {s_tri:.1f} cm²"
            elif name == 'cylinder':
                r_cm = getattr(geom, 'radius_cm', 5.0)
                h_cm = getattr(geom, 'height_cm', 10.0)
                s_rec = 2 * r_cm * h_cm
                return f"✂️ Thiết diện qua trục: Hình chữ nhật  |  2R = {2*r_cm:.1f} cm, h = {h_cm:.1f} cm  |  S = 2Rh = {s_rec:.1f} cm²"
            elif name == 'sphere':
                r_cm = getattr(geom, 'radius_cm', 6.0)
                s_circ = math.pi * (r_cm ** 2)
                return f"✂️ Thiết diện qua trục: Hình tròn lớn  |  R = {r_cm:.1f} cm  |  S = πR² ≈ {s_circ:.1f} cm²"
            elif name == 'pyramid':
                b_cm = getattr(geom, 'base_size_cm', 10.0)
                h_cm = getattr(geom, 'height_cm', 12.0)
                s_tri = 0.5 * b_cm * h_cm
                return f"✂️ Thiết diện qua trục: Tam giác cân  |  đáy = {b_cm:.1f} cm, h = {h_cm:.1f} cm  |  S = {s_tri:.1f} cm²"
            elif name == 'cube':
                a_cm = getattr(geom, 'side_length_cm', 10.0)
                return f"✂️ Thiết diện dọc: Hình vuông  |  a = {a_cm:.1f} cm  |  S = a² = {a_cm*a_cm:.1f} cm²"
            elif name == 'rectangular_prism':
                l = getattr(geom, 'length_cm', 12.0)
                h = getattr(geom, 'height_cm', 6.0)
                return f"✂️ Thiết diện dọc: Hình chữ nhật  |  {l:.1f} × {h:.1f} cm  |  S = {l*h:.1f} cm²"
            else:
                return "✂️ Chế độ Thiết diện Dọc Trục 3D"
        else:
            return "✂️ Thiết diện Nghiêng Conic / Parabol"

    def _get_unfold_info(self, geom):
        p_pct = int(self.unfold_progress * 100)
        name = self.current_shape_key
        if name == 'cube':
            a = getattr(geom, 'side_length_cm', 10.0)
            return f"📦 Trải phẳng 2D: {p_pct}%  |  6 hình vuông phẳng  |  S_tp = 6a² = {6*a*a:.1f} cm²"
        elif name == 'pyramid':
            b = getattr(geom, 'base_size_cm', 10.0)
            h = getattr(geom, 'height_cm', 12.0)
            sh = math.sqrt(h * h + (b / 2.0) ** 2)
            s_xq = 4 * (0.5 * b * sh)
            s_tp = s_xq + b * b
            return f"📦 Trải phẳng 2D: {p_pct}%  |  Đáy vuông + 4 tam giác bên  |  S_xq ≈ {s_xq:.1f} cm²  |  S_tp ≈ {s_tp:.1f} cm²"
        elif name == 'cone':
            r = getattr(geom, 'radius_cm', 5.0)
            h = getattr(geom, 'height_cm', 10.0)
            l = math.sqrt(r * r + h * h)
            deg = (r / l) * 360.0
            s_xq = math.pi * r * l
            s_tp = s_xq + math.pi * r * r
            return f"📦 Trải phẳng 2D: {p_pct}%  |  Hình quạt (góc α = {deg:.0f}°) + Đáy tròn  |  S_xq ≈ {s_xq:.1f} cm²  |  S_tp ≈ {s_tp:.1f} cm²"
        elif name == 'cylinder':
            r = getattr(geom, 'radius_cm', 5.0)
            h = getattr(geom, 'height_cm', 10.0)
            s_xq = 2 * math.pi * r * h
            s_tp = s_xq + 2 * math.pi * r * r
            return f"📦 Trải phẳng 2D: {p_pct}%  |  Chữ nhật (2πR × h) + 2 đáy tròn  |  S_xq ≈ {s_xq:.1f} cm²  |  S_tp ≈ {s_tp:.1f} cm²"
        elif name == 'rectangular_prism':
            l = getattr(geom, 'length_cm', 12.0)
            w = getattr(geom, 'width_cm', 8.0)
            h = getattr(geom, 'height_cm', 6.0)
            s_tp = 2 * (l * w + w * h + h * l)
            return f"📦 Trải phẳng 2D: {p_pct}%  |  Mạng phẳng 6 hình chữ nhật  |  S_tp = {s_tp:.1f} cm²"
        elif name == 'sphere':
            r = getattr(geom, 'radius_cm', 6.0)
            s_disc = math.pi * r * r
            return f"📦 Tách đôi Bán cầu: {p_pct}%  |  Lộ diện đĩa tròn xích đạo  |  S_đáy = πR² ≈ {s_disc:.1f} cm²"
        else:
            return f"📦 Trải phẳng 2D: {p_pct}%"

    @staticmethod
    def _draw_dimension_tag(painter, sx: float, sy: float, text: str, color_hex: str):
        """Vẽ thẻ nhãn kích thước động dạng Capsule bo tròn kính mờ Cyberpunk."""
        font_tag = QFont("Segoe UI", 11)
        font_tag.setBold(True)
        painter.setFont(font_tag)
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(text)
        th = fm.height()

        bw = float(tw + 20)
        bh = float(th + 10)
        bx = sx + 8.0
        by = sy - bh / 2.0

        # Đảm bảo thẻ nhãn không bị đè vào thanh tiêu đề ở đỉnh màn hình
        if by < 48.0:
            by = 48.0

        is_point = len(text) <= 3 or " (" in text

        painter.setBrush(QColor(10, 16, 28, 225))
        border_col = QColor(color_hex)
        painter.setPen(QPen(border_col, 1))
        painter.drawRoundedRect(QRectF(bx, by, bw, bh), bh / 2.0, bh / 2.0)

        text_col = QColor("#ffffff") if is_point else QColor(color_hex)
        painter.setPen(text_col)
        painter.drawText(QRectF(bx, by, bw, bh), Qt.AlignmentFlag.AlignCenter, text)

    def _draw_stream_overlay(self, width: int, height: int):
        if self.hologram_box_mode:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.mirror_mode:
            painter.translate(width, 0)
            painter.scale(-1.0, 1.0)

        # Khung viền ngoài: Chỉ vẽ khi KHÔNG ở chế độ Hộp Hologram (để giữ nền đen tuyệt đối không viền phản chiếu)
        if not self.hologram_box_mode:
            pen = painter.pen()
            pen.setColor(QColor("#00eaff"))
            pen.setWidth(2)
            painter.setPen(pen)
            painter.drawRoundedRect(8, 8, width - 16, height - 16, 10, 10)

        # Tiêu đề Hologram dạng Capsule kính mờ bo góc sang trọng, không đè lên đỉnh hình học
        title_text = "✦ HOLOGRAM TOÁN HỌC ✦"
        font_t = QFont("Segoe UI", 12)
        font_t.setBold(True)
        painter.setFont(font_t)
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(title_text)
        bw, bh = tw + 28, 30
        bx = (width - bw) // 2
        by = 10

        painter.setBrush(QColor(8, 14, 24, 215))
        painter.setPen(QPen(QColor("#00eaff"), 1))
        painter.drawRoundedRect(QRectF(bx, by, bw, bh), 6, 6)

        painter.setPen(QColor("#00eaff"))
        painter.drawText(QRectF(bx, by, bw, bh), Qt.AlignmentFlag.AlignCenter, title_text)

        font = QFont("Segoe UI", 11)
        font.setBold(True)
        painter.setFont(font)
        shape_name = {
            "cube": "Khối lập phương",
            "pyramid": "Hình chóp tứ giác",
            "sphere": "Khối cầu",
            "cylinder": "Hình trụ",
            "torus": "Hình xuyến",
            "cone": "Hình nón",
            "rectangular_prism": "Hình hộp chữ nhật",
            "spherical_section": "Hình cắt cầu",
        }.get(self.current_shape_key, self.current_shape_key)
        painter.setPen(QColor("#dce8ff"))
        painter.drawText(24, height - 22, "OXYZ")
        painter.drawText(width - 220, height - 22, shape_name)
        painter.end()

    @staticmethod
    def _draw_axis_arrow(painter, x1, y1, x2, y2, label, color):
        """Vẽ một trục có mũi tên và nhãn, dùng hệ tọa độ màn hình cố định."""
        from PyQt6.QtCore import QPointF
        from PyQt6.QtGui import QPolygonF
        import math

        pen = painter.pen()
        pen.setColor(QColor(color)); pen.setWidth(3)
        painter.setPen(pen)
        painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        angle = math.atan2(y2-y1, x2-x1)
        size = 9
        points = [
            QPointF(x2, y2),
            QPointF(x2-size*math.cos(angle-0.45), y2-size*math.sin(angle-0.45)),
            QPointF(x2-size*math.cos(angle+0.45), y2-size*math.sin(angle+0.45)),
        ]
        painter.setBrush(QColor(color)); painter.drawPolygon(QPolygonF(points))
        font_axis = QFont("Segoe UI", 12)
        font_axis.setBold(True)
        painter.setFont(font_axis)
        painter.setPen(QColor(color)); painter.drawText(int(x2)+6, int(y2)+6, label)

    def _render_single_view(self, width: int, height: int):
        """Vẽ 1 camera trực diện giữa màn hình (Preview Mode)."""
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        # Thu phóng quang học Optical FOV Zoom: tan(fov / 2) = tan(22.5°) / zoom_factor
        tan_half = math.tan(math.radians(22.5)) / max(0.01, self.zoom_factor)
        fov = max(2.0, min(120.0, 2.0 * math.degrees(math.atan(tan_half))))
        gluPerspective(fov, width / height, 0.05, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        # Nâng nhẹ góc nhìn camera (Y = 0.20) khi có thanh tiêu đề trên cùng,
        # hoặc nhìn thẳng tâm (Y = 0.0) khi ở chế độ Hộp Hologram toàn màn hình
        cam_y = 0.0 if self.hologram_box_mode else 0.20
        gluLookAt(0.0, cam_y, 6.0,
                  0.0, cam_y, 0.0,
                  0.0, 1.0, 0.0)

        # Lưu ma trận biến đổi tọa độ CHUẨN phục vụ chiếu nhãn kích thước động 2D
        self.last_modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        self.last_projection = glGetDoublev(GL_PROJECTION_MATRIX)
        self.last_viewport = glGetIntegerv(GL_VIEWPORT)

        # Nếu bật chế độ Lật gương (Mirror Mode cho Hộp Hologram kính 45°)
        if self.mirror_mode:
            glMatrixMode(GL_PROJECTION)
            glScalef(-1.0, 1.0, 1.0)
            glMatrixMode(GL_MODELVIEW)

        # Thực hiện biến đổi hình học & xoay vật thể
        glPushMatrix()
        glRotatef(self.pitch, 1.0, 0.0, 0.0)
        glRotatef(self.yaw, 0.0, 1.0, 0.0)
        glRotatef(self.roll, 0.0, 0.0, 1.0)

        current_geom = self.geometries[self.current_shape_key]
        self._render_shape_with_slicing(current_geom)
        glPopMatrix()

    def _render_4view_pyramid(self, width: int, height: int):
        """
        Vẽ 4 góc nhìn chuẩn cho Kim Tự Tháp Hologram 4 mặt (Cross Pyramid Layout).
        Sắp xếp 4 viewport tạo hình chữ thập (Top, Bottom, Left, Right)
        xung quanh tâm màn hình.
        """
        size = min(width, height) // 3  # Kích thước mỗi viewport
        cx = width // 2
        cy = height // 2

        # 4 Vùng hiển thị Viewport xung quanh tâm:
        # 1. Viewport Dưới (Bottom View): Nhìn từ phía trước (Front)
        vp_bottom = (cx - size // 2, cy - size * 3 // 2, size, size)
        
        # 2. Viewport Trên (Top View): Nhìn từ phía sau (Back) & Xoay ngược 180 độ
        vp_top = (cx - size // 2, cy + size // 2, size, size)
        
        # 3. Viewport Trái (Left View): Nhìn từ bên trái & Xoay -90 độ
        vp_left = (cx - size * 3 // 2, cy - size // 2, size, size)

        # 4. Viewport Phải (Right View): Nhìn từ bên phải & Xoay +90 độ
        vp_right = (cx + size // 2, cy - size // 2, size, size)

        views = [
            # (Viewport Rect, Screen Rotation Z, Extra Camera Yaw)
            (vp_bottom, 0.0, 0.0),       # Mặt dưới: Giữ nguyên
            (vp_top, 180.0, 180.0),      # Mặt trên: Xoay 180° để ánh chiếu đúng kính
            (vp_left, -90.0, 90.0),      # Mặt trái: Xoay -90°
            (vp_right, 90.0, -90.0)      # Mặt phải: Xoay +90°
        ]

        current_geom = self.geometries[self.current_shape_key]

        for (vx, vy, vw, vh), z_rot, cam_yaw_offset in views:
            glViewport(vx, vy, vw, vh)
            
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            tan_half = math.tan(math.radians(22.5)) / max(0.01, self.zoom_factor)
            fov = max(2.0, min(120.0, 2.0 * math.degrees(math.atan(tan_half))))
            gluPerspective(fov, 1.0, 0.05, 100.0)
            if self.mirror_mode:
                glScalef(-1.0, 1.0, 1.0)

            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            gluLookAt(0.0, 0.0, 6.0,
                      0.0, 0.0, 0.0,
                      0.0, 1.0, 0.0)

            glPushMatrix()
            # Xoay mặt phẳng hiển thị theo góc tương ứng của 4 mặt kim tự tháp
            glRotatef(z_rot, 0.0, 0.0, 1.0)
            
            # Áp dụng góc xoay tương tác người dùng (Pitch & Yaw)
            glRotatef(self.pitch, 1.0, 0.0, 0.0)
            glRotatef(self.yaw + cam_yaw_offset, 0.0, 1.0, 0.0)

            self._render_shape_with_slicing(current_geom)
            glPopMatrix()

    # Thao tác Chuột dự phòng (Mouse Drag to Rotate)
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.last_mouse_pos = event.position()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.last_mouse_pos is not None:
            pos = event.position()
            dx = pos.x() - self.last_mouse_pos.x()
            dy = pos.y() - self.last_mouse_pos.y()
            
            self.yaw += dx * 0.5
            self.pitch += dy * 0.5
            self.pitch = max(-89.0, min(89.0, self.pitch))
            
            self.last_mouse_pos = pos
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.last_mouse_pos = None

    def wheelEvent(self, event: QWheelEvent):
        """Zoom bằng cuộn chuột (Mouse Scroll Wheel)."""
        delta = event.angleDelta().y()
        # Cuộn lên = phóng to (zoom_factor tăng), cuộn xuống = thu nhỏ (zoom_factor giảm)
        steps = delta / 120.0
        rate = 1.15 ** steps
        self.set_zoom_factor(self.zoom_factor * rate)
