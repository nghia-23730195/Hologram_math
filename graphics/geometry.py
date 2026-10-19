"""
graphics/geometry.py
-------------------
Module chứa các lớp tạo hình học 3D (Cube, Pyramid, Sphere, Cylinder, Torus)
cho ứng dụng Hologram 3D.

Mỗi đối tượng hình học hỗ trợ:
- Tính toán tọa độ đỉnh (vertices), vector pháp tuyến (normals), chỉ số mặt (indices).
- Quy đổi thông số kích thước thực tế (cm) thành tỷ lệ không gian 3D (World Units).
- Render bằng PyOpenGL (dùng OpenGL Immediate Mode / Display List hoặc Vertex Arrays).
"""

import math
from OpenGL.GL import *


def draw_dashed_line_3d(p1, p2, num_dashes=None, color=(1.0, 0.88, 0.15, 0.95), line_width=2.4):
    """
    Vẽ đường nét đứt 3D (dashed line) trong không gian.
    Tự động tính số vạch đứt phù hợp dựa theo khoảng cách giữa 2 điểm.
    """
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    dist = math.sqrt(dx * dx + dy * dy + dz * dz)
    if dist <= 1e-6:
        return
    if num_dashes is None:
        num_dashes = max(6, int(dist * 12))

    glLineWidth(line_width)
    glColor4f(*color)
    glBegin(GL_LINES)
    total_steps = num_dashes * 2
    for step in range(0, total_steps, 2):
        t0 = step / total_steps
        t1 = (step + 1) / total_steps
        glVertex3f(p1[0] + dx * t0, p1[1] + dy * t0, p1[2] + dz * t0)
        glVertex3f(p1[0] + dx * t1, p1[1] + dy * t1, p1[2] + dz * t1)
    glEnd()


def draw_point_marker_3d(pos, color=(1.0, 1.0, 1.0, 1.0), point_size=7.5):
    """Vẽ điểm mốc tròn nổi bật trong không gian 3D."""
    glPointSize(point_size)
    glColor4f(*color)
    glBegin(GL_POINTS)
    glVertex3fv(pos)
    glEnd()


def draw_right_angle_3d(corner, v_arm1, v_arm2, size=0.18, color=(1.0, 0.88, 0.15, 0.95), line_width=1.8):
    """
    Vẽ ký hiệu góc vuông chuẩn SGK hình học không gian tại đỉnh `corner`
    tạo bởi 2 vector hướng `v_arm1` và `v_arm2`.
    """
    len1 = math.sqrt(v_arm1[0]**2 + v_arm1[1]**2 + v_arm1[2]**2)
    len2 = math.sqrt(v_arm2[0]**2 + v_arm2[1]**2 + v_arm2[2]**2)
    if len1 < 1e-6 or len2 < 1e-6:
        return
    u1 = (v_arm1[0] / len1 * size, v_arm1[1] / len1 * size, v_arm1[2] / len1 * size)
    u2 = (v_arm2[0] / len2 * size, v_arm2[1] / len2 * size, v_arm2[2] / len2 * size)

    p1 = (corner[0] + u1[0], corner[1] + u1[1], corner[2] + u1[2])
    p_corner = (corner[0] + u1[0] + u2[0], corner[1] + u1[1] + u2[1], corner[2] + u1[2] + u2[2])
    p2 = (corner[0] + u2[0], corner[1] + u2[1], corner[2] + u2[2])

    glLineWidth(line_width)
    glColor4f(*color)
    glBegin(GL_LINE_STRIP)
    glVertex3fv(p1)
    glVertex3fv(p_corner)
    glVertex3fv(p2)
    glEnd()

    # Chấm nhỏ ở tâm góc vuông (ký hiệu chuẩn SGK)
    dot = (corner[0] + 0.5 * (u1[0] + u2[0]), corner[1] + 0.5 * (u1[1] + u2[1]), corner[2] + 0.5 * (u1[2] + u2[2]))
    glPointSize(3.5)
    glBegin(GL_POINTS)
    glVertex3fv(dot)
    glEnd()


class Geometry3D:
    """Lớp cơ sở cho tất cả các đối tượng hình học 3D."""
    def __init__(self):
        self.scale_factor = 0.2  # 1 cm = 0.2 units trong OpenGL coordinate system
        self.color = (0.0, 0.9, 1.0)  # RGB (Cyan Hologram mặc định)
        self.alpha = 0.95  # Độ trong suốt (0.0 - 1.0)
        self.wireframe = False  # Chế độ khung dây
        self.enable_lighting = True
        self.show_dimension_lines = True  # Hiển thị các đường nét đứt đo kích thước đơn vị
        self.unfold_progress = 0.0  # 0.0 (3D kín) -> 1.0 (Trải phẳng 2D hoàn toàn)

    def set_color(self, r: float, g: float, b: float, a: float = 1.0):
        """Cấu hình màu sắc và độ trong suốt."""
        self.color = (r, g, b)
        self.alpha = a

    def apply_material(self):
        """Thiết lập thông số vật liệu và màu sắc trong môi trường OpenGL."""
        r, g, b = self.color
        a = self.alpha
        
        # Thiết lập màu tô sắc (Color) khi vẽ
        glColor4f(r, g, b, a)

        # Cấu hình thuộc tính phản xạ ánh sáng (Phong Material Properties)
        ambient = [r * 0.4, g * 0.4, b * 0.4, a]
        diffuse = [r * 0.9, g * 0.9, b * 0.9, a]
        specular = [1.0, 1.0, 1.0, a]
        shininess = 64.0

        glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, ambient)
        glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, diffuse)
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, specular)
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, shininess)

    def draw(self):
        """Phương thức vẽ ảo - các lớp con ghi đè triển khai cụ thể."""
        pass

    def draw_unfolded(self, progress: float):
        """Phương thức vẽ hoạt hình trải phẳng - mặc định gọi draw()."""
        self.draw()

    def get_dimension_annotations(self):
        """
        Trả về danh sách các nhãn kích thước để chiếu lên 2D:
        Mỗi phần tử: (pos_3d, text, color_hex)
        """
        return []


class CubeGeometry(Geometry3D):
    """
    Hình Lập Phương (Cube).
    Thông số:
    - side_length_cm: Chiều dài cạnh tính bằng cm.
    """
    def __init__(self, side_length_cm: float = 10.0):
        super().__init__()
        self.side_length_cm = side_length_cm

    def draw(self):
        """Vẽ khối lập phương 3D với 6 mặt và vector pháp tuyến chuẩn."""
        self.apply_material()
        
        # Chuyển đổi kích thước cm -> world unit (bán kính một nửa chiều dài)
        s = (self.side_length_cm * self.scale_factor) / 2.0

        # Định nghĩa 6 mặt của hình lập phương (Normal Vector + 4 Vertices)
        faces = [
            # Mặt trước (+Z)
            ((0.0, 0.0, 1.0), [(-s, -s, s), (s, -s, s), (s, s, s), (-s, s, s)]),
            # Mặt sau (-Z)
            ((0.0, 0.0, -1.0), [(-s, -s, -s), (-s, s, -s), (s, s, -s), (s, -s, -s)]),
            # Mặt trên (+Y)
            ((0.0, 1.0, 0.0), [(-s, s, -s), (-s, s, s), (s, s, s), (s, s, -s)]),
            # Mặt dưới (-Y)
            ((0.0, -1.0, 0.0), [(-s, -s, -s), (s, -s, -s), (s, -s, s), (-s, -s, s)]),
            # Mặt phải (+X)
            ((1.0, 0.0, 0.0), [(s, -s, -s), (s, s, -s), (s, s, s), (s, -s, s)]),
            # Mặt trái (-X)
            ((-1.0, 0.0, 0.0), [(-s, -s, -s), (-s, -s, s), (-s, s, s), (-s, s, -s)]),
        ]

        mode = GL_LINE_LOOP if self.wireframe else GL_QUADS

        for normal, verts in faces:
            glBegin(mode)
            glNormal3fv(normal)
            for v in verts:
                glVertex3fv(v)
            glEnd()

        # Hệ thống đường nét đứt đo kích thước đơn vị
        if self.show_dimension_lines and not self.wireframe:
            glDisable(GL_LIGHTING)
            glDisable(GL_DEPTH_TEST)

            # 1. Trục chiều cao tâm: nối từ tâm mặt trên (0, s, 0) xuống tâm mặt dưới (0, -s, 0)
            draw_dashed_line_3d((0.0, s, 0.0), (0.0, -s, 0.0), color=(1.0, 0.88, 0.15, 0.95), line_width=2.5)

            # 2. Hai đường chéo đáy dưới nét đứt giao nhau tại tâm đáy
            draw_dashed_line_3d((-s, -s, -s), (s, -s, s), color=(1.0, 0.62, 0.15, 0.7), line_width=1.8)
            draw_dashed_line_3d((-s, -s, s), (s, -s, -s), color=(1.0, 0.62, 0.15, 0.7), line_width=1.8)

            # 3. Ký hiệu góc vuông tại tâm đáy
            draw_right_angle_3d((0.0, -s, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), size=min(0.2, s * 0.35))

            # 4. Các điểm mốc tâm đáy, tâm trên, tâm khối O
            draw_point_marker_3d((0.0, 0.0, 0.0), color=(1.0, 1.0, 1.0, 1.0), point_size=8.0)
            draw_point_marker_3d((0.0, -s, 0.0), color=(1.0, 0.88, 0.15, 1.0), point_size=7.5)
            draw_point_marker_3d((0.0, s, 0.0), color=(0.15, 0.95, 1.0, 1.0), point_size=7.5)

            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)

    def draw_unfolded(self, progress: float):
        """Trải phẳng hình lập phương thành hình chữ thập 6 mặt (Latin Cross Net)."""
        self.apply_material()
        s = self.side_length_cm * self.scale_factor
        half = s / 2.0
        p = max(0.0, min(1.0, progress))
        fold_ang = 90.0 * (1.0 - p)

        def square():
            glBegin(GL_LINE_LOOP if self.wireframe else GL_QUADS)
            glNormal3f(0.0, 1.0, 0.0)
            glVertex3f(-half, 0.0, -half)
            glVertex3f(half, 0.0, -half)
            glVertex3f(half, 0.0, half)
            glVertex3f(-half, 0.0, half)
            glEnd()
            if not self.wireframe:
                glDisable(GL_LIGHTING)
                glColor4f(0.0, 0.95, 1.0, 0.95)
                glLineWidth(2.0)
                glBegin(GL_LINE_LOOP)
                glVertex3f(-half, 0.0, -half)
                glVertex3f(half, 0.0, -half)
                glVertex3f(half, 0.0, half)
                glVertex3f(-half, 0.0, half)
                glEnd()
                self.apply_material()

        glPushMatrix()
        # Khi p = 0 (3D kín): đáy ở Y = -half để toàn bộ hình nằm cân đối tại Y in [-half, half].
        # Khi p = 1 (trải phẳng 2D): đáy trượt mượt lên Y = 0 để lưới trải phẳng nằm ngay giữa màn hình.
        base_y = -half * (1.0 - p)
        glTranslatef(0.0, base_y, 0.0)
        square()  # Đáy cố định

        # 1. Mặt trước (+Z): gập ngược chiều kim đồng hồ quanh trục X để dựng đứng lên Y
        glPushMatrix()
        glTranslatef(0.0, 0.0, half)
        glRotatef(-fold_ang, 1.0, 0.0, 0.0)
        glTranslatef(0.0, 0.0, half)
        square()
        glPopMatrix()

        # 2. Mặt sau (-Z) và Nắp trên (+Y): gập thuận chiều quanh trục X để dựng đứng lên Y
        glPushMatrix()
        glTranslatef(0.0, 0.0, -half)
        glRotatef(fold_ang, 1.0, 0.0, 0.0)
        glTranslatef(0.0, 0.0, -half)
        square()
        # Nắp trên gắn tiếp vào mặt sau, gập tiếp về phía trước
        glPushMatrix()
        glTranslatef(0.0, 0.0, -half)
        glRotatef(fold_ang, 1.0, 0.0, 0.0)
        glTranslatef(0.0, 0.0, -half)
        square()
        glPopMatrix()
        glPopMatrix()

        # 3. Mặt phải (+X): gập quanh trục Z
        glPushMatrix()
        glTranslatef(half, 0.0, 0.0)
        glRotatef(fold_ang, 0.0, 0.0, 1.0)
        glTranslatef(half, 0.0, 0.0)
        square()
        glPopMatrix()

        # 4. Mặt trái (-X): gập ngược chiều quanh trục Z
        glPushMatrix()
        glTranslatef(-half, 0.0, 0.0)
        glRotatef(-fold_ang, 0.0, 0.0, 1.0)
        glTranslatef(-half, 0.0, 0.0)
        square()
        glPopMatrix()

        glPopMatrix()

    def get_dimension_annotations(self):
        s = (self.side_length_cm * self.scale_factor) / 2.0
        return [
            ((s + 0.1, 0.0, s), f"a = {self.side_length_cm:.1f} cm", "#ffd700"),
            ((0.0, 0.0, 0.0), "O (Tâm)", "#ffffff"),
        ]


class PyramidGeometry(Geometry3D):
    """
    Hình Chóp 4 Mặt (Pyramid).
    Thông số:
    - base_size_cm: Kích thước cạnh đáy (cm).
    - height_cm: Chiều cao hình chóp (cm).
    """
    def __init__(self, base_size_cm: float = 10.0, height_cm: float = 12.0):
        super().__init__()
        self.base_size_cm = base_size_cm
        self.height_cm = height_cm

    def draw(self):
        """Vẽ hình chóp 3D với đáy hình vuông và 4 mặt bên hình tam giác."""
        self.apply_material()

        b = (self.base_size_cm * self.scale_factor) / 2.0
        h = (self.height_cm * self.scale_factor) / 2.0
        top = (0.0, h, 0.0)

        # 4 đỉnh đáy
        p1 = (-b, -h, b)
        p2 = (b, -h, b)
        p3 = (b, -h, -b)
        p4 = (-b, -h, -b)

        # Hàm tính vector pháp tuyến chuẩn cho mặt tam giác (cross product)
        def calc_normal(v1, v2, v3):
            ax, ay, az = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
            bx, by, bz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
            nx = ay * bz - az * by
            ny = az * bx - ax * bz
            nz = ax * by - ay * bx
            length = math.sqrt(nx*nx + ny*ny + nz*nz)
            if length > 0:
                return (nx/length, ny/length, nz/length)
            return (0.0, 1.0, 0.0)

        mode = GL_LINE_LOOP if self.wireframe else GL_TRIANGLES

        # Vẽ 4 mặt bên
        side_faces = [
            (top, p1, p2),
            (top, p2, p3),
            (top, p3, p4),
            (top, p4, p1)
        ]

        for v1, v2, v3 in side_faces:
            n = calc_normal(v1, v2, v3)
            glBegin(mode)
            glNormal3fv(n)
            glVertex3fv(v1)
            glVertex3fv(v2)
            glVertex3fv(v3)
            glEnd()

        # Vẽ mặt đáy
        glBegin(GL_LINE_LOOP if self.wireframe else GL_QUADS)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3fv(p1)
        glVertex3fv(p4)
        glVertex3fv(p3)
        glVertex3fv(p2)
        glEnd()

        # Hệ thống đường nét đứt đo kích thước đơn vị chuẩn SGK
        if self.show_dimension_lines and not self.wireframe:
            glDisable(GL_LIGHTING)
            glDisable(GL_DEPTH_TEST)

            # 1. Trục đường cao SO: từ đỉnh S(0, h, 0) vuông góc xuống tâm đáy O(0, -h, 0)
            draw_dashed_line_3d((0.0, h, 0.0), (0.0, -h, 0.0), color=(1.0, 0.88, 0.15, 0.95), line_width=2.5)

            # 2. Hai đường chéo đáy nét đứt nối các đỉnh đáy đối diện cắt nhau tại tâm O
            draw_dashed_line_3d(p1, p3, color=(1.0, 0.62, 0.15, 0.75), line_width=1.8)
            draw_dashed_line_3d(p2, p4, color=(1.0, 0.62, 0.15, 0.75), line_width=1.8)

            # 3. Ký hiệu góc vuông tại chân đường cao O
            draw_right_angle_3d((0.0, -h, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), size=min(0.22, b * 0.3))

            # 4. Các điểm mốc S (đỉnh), O (tâm đáy)
            draw_point_marker_3d((0.0, h, 0.0), color=(1.0, 1.0, 1.0, 1.0), point_size=8.0)
            draw_point_marker_3d((0.0, -h, 0.0), color=(1.0, 0.88, 0.15, 1.0), point_size=8.0)

            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)

    def draw_unfolded(self, progress: float):
        """Trải phẳng hình chóp thành hình ngôi sao / hoa 4 cánh (Square base + 4 Triangles)."""
        self.apply_material()
        b = (self.base_size_cm * self.scale_factor) / 2.0
        h = (self.height_cm * self.scale_factor) / 2.0
        p = max(0.0, min(1.0, progress))

        s_h = math.sqrt((2.0 * h) ** 2 + b ** 2)
        beta = math.degrees(math.atan2(2.0 * h, b))
        fold_ang = (180.0 - beta) * (1.0 - p)

        mode = GL_LINE_LOOP if self.wireframe else GL_TRIANGLES

        def draw_tri(v1, v2, v3):
            glBegin(mode)
            glNormal3f(0.0, 1.0, 0.0)
            glVertex3fv(v1)
            glVertex3fv(v2)
            glVertex3fv(v3)
            glEnd()
            if not self.wireframe:
                glDisable(GL_LIGHTING)
                glColor4f(0.0, 0.95, 1.0, 0.95)
                glLineWidth(2.0)
                glBegin(GL_LINE_LOOP)
                glVertex3fv(v1)
                glVertex3fv(v2)
                glVertex3fv(v3)
                glEnd()
                self.apply_material()

        glPushMatrix()
        # Di chuyển mượt lên tâm Y = 0 khi trải phẳng 2D
        glTranslatef(0.0, h * p, 0.0)

        # Đáy hình vuông cố định tại Y = -h
        glBegin(GL_LINE_LOOP if self.wireframe else GL_QUADS)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(-b, -h, -b)
        glVertex3f(b, -h, -b)
        glVertex3f(b, -h, b)
        glVertex3f(-b, -h, b)
        glEnd()

        if not self.wireframe:
            glDisable(GL_LIGHTING)
            glColor4f(0.0, 0.95, 1.0, 0.95)
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            glVertex3f(-b, -h, -b)
            glVertex3f(b, -h, -b)
            glVertex3f(b, -h, b)
            glVertex3f(-b, -h, b)
            glEnd()
            self.apply_material()

        # 1. Mặt trước (+Z)
        glPushMatrix()
        glTranslatef(0.0, -h, b)
        glRotatef(-fold_ang, 1.0, 0.0, 0.0)
        draw_tri((-b, 0.0, 0.0), (b, 0.0, 0.0), (0.0, 0.0, s_h))
        glPopMatrix()

        # 2. Mặt sau (-Z)
        glPushMatrix()
        glTranslatef(0.0, -h, -b)
        glRotatef(fold_ang, 1.0, 0.0, 0.0)
        draw_tri((b, 0.0, 0.0), (-b, 0.0, 0.0), (0.0, 0.0, -s_h))
        glPopMatrix()

        # 3. Mặt phải (+X)
        glPushMatrix()
        glTranslatef(b, -h, 0.0)
        glRotatef(fold_ang, 0.0, 0.0, 1.0)
        draw_tri((0.0, 0.0, b), (0.0, 0.0, -b), (s_h, 0.0, 0.0))
        glPopMatrix()

        # 4. Mặt trái (-X)
        glPushMatrix()
        glTranslatef(-b, -h, 0.0)
        glRotatef(-fold_ang, 0.0, 0.0, 1.0)
        draw_tri((0.0, 0.0, -b), (0.0, 0.0, b), (-s_h, 0.0, 0.0))
        glPopMatrix()

        glPopMatrix()

    def get_dimension_annotations(self):
        b = (self.base_size_cm * self.scale_factor) / 2.0
        h = (self.height_cm * self.scale_factor) / 2.0
        return [
            ((0.0, 0.0, 0.0), f"h = {self.height_cm:.1f} cm", "#ffd700"),
            ((b + 0.1, -h, 0.0), f"a = {self.base_size_cm:.1f} cm", "#ff9900"),
            ((0.0, h, 0.0), "S (Đỉnh)", "#ffffff"),
            ((0.0, -h, 0.0), "O (Tâm đáy)", "#ffd700"),
        ]


class SphereGeometry(Geometry3D):
    """
    Khối Cầu 3D (Sphere).
    Thông số:
    - radius_cm: Bán kính khối cầu (cm).
    - slices, stacks: Độ phân giải vòng kinh tuyến & vĩ tuyến.
    """
    def __init__(self, radius_cm: float = 6.0, slices: int = 48, stacks: int = 48):
        super().__init__()
        self.radius_cm = radius_cm
        self.slices = slices
        self.stacks = stacks

    def draw(self):
        """Vẽ khối cầu với bề mặt bóng mịn chuẩn 3D và trục kích thước tinh tế."""
        self.apply_material()
        r = self.radius_cm * self.scale_factor

        # 1. Bề mặt khối cầu mượt mà với vector pháp tuyến chuẩn (Y là trục đứng Bắc-Nam)
        for i in range(self.stacks):
            lat0 = math.pi * (-0.5 + float(i) / self.stacks)
            y0 = math.sin(lat0)
            yr0 = math.cos(lat0)

            lat1 = math.pi * (-0.5 + float(i + 1) / self.stacks)
            y1 = math.sin(lat1)
            yr1 = math.cos(lat1)

            glBegin(GL_LINE_LOOP if self.wireframe else GL_QUAD_STRIP)
            for j in range(self.slices + 1):
                lng = 2.0 * math.pi * float(j) / self.slices
                cos_lng = math.cos(lng)
                sin_lng = math.sin(lng)

                # Điểm trên vĩ tuyến lat0
                nx0, ny0, nz0 = cos_lng * yr0, y0, sin_lng * yr0
                glNormal3f(nx0, ny0, nz0)
                glVertex3f(nx0 * r, ny0 * r, nz0 * r)

                # Điểm trên vĩ tuyến lat1
                nx1, ny1, nz1 = cos_lng * yr1, y1, sin_lng * yr1
                glNormal3f(nx1, ny1, nz1)
                glVertex3f(nx1 * r, ny1 * r, nz1 * r)
            glEnd()

        # 2. Các đường dẫn hướng trực quan tinh tế (không làm rối mắt người xem)
        if not self.wireframe:
            glDisable(GL_LIGHTING)

            # A. Vòng tròn lớn xích đạo (Equator Circle trên mặt phẳng XZ, Y = 0)
            # Màu vàng kim thanh nhã, viền chuẩn SGK Hình học 12
            glColor4f(1.0, 0.85, 0.2, 0.9)
            glLineWidth(2.2)
            glBegin(GL_LINE_LOOP)
            num_eq_steps = 72
            for step in range(num_eq_steps):
                ang = 2.0 * math.pi * step / num_eq_steps
                glVertex3f(math.cos(ang) * r, 0.0, math.sin(ang) * r)
            glEnd()

            # B. Một đường kinh tuyến tham chiếu chính (Meridian qua 2 cực trên mặt phẳng YZ, X = 0)
            # Thanh mảnh, hơi mờ để cảm nhận chiều sâu 3D khi xoay khối cầu mà không bị chói
            glColor4f(0.0, 0.92, 1.0, 0.35)
            glLineWidth(1.2)
            glBegin(GL_LINE_LOOP)
            for step in range(num_eq_steps):
                ang = 2.0 * math.pi * step / num_eq_steps
                glVertex3f(0.0, math.sin(ang) * r, math.cos(ang) * r)
            glEnd()

            # 3. Hệ thống đường nét đứt đo kích thước đơn vị chuẩn SGK Hình học Không gian
            if self.show_dimension_lines:
                glDisable(GL_DEPTH_TEST)

                # (1) Trục thẳng đứng N - S qua 2 cực và tâm O (Đường kính đứng D = 2R)
                draw_dashed_line_3d((0.0, r, 0.0), (0.0, -r, 0.0), color=(1.0, 0.88, 0.15, 0.95), line_width=2.2)

                # (2) Bán kính R nối từ tâm O(0, 0, 0) ra điểm A trên đường tròn xích đạo (chếch 35 độ về phía trước)
                rad_angle = math.radians(35.0)
                ax = math.cos(rad_angle) * r
                az = math.sin(rad_angle) * r
                draw_dashed_line_3d((0.0, 0.0, 0.0), (ax, 0.0, az), color=(1.0, 0.62, 0.15, 0.95), line_width=2.5)

                # (3) Ký hiệu góc vuông tại tâm O giữa trục đứng Y và bán kính OA
                draw_right_angle_3d((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (math.cos(rad_angle), 0.0, math.sin(rad_angle)), size=min(0.22, r * 0.28))

                # (4) Các điểm mốc Hologram: Cực Bắc N, Cực Nam S, Tâm O, Điểm A trên mặt cầu
                draw_point_marker_3d((0.0, r, 0.0), color=(1.0, 1.0, 1.0, 1.0), point_size=8.0)
                draw_point_marker_3d((0.0, -r, 0.0), color=(1.0, 0.88, 0.15, 1.0), point_size=7.0)
                draw_point_marker_3d((0.0, 0.0, 0.0), color=(1.0, 0.88, 0.15, 1.0), point_size=8.0)
                draw_point_marker_3d((ax, 0.0, az), color=(0.15, 0.95, 1.0, 1.0), point_size=7.5)

                glEnable(GL_DEPTH_TEST)

            glEnable(GL_LIGHTING)

    def draw_unfolded(self, progress: float):
        """Tách đôi 2 bán cầu dọc theo trục Y để lộ mặt cắt đĩa tròn xích đạo (Equatorial Disc S = pi*R^2)."""
        self.apply_material()
        r = self.radius_cm * self.scale_factor
        p = max(0.0, min(1.0, progress))
        gap = r * 0.9 * p

        # Bán cầu trên (+Y) di chuyển lên +gap
        glPushMatrix()
        glTranslatef(0.0, gap, 0.0)
        for i in range(self.stacks // 2, self.stacks):
            lat0 = math.pi * (-0.5 + float(i) / self.stacks)
            y0, yr0 = math.sin(lat0), math.cos(lat0)
            lat1 = math.pi * (-0.5 + float(i + 1) / self.stacks)
            y1, yr1 = math.sin(lat1), math.cos(lat1)

            glBegin(GL_LINE_LOOP if self.wireframe else GL_QUAD_STRIP)
            for j in range(self.slices + 1):
                lng = 2.0 * math.pi * float(j) / self.slices
                cos_lng, sin_lng = math.cos(lng), math.sin(lng)

                nx0, ny0, nz0 = cos_lng * yr0, y0, sin_lng * yr0
                glNormal3f(nx0, ny0, nz0)
                glVertex3f(nx0 * r, ny0 * r, nz0 * r)

                nx1, ny1, nz1 = cos_lng * yr1, y1, sin_lng * yr1
                glNormal3f(nx1, ny1, nz1)
                glVertex3f(nx1 * r, ny1 * r, nz1 * r)
            glEnd()

        if not self.wireframe:
            glBegin(GL_TRIANGLE_FAN)
            glNormal3f(0.0, -1.0, 0.0)
            glVertex3f(0.0, 0.0, 0.0)
            for j in range(self.slices + 1):
                lng = -2.0 * math.pi * float(j) / self.slices
                glVertex3f(math.cos(lng) * r, 0.0, math.sin(lng) * r)
            glEnd()
            glDisable(GL_LIGHTING)
            glColor4f(1.0, 0.85, 0.2, 0.95)
            glLineWidth(2.2)
            glBegin(GL_LINE_LOOP)
            for j in range(self.slices + 1):
                lng = 2.0 * math.pi * float(j) / self.slices
                glVertex3f(math.cos(lng) * r, 0.0, math.sin(lng) * r)
            glEnd()
            self.apply_material()
        glPopMatrix()

        # Bán cầu dưới (-Y) di chuyển xuống -gap
        glPushMatrix()
        glTranslatef(0.0, -gap, 0.0)
        for i in range(self.stacks // 2):
            lat0 = math.pi * (-0.5 + float(i) / self.stacks)
            y0, yr0 = math.sin(lat0), math.cos(lat0)
            lat1 = math.pi * (-0.5 + float(i + 1) / self.stacks)
            y1, yr1 = math.sin(lat1), math.cos(lat1)

            glBegin(GL_LINE_LOOP if self.wireframe else GL_QUAD_STRIP)
            for j in range(self.slices + 1):
                lng = 2.0 * math.pi * float(j) / self.slices
                cos_lng, sin_lng = math.cos(lng), math.sin(lng)

                nx0, ny0, nz0 = cos_lng * yr0, y0, sin_lng * yr0
                glNormal3f(nx0, ny0, nz0)
                glVertex3f(nx0 * r, ny0 * r, nz0 * r)

                nx1, ny1, nz1 = cos_lng * yr1, y1, sin_lng * yr1
                glNormal3f(nx1, ny1, nz1)
                glVertex3f(nx1 * r, ny1 * r, nz1 * r)
            glEnd()

        if not self.wireframe:
            glBegin(GL_TRIANGLE_FAN)
            glNormal3f(0.0, 1.0, 0.0)
            glVertex3f(0.0, 0.0, 0.0)
            for j in range(self.slices + 1):
                lng = 2.0 * math.pi * float(j) / self.slices
                glVertex3f(math.cos(lng) * r, 0.0, math.sin(lng) * r)
            glEnd()
            glDisable(GL_LIGHTING)
            glColor4f(1.0, 0.85, 0.2, 0.95)
            glLineWidth(2.2)
            glBegin(GL_LINE_LOOP)
            for j in range(self.slices + 1):
                lng = 2.0 * math.pi * float(j) / self.slices
                glVertex3f(math.cos(lng) * r, 0.0, math.sin(lng) * r)
            glEnd()
            self.apply_material()
        glPopMatrix()

    def get_dimension_annotations(self):
        r = self.radius_cm * self.scale_factor
        rad_angle = math.radians(35.0)
        ax = math.cos(rad_angle) * r
        az = math.sin(rad_angle) * r
        return [
            ((0.0, r, 0.0), "N (Cực Bắc)", "#ffffff"),
            ((0.0, -0.05, 0.0), "O (Tâm)", "#ffd700"),
            ((ax * 0.5, 0.12, az * 0.5), f"R = {self.radius_cm:.1f} cm", "#ff9900"),
            ((ax, 0.0, az), "A", "#00f0ff"),
        ]



class CylinderGeometry(Geometry3D):
    """
    Hình Trụ 3D (Cylinder).
    Thông số:
    - radius_cm: Bán kính mặt đáy (cm).
    - height_cm: Chiều cao hình trụ (cm).
    - slices: Độ phân giải vòng tròn.
    """
    def __init__(self, radius_cm: float = 5.0, height_cm: float = 10.0, slices: int = 32):
        super().__init__()
        self.radius_cm = radius_cm
        self.height_cm = height_cm
        self.slices = slices

    def draw(self):
        """Vẽ hình trụ với thân trụ và 2 nắp hình tròn."""
        self.apply_material()
        r = self.radius_cm * self.scale_factor
        h2 = (self.height_cm * self.scale_factor) / 2.0

        # Thân hình trụ (Quad Strip)
        glBegin(GL_LINE_LOOP if self.wireframe else GL_QUAD_STRIP)
        for i in range(self.slices + 1):
            angle = 2.0 * math.pi * i / self.slices
            x = math.cos(angle)
            z = math.sin(angle)

            glNormal3f(x, 0.0, z)
            glVertex3f(x * r, h2, z * r)
            glVertex3f(x * r, -h2, z * r)
        glEnd()

        # Nắp trên (+Y)
        glBegin(GL_LINE_LOOP if self.wireframe else GL_TRIANGLE_FAN)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, h2, 0.0)
        for i in range(self.slices + 1):
            angle = 2.0 * math.pi * i / self.slices
            glVertex3f(math.cos(angle) * r, h2, math.sin(angle) * r)
        glEnd()

        # Nắp dưới (-Y)
        glBegin(GL_LINE_LOOP if self.wireframe else GL_TRIANGLE_FAN)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(0.0, -h2, 0.0)
        for i in range(self.slices + 1):
            angle = -2.0 * math.pi * i / self.slices
            glVertex3f(math.cos(angle) * r, -h2, math.sin(angle) * r)
        glEnd()

        # Hệ thống đường nét đứt đo kích thước đơn vị chuẩn SGK
        if self.show_dimension_lines and not self.wireframe:
            glDisable(GL_LIGHTING)
            glDisable(GL_DEPTH_TEST)

            # 1. Trục đường cao h: nối tâm 2 đáy O1(0, h2, 0) xuống O2(0, -h2, 0)
            draw_dashed_line_3d((0.0, h2, 0.0), (0.0, -h2, 0.0), color=(1.0, 0.88, 0.15, 0.95), line_width=2.5)

            # 2. Bán kính đáy trên: O1(0, h2, 0) -> A1(r, h2, 0)
            draw_dashed_line_3d((0.0, h2, 0.0), (r, h2, 0.0), color=(1.0, 0.62, 0.15, 0.95), line_width=2.2)

            # 3. Bán kính đáy dưới: O2(0, -h2, 0) -> A2(r, -h2, 0)
            draw_dashed_line_3d((0.0, -h2, 0.0), (r, -h2, 0.0), color=(1.0, 0.62, 0.15, 0.95), line_width=2.2)

            # 4. Ký hiệu góc vuông tại O1 và O2
            draw_right_angle_3d((0.0, h2, 0.0), (0.0, -1.0, 0.0), (1.0, 0.0, 0.0), size=min(0.2, r * 0.28))
            draw_right_angle_3d((0.0, -h2, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), size=min(0.2, r * 0.28))

            # 5. Các điểm mốc tâm đáy trên O1, tâm đáy dưới O2, điểm vành A1, A2
            draw_point_marker_3d((0.0, h2, 0.0), color=(1.0, 1.0, 1.0, 1.0), point_size=8.0)
            draw_point_marker_3d((0.0, -h2, 0.0), color=(1.0, 0.88, 0.15, 1.0), point_size=8.0)
            draw_point_marker_3d((r, h2, 0.0), color=(0.15, 0.95, 1.0, 1.0), point_size=7.0)
            draw_point_marker_3d((r, -h2, 0.0), color=(0.15, 0.95, 1.0, 1.0), point_size=7.0)

            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)

    def draw_unfolded(self, progress: float):
        """Trải phẳng hình trụ: Thân trụ mở thành hình chữ nhật (2*pi*R x h), 2 nắp tròn gắn 2 bên mép."""
        self.apply_material()
        r = self.radius_cm * self.scale_factor
        h2 = (self.height_cm * self.scale_factor) / 2.0
        p = max(0.0, min(1.0, progress))

        # 1. Thân trụ mở dần từ cong tròn -> hình chữ nhật phẳng
        steps = self.slices
        glBegin(GL_LINE_LOOP if self.wireframe else GL_QUAD_STRIP)
        for i in range(steps + 1):
            phi = -math.pi + 2.0 * math.pi * i / steps
            x_3d = r * math.sin(phi)
            z_3d = r * math.cos(phi)
            x_flat = r * phi
            z_flat = r

            x = (1.0 - p) * x_3d + p * x_flat
            z = (1.0 - p) * z_3d + p * z_flat

            nx = (1.0 - p) * math.sin(phi)
            nz = (1.0 - p) * math.cos(phi) + p
            nl = math.sqrt(nx*nx + nz*nz) or 1.0
            glNormal3f(nx/nl, 0.0, nz/nl)

            glVertex3f(x, h2, z)
            glVertex3f(x, -h2, z)
        glEnd()

        # Viền neon sáng bao quanh thân hình chữ nhật khi phẳng dần
        if not self.wireframe:
            glDisable(GL_LIGHTING)
            glColor4f(0.0, 0.95, 1.0, 0.95)
            glLineWidth(2.0)
            glBegin(GL_LINE_STRIP)
            for i in range(steps + 1):
                phi = -math.pi + 2.0 * math.pi * i / steps
                x = (1.0 - p) * (r * math.sin(phi)) + p * (r * phi)
                z = (1.0 - p) * (r * math.cos(phi)) + p * r
                glVertex3f(x, h2, z)
            glEnd()
            glBegin(GL_LINE_STRIP)
            for i in range(steps + 1):
                phi = -math.pi + 2.0 * math.pi * i / steps
                x = (1.0 - p) * (r * math.sin(phi)) + p * (r * phi)
                z = (1.0 - p) * (r * math.cos(phi)) + p * r
                glVertex3f(x, -h2, z)
            glEnd()
            self.apply_material()

        # 2. Hai nắp tròn xoay dần từ phương ngang sang phẳng (gập 90 độ * p)
        # Nắp trên: bản lề tại (0, h2, r)
        glPushMatrix()
        glTranslatef(0.0, h2, r)
        glRotatef(90.0 * p, 1.0, 0.0, 0.0)
        glTranslatef(0.0, 0.0, -r)
        glBegin(GL_LINE_LOOP if self.wireframe else GL_TRIANGLE_FAN)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        for i in range(self.slices + 1):
            angle = 2.0 * math.pi * i / self.slices
            glVertex3f(math.cos(angle) * r, 0.0, math.sin(angle) * r)
        glEnd()
        if not self.wireframe:
            glDisable(GL_LIGHTING)
            glColor4f(1.0, 0.85, 0.2, 0.95)
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            for i in range(self.slices + 1):
                angle = 2.0 * math.pi * i / self.slices
                glVertex3f(math.cos(angle) * r, 0.0, math.sin(angle) * r)
            glEnd()
            self.apply_material()
        glPopMatrix()

        # Nắp dưới: bản lề tại (0, -h2, r)
        glPushMatrix()
        glTranslatef(0.0, -h2, r)
        glRotatef(-90.0 * p, 1.0, 0.0, 0.0)
        glTranslatef(0.0, 0.0, -r)
        glBegin(GL_LINE_LOOP if self.wireframe else GL_TRIANGLE_FAN)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        for i in range(self.slices + 1):
            angle = -2.0 * math.pi * i / self.slices
            glVertex3f(math.cos(angle) * r, 0.0, math.sin(angle) * r)
        glEnd()
        if not self.wireframe:
            glDisable(GL_LIGHTING)
            glColor4f(1.0, 0.85, 0.2, 0.95)
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            for i in range(self.slices + 1):
                angle = -2.0 * math.pi * i / self.slices
                glVertex3f(math.cos(angle) * r, 0.0, math.sin(angle) * r)
            glEnd()
            self.apply_material()
        glPopMatrix()

    def get_dimension_annotations(self):
        r = self.radius_cm * self.scale_factor
        h2 = (self.height_cm * self.scale_factor) / 2.0
        return [
            ((0.0, 0.0, 0.0), f"h = {self.height_cm:.1f} cm", "#ffd700"),
            ((r * 0.5, -h2, 0.0), f"R = {self.radius_cm:.1f} cm", "#ff9900"),
            ((0.0, h2, 0.0), "O₁ (Đáy trên)", "#ffffff"),
            ((0.0, -h2, 0.0), "O₂ (Đáy dưới)", "#ffd700"),
        ]


class TorusGeometry(Geometry3D):
    """
    Khối Xuyến / Bánh Xe 3D (Torus).
    Thông số:
    - major_radius_cm: Bán kính lớn (từ tâm tới lõi vòng) (cm).
    - minor_radius_cm: Bán kính ống nhỏ (cm).
    """
    def __init__(self, major_radius_cm: float = 6.0, minor_radius_cm: float = 2.0, num_major: int = 64, num_minor: int = 32):
        super().__init__()
        self.major_radius_cm = major_radius_cm
        self.minor_radius_cm = minor_radius_cm
        self.num_major = num_major
        self.num_minor = num_minor

    def draw(self):
        """Vẽ hình xuyến (Torus) bóng mịn, triệt tiêu hoàn toàn lỗi rách lưới và xé hình."""
        self.apply_material()
        R = self.major_radius_cm * self.scale_factor
        r = self.minor_radius_cm * self.scale_factor

        # Bật Two-sided lighting và tăng ambient nhẹ cho vùng khuất trong lòng ống
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.35, 0.35, 0.4, 1.0])

        if not self.wireframe:
            glEnable(GL_CULL_FACE)
            glCullFace(GL_BACK)

        # 1. Vẽ mesh Torus với thứ tự đỉnh chuẩn CCW (pháp tuyến hướng ra ngoài)
        for i in range(self.num_major):
            u0 = i * 2.0 * math.pi / self.num_major
            u1 = (i + 1) * 2.0 * math.pi / self.num_major
            cos_u0, sin_u0 = math.cos(u0), math.sin(u0)
            cos_u1, sin_u1 = math.cos(u1), math.sin(u1)

            glBegin(GL_LINE_LOOP if self.wireframe else GL_QUAD_STRIP)
            for j in range(self.num_minor + 1):
                v = j * 2.0 * math.pi / self.num_minor
                cos_v, sin_v = math.cos(v), math.sin(v)

                # Đỉnh trên u1
                nx1 = cos_v * cos_u1
                ny1 = sin_v
                nz1 = cos_v * sin_u1
                x1 = (R + r * cos_v) * cos_u1
                y1 = r * sin_v
                z1 = (R + r * cos_v) * sin_u1

                # Đỉnh trên u0
                nx0 = cos_v * cos_u0
                ny0 = sin_v
                nz0 = cos_v * sin_u0
                x0 = (R + r * cos_v) * cos_u0
                y0 = r * sin_v
                z0 = (R + r * cos_v) * sin_u0

                glNormal3f(nx1, ny1, nz1)
                glVertex3f(x1, y1, z1)

                glNormal3f(nx0, ny0, nz0)
                glVertex3f(x0, y0, z0)
            glEnd()

        if not self.wireframe:
            glDisable(GL_CULL_FACE)

        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, GL_FALSE)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.2, 0.2, 0.2, 1.0])

        # 2. Đường nét trực quan & kích thước toán học
        if not self.wireframe:
            glDisable(GL_LIGHTING)

            # A. Đường tròn tiết diện sinh (Generating circle) tại góc nghiêng 35 độ
            ang = math.radians(35.0)
            cos_a, sin_a = math.cos(ang), math.sin(ang)
            cx, cz = cos_a * R, sin_a * R

            glColor4f(1.0, 0.85, 0.2, 0.95)
            glLineWidth(2.2)
            glBegin(GL_LINE_LOOP)
            for step in range(64):
                v = 2.0 * math.pi * step / 64.0
                px = (R + r * math.cos(v)) * cos_a
                py = r * math.sin(v)
                pz = (R + r * math.cos(v)) * sin_a
                glVertex3f(px, py, pz)
            glEnd()

            # B. Hệ thống đường nét đứt đo kích thước chuẩn SGK
            if self.show_dimension_lines:
                glDisable(GL_DEPTH_TEST)

                # 1. Bán kính lớn R: Từ tâm xuyến O(0,0,0) -> tâm mặt cắt C(cx, 0, cz)
                draw_dashed_line_3d((0.0, 0.0, 0.0), (cx, 0.0, cz), color=(1.0, 0.88, 0.15, 0.95), line_width=2.5)

                # 2. Bán kính nhỏ r: Từ tâm mặt cắt C(cx, 0, cz) thẳng đứng lên đỉnh mặt cắt (cx, r, cz)
                draw_dashed_line_3d((cx, 0.0, cz), (cx, r, cz), color=(1.0, 0.62, 0.15, 0.95), line_width=2.5)

                # 3. Nửa bán kính nhỏ đối xứng hướng xuống nét mờ
                draw_dashed_line_3d((cx, 0.0, cz), (cx, -r, cz), color=(1.0, 0.88, 0.15, 0.45), line_width=1.5)

                # 4. Ký hiệu góc vuông tại C giữa bán kính lớn R và bán kính nhỏ r
                draw_right_angle_3d((cx, 0.0, cz), (-cos_a, 0.0, -sin_a), (0.0, 1.0, 0.0), size=min(0.2, r * 0.35))

                # 5. Các điểm mốc Hologram: O (Tâm xuyến), C (Tâm ống), M (Đỉnh mặt cắt)
                draw_point_marker_3d((0.0, 0.0, 0.0), color=(1.0, 0.88, 0.15, 1.0), point_size=8.0)
                draw_point_marker_3d((cx, 0.0, cz), color=(1.0, 1.0, 1.0, 1.0), point_size=8.0)
                draw_point_marker_3d((cx, r, cz), color=(0.15, 0.95, 1.0, 1.0), point_size=7.5)

                glEnable(GL_DEPTH_TEST)

            glEnable(GL_LIGHTING)

    def get_dimension_annotations(self):
        R = self.major_radius_cm * self.scale_factor
        r = self.minor_radius_cm * self.scale_factor
        ang = math.radians(35.0)
        cos_a, sin_a = math.cos(ang), math.sin(ang)
        cx, cz = cos_a * R, sin_a * R

        return [
            ((0.0, -0.06, 0.0), "O (Tâm xuyến)", "#ffd700"),
            ((cx * 0.5, 0.12, cz * 0.5), f"R = {self.major_radius_cm:.1f} cm", "#ffd700"),
            ((cx + 0.08, r * 0.5, cz), f"r = {self.minor_radius_cm:.1f} cm", "#ff9900"),
            ((cx, 0.0, cz), "C (Tâm ống)", "#ffffff"),
            ((cx, r, cz), "M", "#00f0ff"),
        ]



class ConeGeometry(Geometry3D):
    """
    Hình Nón 3D (Cone).
    Thông số:
    - radius_cm: Bán kính mặt đáy (cm).
    - height_cm: Chiều cao hình nón (cm).
    - slices: Độ phân giải vòng tròn đáy.
    """
    def __init__(self, radius_cm: float = 5.0, height_cm: float = 10.0, slices: int = 36):
        super().__init__()
        self.radius_cm = radius_cm
        self.height_cm = height_cm
        self.slices = slices

    def draw(self):
        """Vẽ hình nón với mặt nón xung quanh và mặt đáy hình tròn."""
        self.apply_material()
        r = self.radius_cm * self.scale_factor
        h = (self.height_cm * self.scale_factor) / 2.0

        # Mặt nón xung quanh (Triangle Fan với vector pháp tuyến chuẩn)
        glBegin(GL_LINE_LOOP if self.wireframe else GL_TRIANGLE_FAN)
        glNormal3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, h, 0.0)
        slant = math.sqrt(r * r + (2.0 * h) * (2.0 * h))
        ny = r / slant
        nr = (2.0 * h) / slant
        for i in range(self.slices + 1):
            angle = 2.0 * math.pi * i / self.slices
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            glNormal3f(cos_a * nr, ny, sin_a * nr)
            glVertex3f(cos_a * r, -h, sin_a * r)
        glEnd()

        # Mặt đáy hình tròn (-Y)
        glBegin(GL_LINE_LOOP if self.wireframe else GL_TRIANGLE_FAN)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(0.0, -h, 0.0)
        for i in range(self.slices + 1):
            angle = -2.0 * math.pi * i / self.slices
            glVertex3f(math.cos(angle) * r, -h, math.sin(angle) * r)
        glEnd()

        # Hệ thống đường nét đứt thể hiện các đơn vị đo kích thước chuẩn SGK
        if self.show_dimension_lines and not self.wireframe:
            glDisable(GL_LIGHTING)
            glDisable(GL_DEPTH_TEST)

            # 1. Trục chiều cao h: Nét đứt từ đỉnh S(0, h, 0) vuông góc xuống tâm đáy O(0, -h, 0)
            draw_dashed_line_3d((0.0, h, 0.0), (0.0, -h, 0.0), color=(1.0, 0.88, 0.15, 0.95), line_width=2.5)

            # 2. Bán kính đáy R: Nét đứt từ tâm đáy O(0, -h, 0) ra mép vành A(r, -h, 0)
            draw_dashed_line_3d((0.0, -h, 0.0), (r, -h, 0.0), color=(1.0, 0.62, 0.15, 0.95), line_width=2.5)

            # 3. Nửa đường kính đối diện nét đứt mờ: từ O(0, -h, 0) ra B(-r, -h, 0)
            draw_dashed_line_3d((0.0, -h, 0.0), (-r, -h, 0.0), color=(1.0, 0.88, 0.15, 0.45), line_width=1.5)

            # 4. Ký hiệu góc vuông tại O giữa trục chiều cao và bán kính đáy
            draw_right_angle_3d((0.0, -h, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), size=min(0.22, r * 0.28))

            # 5. Các điểm mốc S (đỉnh), O (tâm đáy), A (điểm trên đường tròn đáy)
            draw_point_marker_3d((0.0, h, 0.0), color=(1.0, 1.0, 1.0, 1.0), point_size=8.0)
            draw_point_marker_3d((0.0, -h, 0.0), color=(1.0, 0.88, 0.15, 1.0), point_size=8.0)
            draw_point_marker_3d((r, -h, 0.0), color=(0.15, 0.95, 1.0, 1.0), point_size=7.0)

            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)

    def draw_unfolded(self, progress: float):
        """Trải phẳng hình nón: Mặt nón mở thành hình quạt tròn (bán kính l, góc 2*pi*R/l), đáy tròn tiếp xúc mép quạt."""
        self.apply_material()
        r = self.radius_cm * self.scale_factor
        h = (self.height_cm * self.scale_factor) / 2.0
        p = max(0.0, min(1.0, progress))

        slant = math.sqrt(r * r + (2.0 * h) * (2.0 * h))
        sector_angle = (r / slant) * (2.0 * math.pi)

        # 1. Mặt nón mở dần thành hình quạt tròn
        steps = self.slices
        glBegin(GL_LINE_LOOP if self.wireframe else GL_TRIANGLE_FAN)
        glNormal3f(0.0, 0.0, 1.0)
        glVertex3f(0.0, h, 0.0)

        for i in range(steps + 1):
            t = (float(i) / steps) - 0.5
            phi_3d = t * 2.0 * math.pi
            x_3d = r * math.sin(phi_3d)
            y_3d = -h
            z_3d = r * math.cos(phi_3d)

            psi_flat = t * sector_angle
            x_flat = slant * math.sin(psi_flat)
            y_flat = h - slant * math.cos(psi_flat)
            z_flat = 0.0

            x = (1.0 - p) * x_3d + p * x_flat
            y = (1.0 - p) * y_3d + p * y_flat
            z = (1.0 - p) * z_3d + p * z_flat

            glVertex3f(x, y, z)
        glEnd()

        # Viền quạt tròn sáng neon
        if not self.wireframe:
            glDisable(GL_LIGHTING)
            glColor4f(0.0, 0.95, 1.0, 0.95)
            glLineWidth(2.0)
            glBegin(GL_LINE_STRIP)
            glVertex3f(0.0, h, 0.0)
            for i in range(steps + 1):
                t = (float(i) / steps) - 0.5
                phi_3d = t * 2.0 * math.pi
                psi_flat = t * sector_angle
                x = (1.0 - p) * (r * math.sin(phi_3d)) + p * (slant * math.sin(psi_flat))
                y = (1.0 - p) * (-h) + p * (h - slant * math.cos(psi_flat))
                z = (1.0 - p) * (r * math.cos(phi_3d)) + p * 0.0
                glVertex3f(x, y, z)
            glVertex3f(0.0, h, 0.0)
            glEnd()
            self.apply_material()

        # 2. Đáy hình tròn xoay dần từ phương ngang ra phẳng
        glPushMatrix()
        hinge_y = (1.0 - p) * (-h) + p * (h - slant)
        hinge_z = (1.0 - p) * r + p * 0.0
        glTranslatef(0.0, hinge_y, hinge_z)
        glRotatef(-90.0 * p, 1.0, 0.0, 0.0)
        glTranslatef(0.0, 0.0, -r)

        glBegin(GL_LINE_LOOP if self.wireframe else GL_TRIANGLE_FAN)
        glNormal3f(0.0, -1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        for i in range(self.slices + 1):
            angle = -2.0 * math.pi * i / self.slices
            glVertex3f(math.cos(angle) * r, 0.0, math.sin(angle) * r)
        glEnd()

        if not self.wireframe:
            glDisable(GL_LIGHTING)
            glColor4f(1.0, 0.85, 0.2, 0.95)
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            for i in range(self.slices + 1):
                angle = -2.0 * math.pi * i / self.slices
                glVertex3f(math.cos(angle) * r, 0.0, math.sin(angle) * r)
            glEnd()
            self.apply_material()

        glPopMatrix()

    def get_dimension_annotations(self):
        r = self.radius_cm * self.scale_factor
        h = (self.height_cm * self.scale_factor) / 2.0
        return [
            ((0.0, 0.0, 0.0), f"h = {self.height_cm:.1f} cm", "#ffd700"),
            ((r * 0.5, -h, 0.0), f"R = {self.radius_cm:.1f} cm", "#ff9900"),
            ((0.0, h, 0.0), "S (Đỉnh)", "#ffffff"),
            ((0.0, -h, 0.0), "O (Tâm đáy)", "#ffd700"),
            ((r, -h, 0.0), "A", "#00f0ff"),
        ]


class RectangularPrismGeometry(CubeGeometry):
    """
    Hình Hộp Chữ Nhật (Rectangular Prism).
    Thông số:
    - length_cm: Chiều dài đáy (cm) (theo trục X).
    - width_cm: Chiều rộng đáy (cm) (theo trục Z).
    - height_cm: Chiều cao (cm) (theo trục Y).
    """
    def __init__(self, length_cm=12.0, width_cm=8.0, height_cm=6.0):
        super().__init__(1.0)
        self.length_cm = length_cm
        self.width_cm = width_cm
        self.height_cm = height_cm

    def draw(self):
        self.side_length_cm = 1.0
        self.apply_material()
        x = (self.length_cm * self.scale_factor) / 2.0
        y = (self.height_cm * self.scale_factor) / 2.0
        z = (self.width_cm * self.scale_factor) / 2.0

        faces = [
            ((0, 0, 1), [(-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]),
            ((0, 0, -1), [(-x, -y, -z), (-x, y, -z), (x, y, -z), (x, -y, -z)]),
            ((0, 1, 0), [(-x, y, -z), (-x, y, z), (x, y, z), (x, y, -z)]),
            ((0, -1, 0), [(-x, -y, -z), (x, -y, -z), (x, -y, z), (-x, -y, z)]),
            ((1, 0, 0), [(x, -y, -z), (x, y, -z), (x, y, z), (x, -y, z)]),
            ((-1, 0, 0), [(-x, -y, -z), (-x, -y, z), (-x, y, z), (-x, y, -z)])
        ]
        for n, vs in faces:
            glBegin(GL_LINE_LOOP if self.wireframe else GL_QUADS)
            glNormal3fv(n)
            for v in vs:
                glVertex3fv(v)
            glEnd()

        # Hệ thống đường nét đứt đo kích thước đơn vị
        if self.show_dimension_lines and not self.wireframe:
            glDisable(GL_LIGHTING)
            glDisable(GL_DEPTH_TEST)

            # 1. Trục chiều cao tâm: (0, y, 0) -> (0, -y, 0)
            draw_dashed_line_3d((0.0, y, 0.0), (0.0, -y, 0.0), color=(1.0, 0.88, 0.15, 0.95), line_width=2.5)

            # 2. Đường gióng chiều dài trên mặt đáy: (0, -y, 0) -> (x, -y, 0)
            draw_dashed_line_3d((0.0, -y, 0.0), (x, -y, 0.0), color=(0.15, 0.95, 1.0, 0.95), line_width=2.2)

            # 3. Đường gióng chiều rộng trên mặt đáy: (0, -y, 0) -> (0, -y, z)
            draw_dashed_line_3d((0.0, -y, 0.0), (0.0, -y, z), color=(1.0, 0.62, 0.15, 0.95), line_width=2.2)

            # 4. Ký hiệu góc vuông tại tâm mặt đáy
            draw_right_angle_3d((0.0, -y, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), size=min(0.2, min(x, z) * 0.4))
            draw_right_angle_3d((0.0, -y, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), size=min(0.2, min(x, z) * 0.4))

            # 5. Các điểm mốc tâm đáy, tâm trên, tâm khối O
            draw_point_marker_3d((0.0, 0.0, 0.0), color=(1.0, 1.0, 1.0, 1.0), point_size=8.0)
            draw_point_marker_3d((0.0, -y, 0.0), color=(1.0, 0.88, 0.15, 1.0), point_size=8.0)
            draw_point_marker_3d((0.0, y, 0.0), color=(0.15, 0.95, 1.0, 1.0), point_size=7.5)

            glEnable(GL_DEPTH_TEST)
            glEnable(GL_LIGHTING)

    def draw_unfolded(self, progress: float):
        """Trải phẳng hình hộp chữ nhật thành hình chữ thập 6 mặt chữ nhật."""
        self.apply_material()
        x = (self.length_cm * self.scale_factor) / 2.0
        y = (self.height_cm * self.scale_factor) / 2.0
        z = (self.width_cm * self.scale_factor) / 2.0
        p = max(0.0, min(1.0, progress))
        fold_ang = 90.0 * (1.0 - p)

        def rect(w_half, d_half):
            glBegin(GL_LINE_LOOP if self.wireframe else GL_QUADS)
            glNormal3f(0.0, 1.0, 0.0)
            glVertex3f(-w_half, 0.0, -d_half)
            glVertex3f(w_half, 0.0, -d_half)
            glVertex3f(w_half, 0.0, d_half)
            glVertex3f(-w_half, 0.0, d_half)
            glEnd()
            if not self.wireframe:
                glDisable(GL_LIGHTING)
                glColor4f(0.0, 0.95, 1.0, 0.95)
                glLineWidth(2.0)
                glBegin(GL_LINE_LOOP)
                glVertex3f(-w_half, 0.0, -d_half)
                glVertex3f(w_half, 0.0, -d_half)
                glVertex3f(w_half, 0.0, d_half)
                glVertex3f(-w_half, 0.0, d_half)
                glEnd()
                self.apply_material()

        glPushMatrix()
        base_y = -y * (1.0 - p)
        glTranslatef(0.0, base_y, 0.0)
        rect(x, z)  # Mặt đáy cố định (2x * 2z)

        # 1. Mặt trước (+Z): kích thước 2x * 2y
        glPushMatrix()
        glTranslatef(0.0, 0.0, z)
        glRotatef(-fold_ang, 1.0, 0.0, 0.0)
        glTranslatef(0.0, 0.0, y)
        rect(x, y)
        glPopMatrix()

        # 2. Mặt sau (-Z): kích thước 2x * 2y và Mặt trên gắn vào mặt sau (2x * 2z)
        glPushMatrix()
        glTranslatef(0.0, 0.0, -z)
        glRotatef(fold_ang, 1.0, 0.0, 0.0)
        glTranslatef(0.0, 0.0, -y)
        rect(x, y)
        # Mặt trên gắn tiếp
        glPushMatrix()
        glTranslatef(0.0, 0.0, -y)
        glRotatef(fold_ang, 1.0, 0.0, 0.0)
        glTranslatef(0.0, 0.0, -z)
        rect(x, z)
        glPopMatrix()
        glPopMatrix()

        # 3. Mặt phải (+X): kích thước 2y * 2z
        glPushMatrix()
        glTranslatef(x, 0.0, 0.0)
        glRotatef(fold_ang, 0.0, 0.0, 1.0)
        glTranslatef(y, 0.0, 0.0)
        rect(y, z)
        glPopMatrix()

        # 4. Mặt trái (-X): kích thước 2y * 2z
        glPushMatrix()
        glTranslatef(-x, 0.0, 0.0)
        glRotatef(-fold_ang, 0.0, 0.0, 1.0)
        glTranslatef(-y, 0.0, 0.0)
        rect(y, z)
        glPopMatrix()

        glPopMatrix()

    def get_dimension_annotations(self):
        x = (self.length_cm * self.scale_factor) / 2.0
        y = (self.height_cm * self.scale_factor) / 2.0
        z = (self.width_cm * self.scale_factor) / 2.0
        return [
            ((x * 0.5, -y, 0.0), f"dài: {self.length_cm:.1f} cm", "#00f0ff"),
            ((0.0, -y, z * 0.5), f"rộng: {self.width_cm:.1f} cm", "#ff9900"),
            ((0.0, 0.0, 0.0), f"cao: {self.height_cm:.1f} cm", "#ffd700"),
            ((0.0, -y, 0.0), "O (Tâm đáy)", "#ffd700"),
        ]


class SphericalSectionGeometry(SphereGeometry):
    """Hình Cắt Cầu / Chỏm Cầu (Spherical Section)."""
    def draw(self):
        self.apply_material()
        r = self.radius_cm * self.scale_factor
        for i in range(self.stacks // 2):
            p0 = math.pi * i / (2 * self.stacks)
            p1 = math.pi * (i + 1) / (2 * self.stacks)
            glBegin(GL_QUAD_STRIP)
            for j in range(self.slices + 1):
                a = 2 * math.pi * j / self.slices
                for p in (p0, p1):
                    x = math.cos(p) * math.cos(a)
                    y = math.sin(p)
                    z = math.cos(p) * math.sin(a)
                    glNormal3f(x, y, z)
                    glVertex3f(r * x, r * y, r * z)
            glEnd()

        # Đường viền đáy mặt phẳng cắt tại Y = 0
        if not self.wireframe:
            glDisable(GL_LIGHTING)
            glColor4f(1.0, 0.85, 0.2, 0.9)
            glLineWidth(2.0)
            glBegin(GL_LINE_LOOP)
            for j in range(self.slices + 1):
                a = 2 * math.pi * j / self.slices
                glVertex3f(r * math.cos(a), 0.0, r * math.sin(a))
            glEnd()

            # Hệ thống nét đứt đo kích thước
            if self.show_dimension_lines:
                glDisable(GL_DEPTH_TEST)
                # Trục chiều cao từ tâm cắt lên đỉnh chỏm
                draw_dashed_line_3d((0.0, 0.0, 0.0), (0.0, r, 0.0), color=(1.0, 0.88, 0.15, 0.95), line_width=2.2)
                # Bán kính mặt cắt
                draw_dashed_line_3d((0.0, 0.0, 0.0), (r, 0.0, 0.0), color=(1.0, 0.62, 0.15, 0.95), line_width=2.5)
                # Ký hiệu góc vuông
                draw_right_angle_3d((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0), size=min(0.22, r * 0.28))
                # Điểm mốc
                draw_point_marker_3d((0.0, 0.0, 0.0), color=(1.0, 0.88, 0.15, 1.0), point_size=8.0)
                draw_point_marker_3d((0.0, r, 0.0), color=(1.0, 1.0, 1.0, 1.0), point_size=8.0)
                draw_point_marker_3d((r, 0.0, 0.0), color=(0.15, 0.95, 1.0, 1.0), point_size=7.5)
                glEnable(GL_DEPTH_TEST)

            glEnable(GL_LIGHTING)

    def get_dimension_annotations(self):
        r = self.radius_cm * self.scale_factor
        return [
            ((0.0, r, 0.0), "Đỉnh chỏm", "#ffffff"),
            ((0.0, -0.05, 0.0), "O (Tâm cắt)", "#ffd700"),
            ((r * 0.5, 0.12, 0.0), f"R = {self.radius_cm:.1f} cm", "#ff9900"),
            ((r, 0.0, 0.0), "A", "#00f0ff"),
        ]
