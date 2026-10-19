# -*- coding: utf-8 -*-
"""
ui/control_panel.py
-------------------
Bảng điều khiển các thông số của ứng dụng 3D Hologram:
- Chọn loại hình học 3D.
- Nhập thông số thực tế tính bằng cm (chiều dài cạnh, bán kính, chiều cao).
- Tỷ lệ quy đổi (Scale factor).
- Màu sắc, độ trong suốt (Alpha slider), chế độ wireframe.
- Chọn chế độ hiển thị 1 View vs 4-View Pyramid Hologram Cross.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QComboBox,
    QDoubleSpinBox, QSlider, QCheckBox, QPushButton, QColorDialog, QRadioButton, QButtonGroup, QLineEdit, QFrame
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import pyqtSignal, Qt


class ControlPanelWidget(QWidget):
    """Bảng điều khiển thông số thiết lập Hologram."""

    shape_changed = pyqtSignal(str)
    dimension_changed = pyqtSignal(float, float)  # (size_cm, height_cm)
    scale_factor_changed = pyqtSignal(float)
    color_changed = pyqtSignal(float, float, float, float)  # (r, g, b, a)
    wireframe_changed = pyqtSignal(bool)
    dimension_lines_changed = pyqtSignal(bool)
    view_mode_changed = pyqtSignal(str)  # 'single' hoặc 'pyramid'
    auto_rotate_changed = pyqtSignal(bool)
    sensitivity_changed = pyqtSignal(float)
    camera_source_changed = pyqtSignal(object)
    formula_test_requested = pyqtSignal()
    slicing_toggled = pyqtSignal(bool)
    slice_type_changed = pyqtSignal(str)
    slice_offset_changed = pyqtSignal(float)
    unfold_progress_changed = pyqtSignal(float)
    unfold_animate_requested = pyqtSignal()
    mirror_toggled = pyqtSignal(bool)
    hologram_box_toggled = pyqtSignal(bool)
    fit_screen_requested = pyqtSignal()
    fill_screen_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_r = 0.0
        self.current_g = 0.9
        self.current_b = 1.0
        self.current_a = 0.95

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Apply modern, high-contrast Cyberpunk stylesheet with large readable typography
        self.setStyleSheet("""
            QWidget {
                background-color: #11141f;
                color: #e2e8f0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1.5px solid #283347;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 12px;
                padding-bottom: 8px;
                padding-left: 8px;
                padding-right: 8px;
                font-size: 14px;
                color: #00f0ff;
                background-color: #141824;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                background-color: #141824;
            }
            QLabel {
                font-size: 13px;
                color: #cbd5e1;
            }
            QComboBox, QDoubleSpinBox, QLineEdit {
                background-color: #1e2436;
                border: 1.5px solid #334155;
                border-radius: 6px;
                padding: 5px 10px;
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                min-height: 24px;
            }
            QComboBox:hover, QDoubleSpinBox:hover, QLineEdit:hover {
                border-color: #00e5ff;
            }
            QComboBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
                border: 1.5px solid #00f0ff;
                background-color: #222a3d;
            }
            QComboBox::drop-down {
                border: none;
                width: 22px;
            }
            QComboBox QAbstractItemView {
                background-color: #1e2436;
                border: 1.5px solid #00f0ff;
                selection-background-color: #0284c7;
                selection-color: #ffffff;
                color: #ffffff;
                font-size: 13px;
                padding: 4px;
            }
            QPushButton {
                background-color: #1e293b;
                border: 1.5px solid #334155;
                border-radius: 6px;
                padding: 7px 12px;
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #2e3b52;
                border-color: #00f0ff;
                color: #38bdf8;
            }
            QPushButton:pressed {
                background-color: #0284c7;
                color: #ffffff;
            }
            QSlider::groove:horizontal {
                height: 7px;
                background: #1e293b;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #00e5ff;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #ffffff;
                width: 18px;
                height: 18px;
                margin-top: -6px;
                margin-bottom: -6px;
                border-radius: 9px;
                border: 2px solid #0284c7;
            }
            QSlider::handle:horizontal:hover {
                background: #00f0ff;
                border: 2px solid #ffffff;
            }
            QCheckBox, QRadioButton {
                font-size: 13px;
                color: #f1f5f9;
                spacing: 8px;
                font-weight: 500;
            }
            QCheckBox::indicator, QRadioButton::indicator {
                width: 17px;
                height: 17px;
            }
            QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {
                border: 1.5px solid #475569;
                border-radius: 4px;
                background-color: #1e293b;
            }
            QRadioButton::indicator:unchecked {
                border-radius: 8px;
            }
            QCheckBox::indicator:checked, QRadioButton::indicator:checked {
                border: 1.5px solid #00f0ff;
                border-radius: 4px;
                background-color: #0284c7;
            }
            QRadioButton::indicator:checked {
                border-radius: 8px;
            }
        """)

        # -------------------------------------------------------------
        # 1. Chọn loại Hình học (3D Geometries)
        # -------------------------------------------------------------
        group_shape = QGroupBox("🔷 1. Chọn khối hình 3D")
        layout_shape = QVBoxLayout()
        layout_shape.setContentsMargins(8, 6, 8, 6)
        layout_shape.setSpacing(6)

        self.combo_shape = QComboBox()
        self.combo_shape.addItem("📦 Hình Lập Phương (Cube)", "cube")
        self.combo_shape.addItem("🔺 Hình Chóp (Pyramid)", "pyramid")
        self.combo_shape.addItem("⚽ Khối Cầu (Sphere)", "sphere")
        self.combo_shape.addItem("🛢️ Hình Trụ (Cylinder)", "cylinder")
        self.combo_shape.addItem("🍩 Hình Xuyến (Torus)", "torus")
        self.combo_shape.addItem("🔻 Hình Nón (Cone)", "cone")
        self.combo_shape.addItem("▣ Hình Hộp Chữ Nhật", "rectangular_prism")
        self.combo_shape.addItem("◐ Hình Cắt Cầu", "spherical_section")
        self.combo_shape.currentIndexChanged.connect(self._on_shape_changed)
        layout_shape.addWidget(self.combo_shape)

        # Hàng nút chuyển hình nhanh (song song với cử chỉ lướt tay)
        h_shape_nav = QHBoxLayout()
        h_shape_nav.setSpacing(6)
        self.btn_prev_shape = QPushButton("◀ Trước (Lướt Phải)")
        self.btn_prev_shape.setStyleSheet("font-size: 12px; font-weight: bold; padding: 6px 10px; background-color: #1a2234; border: 1.5px solid #2d3d5a; color: #7dd3fc;")
        self.btn_prev_shape.clicked.connect(self.prev_shape)
        self.btn_next_shape = QPushButton("Sau (Lướt Trái) ▶")
        self.btn_next_shape.setStyleSheet("font-size: 12px; font-weight: bold; padding: 6px 10px; background-color: #1a2234; border: 1.5px solid #2d3d5a; color: #7dd3fc;")
        self.btn_next_shape.clicked.connect(self.next_shape)
        h_shape_nav.addWidget(self.btn_prev_shape)
        h_shape_nav.addWidget(self.btn_next_shape)
        layout_shape.addLayout(h_shape_nav)

        group_shape.setLayout(layout_shape)
        layout.addWidget(group_shape)

        # -------------------------------------------------------------
        # 2. Thông số kích thước thực tế (cm)
        # -------------------------------------------------------------
        group_dim = QGroupBox("📏 2. Thông số kích thước thực tế (cm)")
        layout_dim = QVBoxLayout()
        layout_dim.setContentsMargins(8, 6, 8, 6)
        layout_dim.setSpacing(6)

        # Cạnh / Bán kính (cm)
        h_size = QHBoxLayout()
        self.lbl_size = QLabel("Cạnh / Bán kính:")
        self.lbl_size.setStyleSheet("font-weight: bold;")
        self.spin_size = QDoubleSpinBox()
        self.spin_size.setRange(1.0, 50.0)
        self.spin_size.setValue(10.0)
        self.spin_size.setSingleStep(0.5)
        self.spin_size.setSuffix(" cm")
        self.spin_size.setMinimumHeight(32)
        self.spin_size.valueChanged.connect(self._on_dimension_changed)
        h_size.addWidget(self.lbl_size)
        h_size.addWidget(self.spin_size)
        layout_dim.addLayout(h_size)

        # Chiều cao (cm) (dành cho Chóp, Trụ, Nón, Hộp)
        h_height = QHBoxLayout()
        self.lbl_height = QLabel("Chiều cao:")
        self.lbl_height.setStyleSheet("font-weight: bold;")
        self.spin_height = QDoubleSpinBox()
        self.spin_height.setRange(1.0, 50.0)
        self.spin_height.setValue(12.0)
        self.spin_height.setSingleStep(0.5)
        self.spin_height.setSuffix(" cm")
        self.spin_height.setMinimumHeight(32)
        self.spin_height.valueChanged.connect(self._on_dimension_changed)
        h_height.addWidget(self.lbl_height)
        h_height.addWidget(self.spin_height)
        layout_dim.addLayout(h_height)

        # Tỷ lệ quy đổi Scale (1 cm = N units)
        h_scale = QHBoxLayout()
        lbl_scale_title = QLabel("Tỷ lệ Scale (cm ➜ 3D):")
        lbl_scale_title.setStyleSheet("font-weight: bold;")
        h_scale.addWidget(lbl_scale_title)
        self.slider_scale = QSlider(Qt.Orientation.Horizontal)
        self.slider_scale.setRange(5, 100)  # 0.05 đến 1.00 (phóng to tới 5x)
        self.slider_scale.setValue(20)       # Mặc định 0.20
        self.slider_scale.valueChanged.connect(self._on_scale_slider_changed)
        self.lbl_scale_val = QLabel("0.20")
        self.lbl_scale_val.setStyleSheet("font-weight: bold; color: #00f0ff; min-width: 38px; font-size: 13px;")
        h_scale.addWidget(self.slider_scale)
        h_scale.addWidget(self.lbl_scale_val)
        layout_dim.addLayout(h_scale)

        # Các nút thao tác nhanh: Vừa màn hình & Tràn màn hình 100%
        h_zoom_btns = QHBoxLayout()
        self.btn_fit_screen = QPushButton("⛶ Vừa màn hình (Fit)")
        self.btn_fit_screen.setToolTip("Căn chỉnh kích thước vừa vặn màn hình (Phím tắt: F)")
        self.btn_fit_screen.setStyleSheet("""
            QPushButton {
                background-color: #0f2b3e; border: 1.5px solid #00f0ff; color: #00f0ff;
                font-size: 12px; font-weight: bold; padding: 6px 10px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #0284c7; color: #ffffff; }
        """)
        self.btn_fit_screen.clicked.connect(self.fit_screen_requested.emit)

        self.btn_fill_screen = QPushButton("🔲 Tràn màn hình (Fill 100%)")
        self.btn_fill_screen.setToolTip("Phóng to cực đại tràn toàn bộ màn hình 16:9 (Phím tắt: Shift+F)")
        self.btn_fill_screen.setStyleSheet("""
            QPushButton {
                background-color: #1a2a1a; border: 1.5px solid #22c55e; color: #4ade80;
                font-size: 12px; font-weight: bold; padding: 6px 10px; border-radius: 6px;
            }
            QPushButton:hover { background-color: #16a34a; color: #ffffff; }
        """)
        self.btn_fill_screen.clicked.connect(self.fill_screen_requested.emit)

        h_zoom_btns.addWidget(self.btn_fit_screen)
        h_zoom_btns.addWidget(self.btn_fill_screen)
        layout_dim.addLayout(h_zoom_btns)

        group_dim.setLayout(layout_dim)
        layout.addWidget(group_dim)

        # -------------------------------------------------------------
        # 3. Màu sắc & Độ trong suốt (Material & Transparency)
        # -------------------------------------------------------------
        group_mat = QGroupBox("🎨 3. Màu sắc & Độ trong suốt (Alpha)")
        layout_mat = QVBoxLayout()
        layout_mat.setContentsMargins(8, 6, 8, 6)
        layout_mat.setSpacing(6)

        # Nút chọn màu Custom
        h_color = QHBoxLayout()
        self.btn_color_picker = QPushButton("🎨 Chọn Màu Tùy Chỉnh (Picker)")
        self.btn_color_picker.setStyleSheet("font-size: 13px; font-weight: bold; padding: 7px 12px;")
        self.btn_color_picker.clicked.connect(self._open_color_dialog)
        
        self.lbl_color_swatch = QLabel()
        self.lbl_color_swatch.setFixedSize(36, 28)
        self.lbl_color_swatch.setStyleSheet("background-color: #00e5ff; border-radius: 6px; border: 2px solid #ffffff;")
        
        h_color.addWidget(self.btn_color_picker)
        h_color.addWidget(self.lbl_color_swatch)
        layout_mat.addLayout(h_color)

        # Bảng màu Preset Hologram Nổi bật
        lbl_preset = QLabel("Bảng màu Hologram đặc trưng:")
        lbl_preset.setStyleSheet("font-weight: bold; color: #94a3b8; font-size: 12px; margin-top: 2px;")
        layout_mat.addWidget(lbl_preset)
        
        h_presets = QHBoxLayout()
        h_presets.setSpacing(6)
        presets = [
            ("Cyan", "#00f0ff", (0.0, 0.94, 1.0)),
            ("Neon Green", "#00ff66", (0.0, 1.0, 0.4)),
            ("Gold", "#ffcc00", (1.0, 0.8, 0.0)),
            ("Magenta", "#ff007f", (1.0, 0.0, 0.5)),
            ("Ice Blue", "#70b5ff", (0.44, 0.71, 1.0)),
            ("White", "#ffffff", (1.0, 1.0, 1.0))
        ]
        for name, hex_code, (r, g, b) in presets:
            btn_p = QPushButton()
            btn_p.setToolTip(name)
            btn_p.setStyleSheet(f"background-color: {hex_code}; border-radius: 6px; border: 1.5px solid #475569; min-width: 36px; max-width: 46px; min-height: 26px;")
            btn_p.clicked.connect(lambda checked, red=r, green=g, blue=b, hx=hex_code: self._set_preset_color(red, green, blue, hx))
            h_presets.addWidget(btn_p)
        layout_mat.addLayout(h_presets)

        # Alpha Transparency Slider
        h_alpha = QHBoxLayout()
        lbl_alpha_title = QLabel("Độ trong suốt (Alpha):")
        lbl_alpha_title.setStyleSheet("font-weight: bold;")
        h_alpha.addWidget(lbl_alpha_title)
        self.slider_alpha = QSlider(Qt.Orientation.Horizontal)
        self.slider_alpha.setRange(10, 100)
        self.slider_alpha.setValue(95)
        self.slider_alpha.valueChanged.connect(self._on_alpha_changed)
        self.lbl_alpha_val = QLabel("95%")
        self.lbl_alpha_val.setStyleSheet("font-weight: bold; color: #00f0ff; min-width: 38px; font-size: 13px;")
        h_alpha.addWidget(self.slider_alpha)
        h_alpha.addWidget(self.lbl_alpha_val)
        layout_mat.addLayout(h_alpha)

        # Wireframe Checkbox
        self.chk_wireframe = QCheckBox("Chế độ Khung dây (Wireframe)")
        self.chk_wireframe.setStyleSheet("font-weight: bold;")
        self.chk_wireframe.toggled.connect(self.wireframe_changed.emit)
        layout_mat.addWidget(self.chk_wireframe)

        group_mat.setLayout(layout_mat)
        layout.addWidget(group_mat)

        # -------------------------------------------------------------
        # 4. Chế độ hiển thị Hologram & Tự động xoay
        # -------------------------------------------------------------
        group_view = QGroupBox("🖥️ 4. Định dạng Hiển thị Hologram")
        layout_view = QVBoxLayout()
        layout_view.setContentsMargins(8, 6, 8, 6)
        layout_view.setSpacing(6)

        self.btn_group_view = QButtonGroup(self)
        self.radio_4view = QRadioButton("✨ 4-View Pyramid (Hologram 4 mặt)")
        self.radio_4view.setChecked(True)
        self.radio_single = QRadioButton("👁️ Single View (Xem thử 1 góc nhìn)")
        
        self.btn_group_view.addButton(self.radio_4view, 1)
        self.btn_group_view.addButton(self.radio_single, 2)
        self.btn_group_view.idToggled.connect(self._on_view_mode_toggled)

        layout_view.addWidget(self.radio_4view)
        layout_view.addWidget(self.radio_single)

        # Auto rotate
        self.chk_auto_rotate = QCheckBox("🔄 Tự động xoay 360°")
        self.chk_auto_rotate.setStyleSheet("font-weight: bold;")
        self.chk_auto_rotate.toggled.connect(self.auto_rotate_changed.emit)
        layout_view.addWidget(self.chk_auto_rotate)

        # Dimension Lines
        self.chk_dimension_lines = QCheckBox("📏 Nét đứt kích thước (h, R, a...)")
        self.chk_dimension_lines.setChecked(True)
        self.chk_dimension_lines.setStyleSheet("font-weight: bold;")
        self.chk_dimension_lines.toggled.connect(self.dimension_lines_changed.emit)
        layout_view.addWidget(self.chk_dimension_lines)

        # Chế độ Chiếu Hộp Hologram & Lật gương kính 45°
        self.chk_mirror = QCheckBox("🪞 Lật gương chiếu hộp (Kính 45° - Phím M)")
        self.chk_mirror.setStyleSheet("font-weight: bold; color: #a5b4fc;")
        self.chk_mirror.toggled.connect(self.mirror_toggled.emit)
        layout_view.addWidget(self.chk_mirror)

        self.chk_box_mode = QCheckBox("📦 Chế độ Hộp Hologram (Nền đen tuyền - Phím H)")
        self.chk_box_mode.setStyleSheet("font-weight: bold; color: #38bdf8;")
        self.chk_box_mode.toggled.connect(self.hologram_box_toggled.emit)
        layout_view.addWidget(self.chk_box_mode)

        # Hand Gesture Sensitivity
        h_sens = QHBoxLayout()
        lbl_sens_title = QLabel("Độ nhạy cử chỉ tay:")
        lbl_sens_title.setStyleSheet("font-weight: bold;")
        h_sens.addWidget(lbl_sens_title)
        self.slider_sens = QSlider(Qt.Orientation.Horizontal)
        self.slider_sens.setRange(100, 500)
        self.slider_sens.setValue(250)
        self.slider_sens.valueChanged.connect(lambda v: self.sensitivity_changed.emit(float(v)))
        h_sens.addWidget(self.slider_sens)
        layout_view.addLayout(h_sens)

        group_view.setLayout(layout_view)
        layout.addWidget(group_view)

        # -------------------------------------------------------------
        # 5. Công cụ Sư phạm Toán học 3D (Mặt cắt & Trải phẳng)
        # -------------------------------------------------------------
        group_pedagogy = QGroupBox("📐 5. Công cụ Sư phạm 3D")
        layout_pedagogy = QVBoxLayout()
        layout_pedagogy.setContentsMargins(8, 8, 8, 8)
        layout_pedagogy.setSpacing(6)

        # Phần A: Mặt cắt không gian (Slicing Plane)
        lbl_slice_title = QLabel("✂️ MẶT CẮT KHÔNG GIAN 3D:")
        lbl_slice_title.setStyleSheet("color: #ffd700; font-weight: bold; font-size: 13px; margin-bottom: 2px;")
        layout_pedagogy.addWidget(lbl_slice_title)

        self.chk_slicing = QCheckBox("Kích hoạt Mặt phẳng Cắt 3D")
        self.chk_slicing.setStyleSheet("font-weight: bold;")
        self.chk_slicing.toggled.connect(self._on_slicing_toggled)
        layout_pedagogy.addWidget(self.chk_slicing)

        h_slice_type = QHBoxLayout()
        lbl_st = QLabel("Kiểu cắt:")
        lbl_st.setStyleSheet("font-weight: bold;")
        h_slice_type.addWidget(lbl_st)
        self.combo_slice_type = QComboBox()
        self.combo_slice_type.addItem("Mặt cắt ngang (Trục Y)", "horizontal")
        self.combo_slice_type.addItem("Cắt dọc qua trục (Trục Z)", "axial")
        self.combo_slice_type.addItem("Cắt xiên nghiêng 45°", "oblique")
        self.combo_slice_type.currentIndexChanged.connect(self._on_slice_type_changed)
        h_slice_type.addWidget(self.combo_slice_type)
        layout_pedagogy.addLayout(h_slice_type)

        h_slice_offset = QHBoxLayout()
        lbl_so = QLabel("Vị trí cắt:")
        lbl_so.setStyleSheet("font-weight: bold;")
        h_slice_offset.addWidget(lbl_so)
        self.slider_slice_offset = QSlider(Qt.Orientation.Horizontal)
        self.slider_slice_offset.setRange(-100, 100)
        self.slider_slice_offset.setValue(0)
        self.slider_slice_offset.valueChanged.connect(self._on_slice_offset_changed)
        self.lbl_slice_offset_val = QLabel("0.00")
        self.lbl_slice_offset_val.setStyleSheet("font-weight: bold; color: #ffd700; min-width: 42px; font-size: 13px;")
        h_slice_offset.addWidget(self.slider_slice_offset)
        h_slice_offset.addWidget(self.lbl_slice_offset_val)
        layout_pedagogy.addLayout(h_slice_offset)

        lbl_slice_tip = QLabel("💡 <i>Cử chỉ AI:</i> <b>👆 Chỉ tay</b> lên/xuống để cắt lát & <b>🤟 3 ngón</b> đổi mặt cắt")
        lbl_slice_tip.setStyleSheet("color: #a3e635; font-size: 11px; margin-top: 1px; margin-bottom: 2px;")
        lbl_slice_tip.setWordWrap(True)
        layout_pedagogy.addWidget(lbl_slice_tip)

        # Đường kẻ phân cách nhẹ
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a354a; margin: 4px 0;")
        layout_pedagogy.addWidget(sep)

        # Phần B: Hoạt hình trải phẳng (Unfolding Net Animation)
        lbl_unfold_title = QLabel("📦 HOẠT HÌNH TRẢI PHẲNG 2D:")
        lbl_unfold_title.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 13px; margin-bottom: 2px;")
        layout_pedagogy.addWidget(lbl_unfold_title)

        h_unfold_ctrl = QHBoxLayout()
        self.btn_unfold_play = QPushButton("▶ Chạy Hoạt hình Trải phẳng")
        self.btn_unfold_play.setStyleSheet(
            "background-color: #0c4a6e; border: 1.5px solid #0284c7; color: #38bdf8; font-weight: bold; font-size: 13px; padding: 7px 12px; border-radius: 6px;"
        )
        self.btn_unfold_play.clicked.connect(self._on_unfold_animate_clicked)
        h_unfold_ctrl.addWidget(self.btn_unfold_play)
        layout_pedagogy.addLayout(h_unfold_ctrl)

        h_unfold_slider = QHBoxLayout()
        lbl_prog = QLabel("Tiến độ:")
        lbl_prog.setStyleSheet("font-weight: bold;")
        h_unfold_slider.addWidget(lbl_prog)
        self.slider_unfold = QSlider(Qt.Orientation.Horizontal)
        self.slider_unfold.setRange(0, 100)
        self.slider_unfold.setValue(0)
        self.slider_unfold.valueChanged.connect(self._on_unfold_slider_changed)
        self.lbl_unfold_val = QLabel("0%")
        self.lbl_unfold_val.setStyleSheet("font-weight: bold; color: #38bdf8; min-width: 42px; font-size: 13px;")
        h_unfold_slider.addWidget(self.slider_unfold)
        h_unfold_slider.addWidget(self.lbl_unfold_val)
        layout_pedagogy.addLayout(h_unfold_slider)

        # 3 Nút đặt độ mở 2D theo ý muốn (0%, 50%, 100%)
        h_presets_unfold = QHBoxLayout()
        h_presets_unfold.setSpacing(4)
        
        btn_u0 = QPushButton("Đóng lại (0%)")
        btn_u0.setStyleSheet("font-size: 11px; padding: 4px; background-color: #1e293b; border: 1px solid #475569; color: #cbd5e1; border-radius: 4px;")
        btn_u0.clicked.connect(lambda: self.slider_unfold.setValue(0))
        
        btn_u50 = QPushButton("Mở 50%")
        btn_u50.setStyleSheet("font-size: 11px; padding: 4px; background-color: #1e293b; border: 1px solid #0284c7; color: #38bdf8; border-radius: 4px;")
        btn_u50.clicked.connect(lambda: self.slider_unfold.setValue(50))
        
        btn_u100 = QPushButton("Trải phẳng (100%)")
        btn_u100.setStyleSheet("font-size: 11px; padding: 4px; background-color: #0c4a6e; border: 1px solid #00f0ff; color: #e0f2fe; font-weight: bold; border-radius: 4px;")
        btn_u100.clicked.connect(lambda: self.slider_unfold.setValue(100))
        
        h_presets_unfold.addWidget(btn_u0)
        h_presets_unfold.addWidget(btn_u50)
        h_presets_unfold.addWidget(btn_u100)
        layout_pedagogy.addLayout(h_presets_unfold)

        lbl_unfold_tip = QLabel("💡 <i>Cử chỉ AI:</i> <b>👍 Giơ ngón cái (0.35s)</b> | Phím <b>U / Space</b> để Bật/Tạm dừng mở hộp")
        lbl_unfold_tip.setStyleSheet("color: #7dd3fc; font-size: 11px; margin-top: 2px;")
        lbl_unfold_tip.setWordWrap(True)
        layout_pedagogy.addWidget(lbl_unfold_tip)

        group_pedagogy.setLayout(layout_pedagogy)
        layout.addWidget(group_pedagogy)

        # -------------------------------------------------------------
        # 6. Cấu hình Camera & DroidCam / IP Stream
        # -------------------------------------------------------------
        group_cam = QGroupBox("📱 6. Thấu kính Camera & DroidCam")
        layout_cam = QVBoxLayout()
        layout_cam.setContentsMargins(8, 6, 8, 6)
        layout_cam.setSpacing(6)

        self.combo_camera = QComboBox()
        self.combo_camera.addItem("📷 Camera 0 (Laptop/USB Webcam)", 0)
        self.combo_camera.addItem("📱 DroidCam / Phone IP Camera", "droidcam")
        self.combo_camera.addItem("✨ Mô phỏng Cử chỉ Bàn tay (Virtual Demo)", -1)
        self.combo_camera.addItem("📷 Camera 1", 1)
        self.combo_camera.addItem("📷 Camera 2", 2)
        self.combo_camera.currentIndexChanged.connect(self._on_camera_source_changed)
        layout_cam.addWidget(self.combo_camera)

        # DroidCam IP URL Input Widget Group (Ẩn mặc định khi dùng Camera 0)
        self.widget_droidcam_input = QWidget()
        self.widget_droidcam_input.setVisible(False)
        layout_droid = QVBoxLayout(self.widget_droidcam_input)
        layout_droid.setContentsMargins(0, 4, 0, 0)
        layout_droid.setSpacing(4)

        lbl_url = QLabel("Đường dẫn DroidCam / IP Stream URL:")
        lbl_url.setStyleSheet("font-size: 12px; font-weight: bold; color: #00e5ff;")
        layout_droid.addWidget(lbl_url)

        self.edit_droidcam_url = QLineEdit()
        self.edit_droidcam_url.setText("http://192.168.1.28:4747/video")
        self.edit_droidcam_url.setPlaceholderText("http://192.168.1.28:4747/video")
        self.edit_droidcam_url.setStyleSheet("background-color: #1e2436; border: 1.5px solid #00e5ff; border-radius: 6px; padding: 5px 8px; color: #ffffff;")
        layout_droid.addWidget(self.edit_droidcam_url)

        h_btn_droid = QHBoxLayout()
        h_btn_droid.setSpacing(6)
        self.btn_connect_droidcam = QPushButton("🔌 Kết nối DroidCam")
        self.btn_connect_droidcam.setStyleSheet("background-color: #0284c7; color: #ffffff; font-weight: bold; padding: 6px 10px;")
        self.btn_connect_droidcam.clicked.connect(self._on_connect_droidcam_clicked)
        
        self.btn_preset_wifi = QPushButton("WiFi (.28)")
        self.btn_preset_wifi.setStyleSheet("font-size: 11px; padding: 5px;")
        self.btn_preset_wifi.clicked.connect(lambda: self.edit_droidcam_url.setText("http://192.168.1.28:4747/video"))

        self.btn_preset_local = QPushButton("Local (127.0.0.1)")
        self.btn_preset_local.setStyleSheet("font-size: 11px; padding: 5px;")
        self.btn_preset_local.clicked.connect(lambda: self.edit_droidcam_url.setText("http://127.0.0.1:4747/mjpegfeed"))

        h_btn_droid.addWidget(self.btn_connect_droidcam)
        h_btn_droid.addWidget(self.btn_preset_wifi)
        h_btn_droid.addWidget(self.btn_preset_local)
        layout_droid.addLayout(h_btn_droid)

        layout_cam.addWidget(self.widget_droidcam_input)

        self.lbl_hint = QLabel("💡 Mẹo: Mở App DroidCam trên điện thoại & PC, nhập IP rồi bấm 'Kết nối'.")
        self.lbl_hint.setWordWrap(True)
        self.lbl_hint.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.lbl_hint.setVisible(False)
        layout_cam.addWidget(self.lbl_hint)

        group_cam.setLayout(layout_cam)
        layout.addWidget(group_cam)

        # -------------------------------------------------------------
        # 7. Kiểm tra công thức toán học
        # -------------------------------------------------------------
        group_test = QGroupBox("🧮 7. Kiểm tra công thức toán học")
        test_layout = QVBoxLayout()
        test_layout.setContentsMargins(8, 8, 8, 8)
        test_layout.setSpacing(6)
        self.btn_formula_test = QPushButton("✨ Mở Kiểm Thử Diện Tích & Thể Tích")
        self.btn_formula_test.setMinimumHeight(38)
        self.btn_formula_test.setStyleSheet(
            "background-color: #164e63; border: 1.5px solid #00f0ff; color: #38bdf8; font-weight: bold; font-size: 13px; border-radius: 6px;"
        )
        self.btn_formula_test.clicked.connect(self.formula_test_requested.emit)
        test_layout.addWidget(self.btn_formula_test)
        group_test.setLayout(test_layout)
        layout.addWidget(group_test)

        layout.addStretch()

    def _on_shape_changed(self, index: int):
        shape_key = self.combo_shape.currentData()
        self.shape_changed.emit(shape_key)

    def next_shape(self) -> str:
        """Chuyển sang hình học tiếp theo (vòng tròn)."""
        idx = (self.combo_shape.currentIndex() + 1) % self.combo_shape.count()
        self.combo_shape.setCurrentIndex(idx)
        return self.combo_shape.currentText()

    def prev_shape(self) -> str:
        """Quay lại hình học trước đó (vòng tròn)."""
        idx = (self.combo_shape.currentIndex() - 1) % self.combo_shape.count()
        self.combo_shape.setCurrentIndex(idx)
        return self.combo_shape.currentText()

    def toggle_auto_rotate(self) -> bool:
        """Đảo trạng thái checkbox tự động xoay."""
        new_state = not self.chk_auto_rotate.isChecked()
        self.chk_auto_rotate.setChecked(new_state)
        return new_state

    def _on_dimension_changed(self):
        size = self.spin_size.value()
        height = self.spin_height.value()
        self.dimension_changed.emit(size, height)

    def _on_scale_slider_changed(self, value: int):
        factor = value / 100.0
        self.lbl_scale_val.setText(f"{factor:.2f}")
        self.scale_factor_changed.emit(factor)

    def _open_color_dialog(self):
        initial_color = QColor(int(self.current_r * 255), int(self.current_g * 255), int(self.current_b * 255))
        color = QColorDialog.getColor(initial_color, self, "Chọn màu vật thể Hologram")
        if color.isValid():
            self.current_r = color.redF()
            self.current_g = color.greenF()
            self.current_b = color.blueF()
            self.lbl_color_swatch.setStyleSheet(f"background-color: {color.name()}; border-radius: 4px; border: 1px solid #fff;")
            self.color_changed.emit(self.current_r, self.current_g, self.current_b, self.current_a)

    def _set_preset_color(self, r: float, g: float, b: float, hex_code: str):
        self.current_r = r
        self.current_g = g
        self.current_b = b
        self.lbl_color_swatch.setStyleSheet(f"background-color: {hex_code}; border-radius: 4px; border: 1px solid #fff;")
        self.color_changed.emit(self.current_r, self.current_g, self.current_b, self.current_a)

    def _on_alpha_changed(self, value: int):
        self.current_a = value / 100.0
        self.lbl_alpha_val.setText(f"{value}%")
        self.color_changed.emit(self.current_r, self.current_g, self.current_b, self.current_a)


    def _on_view_mode_toggled(self, id_val: int, checked: bool):
        if checked:
            mode = 'pyramid' if id_val == 1 else 'single'
            self.view_mode_changed.emit(mode)

    def _on_camera_source_changed(self, index: int):
        data = self.combo_camera.currentData()
        is_droid = (data == "droidcam")
        self.widget_droidcam_input.setVisible(is_droid)
        if hasattr(self, 'lbl_hint'):
            self.lbl_hint.setVisible(is_droid)
        if is_droid:
            url = self.edit_droidcam_url.text().strip()
            if url:
                self.camera_source_changed.emit(url)
        else:
            self.camera_source_changed.emit(data)

    def _on_connect_droidcam_clicked(self):
        url = self.edit_droidcam_url.text().strip()
        if url:
            self.camera_source_changed.emit(url)

    def _on_slicing_toggled(self, checked: bool):
        if checked and self.slider_unfold.value() > 0:
            self.slider_unfold.setValue(0)
        self.slicing_toggled.emit(checked)

    def _on_slice_type_changed(self, index: int):
        stype = self.combo_slice_type.currentData()
        self.slice_type_changed.emit(stype)

    def _on_slice_offset_changed(self, value: int):
        val = value / 100.0
        self.lbl_slice_offset_val.setText(f"{val:+.2f}")
        self.slice_offset_changed.emit(val)

    def _on_unfold_animate_clicked(self):
        self.unfold_animate_requested.emit()

    def _on_unfold_slider_changed(self, value: int):
        val = value / 100.0
        self.lbl_unfold_val.setText(f"{value}%")
        if value > 0 and self.chk_slicing.isChecked():
            self.chk_slicing.setChecked(False)
        self.unfold_progress_changed.emit(val)
