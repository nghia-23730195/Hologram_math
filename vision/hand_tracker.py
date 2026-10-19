# -*- coding: utf-8 -*-
"""
vision/hand_tracker.py
----------------------
Phân hệ thị giác máy tính & nhận diện cử chỉ bàn tay thông minh dùng MediaPipe.

Hỗ trợ các cử chỉ:
1. 👌 Pinch Xoay 3D (Ngón cái + Ngón trỏ): Xoay Yaw & Pitch mượt mà với Pinch Lock.
2. 👐 Zoom 2 Bàn tay (Two-Hand Zoom): Kéo 2 tay ra xa để phóng to, đưa lại gần để thu nhỏ.
3. 🤏 Zoom 1 Bàn tay (Ngón cái + Ngón giữa): Kéo tay lên/xuống để zoom khi dùng 1 tay.
4. 🖐️↔️ Lướt tay (Swipe Gesture): Vẫy tay sang trái/phải để chuyển khối hình học tiếp theo/trước đó.
5. ✊ Nắm tay (Fist Gesture): Nắm bàn tay để Bật/Tắt chế độ Tự động xoay 360° (Auto-rotate).
6. ✌️ Giơ 2 ngón tay (Peace/V-Sign): Đặt lại góc nhìn mặc định (Reset View).
7. 👍 Giơ ngón cái (Thumbs-Up): Bật / Tắt hoạt hình mở hộp trải phẳng 2D.
"""

import math
import time
import cv2
import numpy as np
import mediapipe as mp


def to_ascii_hud(text: str) -> str:
    """Chuyển đổi chuỗi tiếng Việt / emoji sang ASCII để cv2.putText không bao giờ hiển thị dấu chấm hỏi '?'."""
    if not text:
        return ""
    mapping = {
        'à': 'a', 'á': 'a', 'ả': 'a', 'ã': 'a', 'ạ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ẳ': 'a', 'ẵ': 'a', 'ặ': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ẩ': 'a', 'ẫ': 'a', 'ậ': 'a',
        'đ': 'd',
        'è': 'e', 'é': 'e', 'ẻ': 'e', 'ẽ': 'e', 'ẹ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ể': 'e', 'ễ': 'e', 'ệ': 'e',
        'ì': 'i', 'í': 'i', 'ỉ': 'i', 'ĩ': 'i', 'ị': 'i',
        'ò': 'o', 'ó': 'o', 'ỏ': 'o', 'õ': 'o', 'ọ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ổ': 'o', 'ỗ': 'o', 'ộ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ở': 'o', 'ỡ': 'o', 'ợ': 'o',
        'ù': 'u', 'ú': 'u', 'ủ': 'u', 'ũ': 'u', 'ụ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ử': 'u', 'ữ': 'u', 'ự': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỷ': 'y', 'ỹ': 'y', 'ỵ': 'y',
        'À': 'A', 'Á': 'A', 'Ả': 'A', 'Ã': 'A', 'Ạ': 'A',
        'Ă': 'A', 'Ằ': 'A', 'Ắ': 'A', 'Ẳ': 'A', 'Ẵ': 'A', 'Ặ': 'A',
        'Â': 'A', 'Ầ': 'A', 'Ấ': 'A', 'Ẩ': 'A', 'Ẫ': 'A', 'Ậ': 'A',
        'Đ': 'D',
        'È': 'E', 'É': 'E', 'Ẻ': 'E', 'Ẽ': 'E', 'Ẹ': 'E',
        'Ê': 'E', 'Ề': 'E', 'Ế': 'E', 'Ể': 'E', 'Ễ': 'E', 'Ệ': 'E',
        'Ì': 'I', 'Í': 'I', 'Ỉ': 'I', 'Ĩ': 'I', 'Ị': 'I',
        'Ò': 'O', 'Ó': 'O', 'Ỏ': 'O', 'Õ': 'O', 'Ọ': 'O',
        'Ô': 'O', 'Ồ': 'O', 'Ố': 'O', 'Ổ': 'O', 'Ỗ': 'O', 'Ộ': 'O',
        'Ơ': 'O', 'Ờ': 'O', 'Ớ': 'O', 'Ở': 'O', 'Ỡ': 'O', 'Ợ': 'O',
        'Ù': 'U', 'Ú': 'U', 'Ủ': 'U', 'Ũ': 'U', 'Ụ': 'U',
        'Ư': 'U', 'Ừ': 'U', 'Ứ': 'U', 'Ử': 'U', 'Ữ': 'U', 'Ự': 'U',
        'Ỳ': 'Y', 'Ý': 'Y', 'Ỷ': 'Y', 'Ỹ': 'Y', 'Ỵ': 'Y'
    }
    chars = []
    for ch in text:
        if ch in mapping:
            chars.append(mapping[ch])
        elif 32 <= ord(ch) <= 126:
            chars.append(ch)
    return "".join(chars).strip()


class HandTracker:
    """Bộ xử lý nhận diện bàn tay & phát hiện cử chỉ đa dạng (Rotate, Zoom, Swipe, Fist, V-sign)."""

    def __init__(self, pinch_threshold: float = 0.06, sensitivity: float = 250.0):
        try:
            self.mp_hands = mp.solutions.hands
            self.mp_drawing = mp.solutions.drawing_utils
            self.mp_drawing_styles = mp.solutions.drawing_styles
        except AttributeError:
            try:
                import mediapipe.python.solutions.hands as h
                import mediapipe.python.solutions.drawing_utils as du
                import mediapipe.python.solutions.drawing_styles as ds
                self.mp_hands = h
                self.mp_drawing = du
                self.mp_drawing_styles = ds
            except Exception as e:
                raise RuntimeError(
                    "Phiên bản MediaPipe hiện tại không hỗ trợ API solutions. Vui lòng chạy lệnh: pip install mediapipe==0.10.14"
                ) from e

        # Hỗ trợ tối đa 2 bàn tay để zoom 2 tay
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.65,
            min_tracking_confidence=0.65
        )

        # Ngưỡng phát hiện cử chỉ Chụm tay (Pinch)
        self.pinch_threshold = pinch_threshold
        self.pinch_start_threshold = 0.065   # Ngưỡng bắt đầu pinch (chặt chẽ)
        self.pinch_release_threshold = 0.095 # Ngưỡng thả pinch (Schmitt trigger chống rung giật)
        self.sensitivity = sensitivity

        # Trạng thái cử chỉ Xoay (Thumb + Index Finger)
        self.is_pinching = False
        self.last_pinch_pos = None

        # Trạng thái cử chỉ Zoom 1 tay (Thumb + Middle Finger)
        self.is_zoom_pinching = False
        self.last_zoom_pos = None

        # Smoothing filters
        self.smooth_alpha = 0.4
        self.current_delta_yaw = 0.0
        self.current_delta_pitch = 0.0
        self.current_delta_zoom = 0.0

        # --- CỬ CHỈ 2 TAY (Two-hand Zoom: Kéo xa để phóng to, lại gần để thu nhỏ) ---
        self.is_two_hand_active = False
        self.last_two_hand_dist = None
        self.two_hand_smooth_delta = 0.0
        self.two_hand_frame_count = 0
        self.two_hand_lost_frames = 0
        self.last_two_hand_time = 0.0

        # --- KHOẢNG ĐỆM CHUYỂN TIẾP CỬ CHỈ (Grace Periods để tránh kích hoạt nhầm) ---
        self.last_pinch_time = 0.0
        self.last_pointing_time = 0.0
        self.last_fist_time = 0.0
        self.last_active_gesture_time = 0.0   # Cập nhật khi có bất kỳ cử chỉ chủ động nào hoạt động
        self.gesture_grace_period = 0.25       # 0.25s sau khi buông cử chỉ khác sẽ khóa Swipe (nhạy hơn, không bị trễ)
        self.open_palm_start_time = None       # Thời điểm bắt đầu xòe bàn tay ổn định

        # --- CỬ CHỈ LƯỚT TAY (Swipe Gesture: Lướt dứt khoát để đổi hình) ---
        self.swipe_history = []  # Danh sách các điểm (timestamp, x)
        self.last_swipe_time = 0.0
        self.swipe_cooldown = 0.55             # 0.55s cooldown cho phép chuyển hình liên tục mượt mà
        self.swipe_min_velocity = 0.35         # Vận tốc lướt nhẹ nhàng (~35% chiều rộng/giây)
        self.swipe_min_distance = 0.10         # Khoảng cách lướt chỉ cần 10% chiều ngang màn hình (~64px)
        self.active_swipe_label = ""
        self.active_swipe_expire = 0.0

        # --- CỬ CHỈ NẮM TAY (Fist Gesture -> Toggle Auto-Rotate) ---
        self.fist_start_time = None
        self.last_fist_toggle_time = 0.0
        self.fist_hold_threshold = 0.35  # Cần giữ nắm tay 0.35s
        self.fist_cooldown = 1.3

        # --- CỬ CHỈ CHỮ V (Peace / V-sign -> Reset View) ---
        self.vsign_start_time = None
        self.last_vsign_time = 0.0
        self.vsign_hold_threshold = 0.35  # Cần giữ chữ V 0.35s
        self.vsign_cooldown = 1.3

        # --- CỬ CHỈ 3 NGÓN (Three-Finger -> Cycle Slice Mode) ---
        self.three_finger_start_time = None
        self.last_three_fingers_time = 0.0
        self.three_fingers_cooldown = 1.3

        # --- CỬ CHỈ GIƠ NGÓN CÁI (Thumbs Up 👍 -> Bật/Tắt Mở Hộp 2D) ---
        self.thumbs_up_start_time = None
        self.last_unfold_toggle_time = 0.0
        self.unfold_hold_threshold = 0.35  # Giữ ngón cái hướng lên 0.35s
        self.unfold_cooldown = 1.3         # Thời gian chờ giữa 2 lần bật/tắt (1.3s)

        # --- LÀM MƯỢT TỌA ĐỘ CON TRỎ 3D & MẶT CẮT ---
        self.pointer_alpha = 0.35
        self.smooth_pointer_pos = None
        self.smooth_slice_offset = 0.0
        self.two_hand_unfold_smooth = 0.0

    @staticmethod
    def _dist(p1, p2):
        """Tính khoảng cách Euclid giữa 2 điểm 2D."""
        return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

    def _is_finger_folded(self, tip, pip, wrist):
        """Kiểm tra ngón tay có đang gập vào lòng bàn tay (so sánh cự ly tới cổ tay)."""
        return self._dist(tip, wrist) < self._dist(pip, wrist) * 1.05

    def _is_finger_extended(self, tip, pip, wrist):
        """Kiểm tra ngón tay có đang duỗi thẳng."""
        return self._dist(tip, wrist) > self._dist(pip, wrist) * 1.2

    def _check_thumbs_up(self, lms):
        """
        Kiểm tra cử chỉ giơ ngón cái (Thumbs Up 👍):
        - 4 ngón chính (Trỏ, Giữa, Nhẫn, Út) đều gập lại sát lòng bàn tay.
        - Ngón cái (Thumb TIP) duỗi thẳng hướng lên trời:
          + Cao hơn khớp ngón cái (MCP & IP) và khớp gốc ngón trỏ (index_mcp).
          + Duỗi cách xa cổ tay.
          + Cách xa đầu ngón trỏ để không bị nhầm với Pinch.
        """
        wrist = lms.landmark[0]
        # 4 ngón chính (Trỏ, Giữa, Nhẫn, Út) đều phải gập
        f_index = self._is_finger_folded(lms.landmark[8], lms.landmark[6], wrist)
        f_middle = self._is_finger_folded(lms.landmark[12], lms.landmark[10], wrist)
        f_ring = self._is_finger_folded(lms.landmark[16], lms.landmark[14], wrist)
        f_pinky = self._is_finger_folded(lms.landmark[20], lms.landmark[18], wrist)
        if not (f_index and f_middle and f_ring and f_pinky):
            return False

        thumb_tip = lms.landmark[4]
        thumb_ip = lms.landmark[3]
        thumb_mcp = lms.landmark[2]
        index_mcp = lms.landmark[5]
        index_tip = lms.landmark[8]

        # Trong hệ tọa độ MediaPipe: trục Y hướng xuống dưới (0 ở trên đỉnh, 1 ở đáy)
        # Giơ ngón cái lên -> thumb_tip.y phải nhỏ hơn thumb_mcp.y và index_mcp.y
        pointing_up = (thumb_tip.y < thumb_mcp.y - 0.035) and (thumb_tip.y < index_mcp.y - 0.03) and (thumb_tip.y < thumb_ip.y)
        extended = self._dist(thumb_tip, wrist) > self._dist(thumb_mcp, wrist) * 1.15
        # Không được chụm với ngón trỏ (tránh nhầm Pinch)
        not_pinching = self._dist(thumb_tip, index_tip) > 0.08
        return pointing_up and extended and not_pinching

    def _check_fist(self, lms):
        """
        Kiểm tra bàn tay có đang nắm chặt (Fist ✊) hay không:
        - Bắt buộc CẢ 5 NGÓN đều phải gập!
        - 4 ngón chính (Trỏ, Giữa, Nhẫn, Út) gập sát lòng bàn tay.
        - Ngón cái (Thumb) gập ôm lấy ngón trỏ/giữa, tuyệt đối không được giơ lên cao hoặc duỗi xa ra ngoài.
        """
        wrist = lms.landmark[0]
        # 4 ngón chính (Trỏ, Giữa, Nhẫn, Út)
        f_index = self._is_finger_folded(lms.landmark[8], lms.landmark[6], wrist)
        f_middle = self._is_finger_folded(lms.landmark[12], lms.landmark[10], wrist)
        f_ring = self._is_finger_folded(lms.landmark[16], lms.landmark[14], wrist)
        f_pinky = self._is_finger_folded(lms.landmark[20], lms.landmark[18], wrist)
        if not (f_index and f_middle and f_ring and f_pinky):
            return False

        # Nếu đang là Thumbs Up thì tuyệt đối không phải Fist
        if self._check_thumbs_up(lms):
            return False

        thumb_tip = lms.landmark[4]
        thumb_ip = lms.landmark[3]

        # Trong nắm tay (Fist), ngón cái không được giơ lên trời (thumb_tip phải thấp hơn hoặc ngang thumb_ip)
        if thumb_tip.y < thumb_ip.y - 0.01:
            return False

        # Ngón cái phải gập ôm sát ngón trỏ/giữa hoặc lòng bàn tay
        close_to_fingers = (self._dist(thumb_tip, lms.landmark[6]) < 0.13) or \
                           (self._dist(thumb_tip, lms.landmark[10]) < 0.13) or \
                           (self._dist(thumb_tip, lms.landmark[5]) < 0.13)
        return close_to_fingers

    def _check_v_sign(self, lms):
        """Kiểm tra cử chỉ chữ V (Peace sign ✌️): Ngón trỏ & giữa giơ thẳng, 2 ngón kia gập, ngón cái gập."""
        wrist = lms.landmark[0]
        ext_index = self._is_finger_extended(lms.landmark[8], lms.landmark[6], wrist)
        ext_middle = self._is_finger_extended(lms.landmark[12], lms.landmark[10], wrist)
        fold_ring = self._is_finger_folded(lms.landmark[16], lms.landmark[14], wrist)
        fold_pinky = self._is_finger_folded(lms.landmark[20], lms.landmark[18], wrist)
        separated = self._dist(lms.landmark[8], lms.landmark[12]) > 0.035
        # Ngón cái không được duỗi tạo thành 3 ngón
        thumb_tip = lms.landmark[4]
        thumb_not_extended = self._dist(thumb_tip, wrist) < self._dist(lms.landmark[2], wrist) * 1.3
        return ext_index and ext_middle and fold_ring and fold_pinky and separated and thumb_not_extended

    def _check_pointing(self, lms):
        """
        Kiểm tra cử chỉ trỏ ngón tay (Air Pointer 👆):
        - Chỉ ngón trỏ duỗi thẳng, các ngón kia gập.
        - NGĂN CHẶN XUNG ĐỘT VỚI PINCH (XOAY 3D): 
          Đầu ngón cái PHẢI cách xa đầu ngón trỏ (> 0.11). Nếu ngón cái ở gần ngón trỏ thì là chuẩn bị xoay, không phải trỏ.
        """
        wrist = lms.landmark[0]
        ext_index = self._is_finger_extended(lms.landmark[8], lms.landmark[6], wrist)
        fold_middle = self._is_finger_folded(lms.landmark[12], lms.landmark[10], wrist)
        fold_ring = self._is_finger_folded(lms.landmark[16], lms.landmark[14], wrist)
        fold_pinky = self._is_finger_folded(lms.landmark[20], lms.landmark[18], wrist)
        if not (ext_index and fold_middle and fold_ring and fold_pinky):
            return False

        thumb_tip = lms.landmark[4]
        index_tip = lms.landmark[8]
        # Bắt buộc cự ly ngón cái và ngón trỏ phải tách xa (tránh nhầm với Pinch xoay)
        separated_from_thumb = self._dist(thumb_tip, index_tip) > 0.11
        return separated_from_thumb

    def _check_three_fingers(self, lms):
        """Kiểm tra cử chỉ 3 ngón tay: Ngón trỏ, giữa, nhẫn duỗi thẳng, ngón út gập."""
        wrist = lms.landmark[0]
        ext_index = self._is_finger_extended(lms.landmark[8], lms.landmark[6], wrist)
        ext_middle = self._is_finger_extended(lms.landmark[12], lms.landmark[10], wrist)
        ext_ring = self._is_finger_extended(lms.landmark[16], lms.landmark[14], wrist)
        fold_pinky = self._is_finger_folded(lms.landmark[20], lms.landmark[18], wrist)
        if not (ext_index and ext_middle and ext_ring and fold_pinky):
            return False
        # Ngón út tuyệt đối không được duỗi (tránh nhầm với xòe bàn tay 4 ngón)
        ext_pinky = self._is_finger_extended(lms.landmark[20], lms.landmark[18], wrist)
        return not ext_pinky

    def _check_open_palm(self, lms):
        """
        Kiểm tra bàn tay mở/xòe để nhận diện lướt tay (Swipe):
        - Cho phép ngón út hoặc áp út hơi cong tự nhiên khi vung tay nhanh / nhòe chuyển động.
        - Chấp nhận khi có từ 3 ngón tay duỗi trở lên, hoặc 2 ngón chính (trỏ + giữa) duỗi
          mà không gập chặt 2 ngón còn lại thành chữ V.
        """
        wrist = lms.landmark[0]
        ext_index = self._is_finger_extended(lms.landmark[8], lms.landmark[6], wrist)
        ext_middle = self._is_finger_extended(lms.landmark[12], lms.landmark[10], wrist)
        ext_ring = self._is_finger_extended(lms.landmark[16], lms.landmark[14], wrist)
        ext_pinky = self._is_finger_extended(lms.landmark[20], lms.landmark[18], wrist)
        extended_count = sum([ext_index, ext_middle, ext_ring, ext_pinky])

        # 1. Nếu có từ 3 ngón duỗi trở lên -> Chắc chắn là bàn tay mở
        if extended_count >= 3:
            return True

        # 2. Nếu 2 ngón duỗi (trỏ + giữa) nhưng ngón áp út/út không gập chặt vào lòng bàn tay (không phải chữ V)
        fold_ring = self._is_finger_folded(lms.landmark[16], lms.landmark[14], wrist)
        fold_pinky = self._is_finger_folded(lms.landmark[20], lms.landmark[18], wrist)
        if ext_index and ext_middle and not (fold_ring and fold_pinky):
            return True

        return False

    def process_frame(self, frame_bgr: np.ndarray):
        """
        Xử lý khung hình và nhận diện các cử chỉ.
        Trả về:
        - frame_bgr: Ảnh có vẽ chú thích cử chỉ.
        - gesture_data: Từ điển chứa các sự kiện cử chỉ.
        """
        now = time.time()
        h, w, _ = frame_bgr.shape
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        results = self.hands.process(frame_rgb)

        gesture_data = {
            'hand_detected': False,
            'num_hands': 0,
            'primary_gesture': 'none',
            'is_pinching': False,
            'is_zoom_pinching': False,
            'is_two_hand_zoom': False,
            'is_two_hand_unfold': False,
            'two_hand_unfold_progress': 0.0,
            'is_pointing': False,
            'pointer_pos': None,          # (norm_x, norm_y)
            'is_slicing_gesture': False,
            'slice_offset': 0.0,
            'cycle_slice_type': False,
            'swipe_direction': None,      # 'left', 'right', hoặc None
            'toggle_auto_rotate': False,
            'toggle_unfold': False,       # Sự kiện bật/tắt mở hộp 2D bằng xòe tay giữ yên
            'reset_view': False,
            'delta_yaw': 0.0,
            'delta_pitch': 0.0,
            'delta_zoom': 0.0,
            'pinch_distance': 0.0,
            'zoom_pinch_distance': 0.0,
            'gesture_name': "CHỜ CỬ CHỈ",
            'landmarks': None
        }

        num_hands = len(results.multi_hand_landmarks) if results.multi_hand_landmarks else 0
        raw_num_hands = num_hands
        gesture_data['num_hands'] = num_hands

        if num_hands > 0:
            gesture_data['hand_detected'] = True
            gesture_data['landmarks'] = results.multi_hand_landmarks[0]

            # Vẽ xương tay cho tất cả bàn tay phát hiện được
            for hand_lms in results.multi_hand_landmarks:
                self.mp_drawing.draw_landmarks(
                    frame_bgr,
                    hand_lms,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_drawing_styles.get_default_hand_landmarks_style(),
                    self.mp_drawing_styles.get_default_hand_connections_style()
                )

            # --- DEBOUNCE VÀ HYSTERESIS CHO 2 BÀN TAY (TRÁNH CHỚP HỤT FRAME) ---
            if raw_num_hands >= 2:
                self.two_hand_frame_count += 1
                self.two_hand_lost_frames = 0
            else:
                if self.is_two_hand_active:
                    self.two_hand_lost_frames += 1
                else:
                    self.two_hand_frame_count = 0

            # Kích hoạt khi có 2 frame liên tiếp phát hiện 2 tay
            # Duy trì nếu chỉ mất dấu tạm thời <= 3 frames khi đang active
            is_two_hand_mode = (self.two_hand_frame_count >= 2) and (
                raw_num_hands >= 2 or (self.is_two_hand_active and self.two_hand_lost_frames <= 3)
            )

            # =========================================================
            # TRƯỜNG HỢP A: NHẬN DIỆN 2 BÀN TAY -> CHỈ DÀNH RIÊNG CHO THU PHÓNG (ZOOM 3D)
            # Không bao giờ nhầm lẫn với Mở hộp 2D hay Xoay 3D!
            # =========================================================
            if is_two_hand_mode and raw_num_hands >= 2:
                self.last_two_hand_time = now
                self.last_active_gesture_time = now
                hand1 = results.multi_hand_landmarks[0]
                hand2 = results.multi_hand_landmarks[1]

                # Tâm 2 bàn tay (trung điểm cổ tay và gốc ngón giữa)
                c1_x = (hand1.landmark[0].x + hand1.landmark[9].x) / 2.0
                c1_y = (hand1.landmark[0].y + hand1.landmark[9].y) / 2.0
                c2_x = (hand2.landmark[0].x + hand2.landmark[9].x) / 2.0
                c2_y = (hand2.landmark[0].y + hand2.landmark[9].y) / 2.0

                p1_px = (int(c1_x * w), int(c1_y * h))
                p2_px = (int(c2_x * w), int(c2_y * h))

                current_dist = math.sqrt((c1_x - c2_x) ** 2 + (c1_y - c2_y) ** 2)

                # Vẽ tia laser kết nối màu Cyan / Neon giữa 2 bàn tay
                cv2.line(frame_bgr, p1_px, p2_px, (255, 230, 0), 3)
                cv2.circle(frame_bgr, p1_px, 12, (255, 255, 0), -1)
                cv2.circle(frame_bgr, p2_px, 12, (255, 255, 0), -1)

                mid_px = ((p1_px[0] + p2_px[0]) // 2, (p1_px[1] + p2_px[1]) // 2)
                cv2.circle(frame_bgr, mid_px, 8, (255, 255, 255), -1)

                if self.is_two_hand_active and self.last_two_hand_dist is not None:
                    diff_dist = current_dist - self.last_two_hand_dist
                    # Vùng chết (deadzone) để loại bỏ rung lắc tay nhẹ
                    if abs(diff_dist) > 0.005:
                        raw_delta = diff_dist * self.sensitivity * 1.5
                        self.two_hand_smooth_delta = (
                            self.smooth_alpha * raw_delta +
                            (1.0 - self.smooth_alpha) * self.two_hand_smooth_delta
                        )
                    else:
                        self.two_hand_smooth_delta = 0.0

                    gesture_data['delta_zoom'] = self.two_hand_smooth_delta
                    gesture_data['is_two_hand_zoom'] = True
                    gesture_data['primary_gesture'] = 'zoom_2hand'
                else:
                    self.is_two_hand_active = True
                    self.two_hand_smooth_delta = 0.0
                    gesture_data['primary_gesture'] = 'zoom_2hand'

                self.last_two_hand_dist = current_dist

                # Chế độ 2 tay CHỈ ZOOM, tuyệt đối không chạm vào Mở hộp 2D!
                gesture_data['is_two_hand_unfold'] = False
                gesture_data['two_hand_unfold_progress'] = 0.0

                sign = "+" if self.two_hand_smooth_delta >= 0 else ""
                gesture_data['gesture_name'] = f"🔍 ZOOM 2 TAY | Δ: {sign}{self.two_hand_smooth_delta:.2f}"
                cv2.putText(frame_bgr, to_ascii_hud(gesture_data['gesture_name']), (max(20, min(p1_px[0], p2_px[0]) - 30), max(30, min(p1_px[1], p2_px[1]) - 20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)

                # Reset các trạng thái 1 tay khi đang ở chế độ 2 tay
                self.is_pinching = False
                self.last_pinch_pos = None
                self.fist_start_time = None
                self.vsign_start_time = None
                self.three_finger_start_time = None
                self.thumbs_up_start_time = None
                self.open_palm_start_time = None
                self.smooth_pointer_pos = None

                return frame_bgr, gesture_data

            # Nếu đang ở chế độ 2 tay nhưng mất tạm thời 1-3 frames
            if is_two_hand_mode and self.is_two_hand_active and self.two_hand_lost_frames <= 3:
                gesture_data['primary_gesture'] = 'zoom_2hand'
                gesture_data['is_two_hand_zoom'] = True
                gesture_data['delta_zoom'] = 0.0
                gesture_data['gesture_name'] = "🔍 ZOOM 2 TAY (GIỮ TRẠNG THÁI)"
                return frame_bgr, gesture_data

            # =========================================================
            # TRƯỜNG HỢP B: XỬ LÝ 1 BÀN TAY (Single Hand)
            # =========================================================
            if self.is_two_hand_active:
                self.is_two_hand_active = False
                self.last_two_hand_dist = None
                self.two_hand_smooth_delta = 0.0
                self.last_two_hand_time = now

            # Khoảng đệm hạ tay: nếu vừa rời chế độ 2 tay trong vòng 0.60s,
            # bỏ qua tất cả cử chỉ 1 tay để tránh tay còn lại kích hoạt nhầm
            if now - self.last_two_hand_time < 0.60:
                self.is_pinching = False
                self.thumbs_up_start_time = None
                self.fist_start_time = None
                self.vsign_start_time = None
                self.open_palm_start_time = None
                self.swipe_history.clear()
                gesture_data['gesture_name'] = "✋ BÀN TAY (SẴN SÀNG)"
                gesture_data['primary_gesture'] = 'none'
                return frame_bgr, gesture_data

            hand_landmarks = results.multi_hand_landmarks[0]
            thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
            index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

            t_x, t_y = int(thumb_tip.x * w), int(thumb_tip.y * h)
            i_x, i_y = int(index_tip.x * w), int(index_tip.y * h)
            m_x, m_y = int(middle_tip.x * w), int(middle_tip.y * h)

            dist_rotate = self._dist(thumb_tip, index_tip)
            gesture_data['pinch_distance'] = dist_rotate
            is_fist_check = self._check_fist(hand_landmarks)
            is_thumbs_up_check = self._check_thumbs_up(hand_landmarks)

            # Schmitt Trigger / Hysteresis cho Pinch xoay 3D:
            # - Khi CHƯA pinch: cần chụm ngón tay sát < pinch_start_threshold (0.065)
            # - Khi ĐANG pinch: giữ trạng thái cho đến khi mở rộng ra >= pinch_release_threshold (0.095)
            curr_pinch_thresh = self.pinch_release_threshold if self.is_pinching else self.pinch_start_threshold
            rotate_active = (dist_rotate < curr_pinch_thresh) and (not is_fist_check) and (not is_thumbs_up_check)

            # Điểm trung tâm bàn tay
            wrist = hand_landmarks.landmark[0]
            middle_mcp = hand_landmarks.landmark[9]
            palm_x = (wrist.x + middle_mcp.x) / 2.0
            palm_y = (wrist.y + middle_mcp.y) / 2.0

            # --- CỬ CHỈ XOAY 3D (Ngón cái + ngón trỏ) ---
            if rotate_active:
                self.last_pinch_time = now
                self.last_active_gesture_time = now
                mid_rot_x = (thumb_tip.x + index_tip.x) / 2.0
                mid_rot_y = (thumb_tip.y + index_tip.y) / 2.0

                cv2.line(frame_bgr, (t_x, t_y), (i_x, i_y), (0, 255, 0), 4)
                cv2.circle(frame_bgr, (int(mid_rot_x * w), int(mid_rot_y * h)), 9, (0, 255, 0), -1)

                if not self.is_pinching:
                    self.last_pinch_pos = (mid_rot_x, mid_rot_y)
                    self.is_pinching = True
                else:
                    if self.last_pinch_pos is not None:
                        lx, ly = self.last_pinch_pos
                        diff_x = mid_rot_x - lx
                        diff_y = mid_rot_y - ly

                        raw_delta_yaw = diff_x * self.sensitivity
                        raw_delta_pitch = diff_y * self.sensitivity

                        self.current_delta_yaw = (
                            self.smooth_alpha * raw_delta_yaw +
                            (1 - self.smooth_alpha) * self.current_delta_yaw
                        )
                        self.current_delta_pitch = (
                            self.smooth_alpha * raw_delta_pitch +
                            (1 - self.smooth_alpha) * self.current_delta_pitch
                        )

                        gesture_data['delta_yaw'] = self.current_delta_yaw
                        gesture_data['delta_pitch'] = self.current_delta_pitch
                        self.last_pinch_pos = (mid_rot_x, mid_rot_y)

                gesture_data['is_pinching'] = True
                gesture_data['primary_gesture'] = 'pinch_rotate'
                gesture_data['gesture_name'] = "👌 XOAY 3D"
                self.smooth_pointer_pos = None
                self.thumbs_up_start_time = None
                self.open_palm_start_time = None
                self.swipe_history.clear()

            # --- CÁC CỬ CHỈ KHI KHÔNG PINCH (Fist, V-sign, Point, Open Palm, Thumbs Up) ---
            else:
                self.is_pinching = False
                self.last_pinch_pos = None

                # Vẽ chỉ thị thả tay (Pinch Lock)
                cv2.line(frame_bgr, (t_x, t_y), (i_x, i_y), (0, 0, 255), 2)

                is_pointing = self._check_pointing(hand_landmarks)
                is_three_fingers = self._check_three_fingers(hand_landmarks)
                is_thumbs_up = self._check_thumbs_up(hand_landmarks)
                is_fist = self._check_fist(hand_landmarks)
                is_vsign = self._check_v_sign(hand_landmarks)
                is_open_palm = self._check_open_palm(hand_landmarks)

                # Khoảng đệm chống kích hoạt nhầm sau khi kết thúc cử chỉ khác (0.65s)
                # Đảm bảo khi vừa xoay/chỉ/nắm xong buông tay không bị nhảy sang Swipe/Unfold
                in_grace_period = (now - self.last_active_gesture_time < self.gesture_grace_period)

                # A. KIỂM TRA CHỈ TAY (Air Pointer & Điều khiển Mặt cắt Air Slice)
                if is_pointing:
                    self.last_pointing_time = now
                    self.last_active_gesture_time = now
                    self.fist_start_time = None
                    self.vsign_start_time = None
                    self.thumbs_up_start_time = None
                    self.open_palm_start_time = None
                    self.swipe_history.clear()

                    target_x = float(index_tip.x)
                    target_y = float(index_tip.y)
                    if self.smooth_pointer_pos is None:
                        self.smooth_pointer_pos = (target_x, target_y)
                    else:
                        px, py = self.smooth_pointer_pos
                        self.smooth_pointer_pos = (
                            self.pointer_alpha * target_x + (1.0 - self.pointer_alpha) * px,
                            self.pointer_alpha * target_y + (1.0 - self.pointer_alpha) * py
                        )

                    # Ánh xạ target_y (0.15 -> 0.85) thành slice_offset (+1.0 -> -1.0)
                    raw_slice = 1.0 - 2.0 * ((target_y - 0.15) / 0.70)
                    raw_slice = max(-1.0, min(1.0, raw_slice))
                    self.smooth_slice_offset = 0.3 * raw_slice + 0.7 * self.smooth_slice_offset

                    gesture_data['is_pointing'] = True
                    gesture_data['primary_gesture'] = 'pointing'
                    gesture_data['pointer_pos'] = self.smooth_pointer_pos
                    gesture_data['is_slicing_gesture'] = True
                    gesture_data['slice_offset'] = round(float(self.smooth_slice_offset), 2)
                    gesture_data['gesture_name'] = "👆 CHỈ TAY / CẮT LÁT KHÔNG GIAN"

                    # Vẽ Cyberpunk Reticle quanh đầu ngón trỏ trên camera
                    pt_x = int(self.smooth_pointer_pos[0] * w)
                    pt_y = int(self.smooth_pointer_pos[1] * h)
                    cv2.circle(frame_bgr, (pt_x, pt_y), 18, (0, 255, 255), 2)
                    cv2.circle(frame_bgr, (pt_x, pt_y), 5, (0, 255, 255), -1)
                    cv2.line(frame_bgr, (pt_x - 26, pt_y), (pt_x + 26, pt_y), (0, 255, 255), 1)
                    cv2.line(frame_bgr, (pt_x, pt_y - 26), (pt_x, pt_y + 26), (0, 255, 255), 1)
                    cv2.putText(frame_bgr, f"AIR POINTER ({pt_x}, {pt_y})", (pt_x + 22, pt_y - 8),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
                    cv2.putText(frame_bgr, f"SLICE: {gesture_data['slice_offset']:+.2f}", (pt_x + 22, pt_y + 12),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (50, 255, 150), 2)

                # B. KIỂM TRA 3 NGÓN TAY (Cycle Slice Type: Ngang -> Trục -> Xiên)
                elif is_three_fingers:
                    self.last_active_gesture_time = now
                    self.fist_start_time = None
                    self.vsign_start_time = None
                    self.thumbs_up_start_time = None
                    self.open_palm_start_time = None
                    self.smooth_pointer_pos = None
                    self.swipe_history.clear()

                    if now - self.last_three_fingers_time >= self.three_fingers_cooldown:
                        gesture_data['cycle_slice_type'] = True
                        self.last_three_fingers_time = now
                        self.active_swipe_label = "🤟 3 NGÓN: ĐỔI MẶT CẮT (NGANG/TRỤC/XIÊN)"
                        self.active_swipe_expire = now + 1.5

                    gesture_data['primary_gesture'] = 'three_fingers'
                    gesture_data['gesture_name'] = "🤟 3 NGÓN (CHUYỂN MẶT CẮT)"
                    cv2.putText(frame_bgr, "3-FINGER: CYCLE SLICE", (10, 65),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 120, 255), 2)

                # C. KIỂM TRA GIƠ NGÓN CÁI (Thumbs Up 👍 -> Bật/Tắt Mở Hộp 2D)
                elif is_thumbs_up:
                    self.last_active_gesture_time = now
                    self.smooth_pointer_pos = None
                    self.fist_start_time = None
                    self.vsign_start_time = None
                    self.open_palm_start_time = None
                    self.swipe_history.clear()

                    if now - self.last_unfold_toggle_time < self.unfold_cooldown:
                        self.thumbs_up_start_time = None
                        gesture_data['gesture_name'] = "👍 NGÓN CÁI (CHỜ COOLDOWN)"
                        gesture_data['primary_gesture'] = 'thumbs_up'
                    elif self.thumbs_up_start_time is None:
                        self.thumbs_up_start_time = now
                        gesture_data['gesture_name'] = "👍 GIỮ NGÓN CÁI: ĐỂ MỞ HỘP 2D..."
                        gesture_data['primary_gesture'] = 'thumbs_up'
                    else:
                        hold_duration = now - self.thumbs_up_start_time
                        progress = min(1.0, max(0.0, hold_duration / max(0.01, self.unfold_hold_threshold)))
                        pct = int(progress * 100)

                        # Vẽ vòng tiến trình trực quan quanh đầu ngón cái trên camera preview
                        try:
                            t_x_px, t_y_px = int(thumb_tip.x * w), int(thumb_tip.y * h)
                            cv2.circle(frame_bgr, (t_x_px, t_y_px), 28, (50, 60, 70), 3)
                            angle = int(progress * 360)
                            if angle > 0:
                                cv2.ellipse(frame_bgr, (t_x_px, t_y_px), (28, 28), -90, 0, angle, (0, 255, 180), 4)
                            cv2.putText(frame_bgr, f"{pct}%", (t_x_px - 14, t_y_px - 8),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 180), 1)
                        except Exception:
                            pass

                        gesture_data['gesture_name'] = f"👍 GIỮ NGÓN CÁI ({pct}% -> MỞ HỘP 2D)"
                        gesture_data['primary_gesture'] = 'thumbs_up'

                        if hold_duration >= self.unfold_hold_threshold:
                            gesture_data['toggle_unfold'] = True
                            self.last_unfold_toggle_time = now
                            self.thumbs_up_start_time = None
                            self.active_swipe_label = "📦 ĐÃ BẬT/TẮT MỞ HỘP 2D"
                            self.active_swipe_expire = now + 1.5
                            gesture_data['gesture_name'] = "📦 ĐÃ MỞ HỘP 2D (THÀNH CÔNG)"

                # D. KIỂM TRA NẮM TAY (Fist -> Toggle Auto-Rotate)
                elif is_fist:
                    self.last_fist_time = now
                    self.last_active_gesture_time = now
                    self.smooth_pointer_pos = None
                    self.vsign_start_time = None
                    self.thumbs_up_start_time = None
                    self.open_palm_start_time = None
                    self.swipe_history.clear()
                    if self.fist_start_time is None:
                        self.fist_start_time = now
                    elif (now - self.fist_start_time >= self.fist_hold_threshold and
                          now - self.last_fist_toggle_time >= self.fist_cooldown):
                        gesture_data['toggle_auto_rotate'] = True
                        self.last_fist_toggle_time = now
                        self.fist_start_time = None
                        self.active_swipe_label = "✊ NẮM TAY: ĐỔI TRẠNG THÁI XOAY 360°"
                        self.active_swipe_expire = now + 1.5

                    gesture_data['primary_gesture'] = 'fist'
                    gesture_data['gesture_name'] = "✊ NẮM TAY (TỰ ĐỘNG XOAY)"
                    cv2.putText(frame_bgr, "FIST DETECTED", (10, 65),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 200, 255), 2)

                # E. KIỂM TRA CHỮ V (Peace / V-Sign -> Reset View)
                elif is_vsign:
                    self.last_active_gesture_time = now
                    self.smooth_pointer_pos = None
                    self.fist_start_time = None
                    self.thumbs_up_start_time = None
                    self.open_palm_start_time = None
                    self.swipe_history.clear()
                    if self.vsign_start_time is None:
                        self.vsign_start_time = now
                    elif (now - self.vsign_start_time >= self.vsign_hold_threshold and
                          now - self.last_vsign_time >= self.vsign_cooldown):
                        gesture_data['reset_view'] = True
                        self.last_vsign_time = now
                        self.vsign_start_time = None
                        self.active_swipe_label = "✌️ CHỮ V: ĐẶT LẠI GÓC NHÌN CHUẨN"
                        self.active_swipe_expire = now + 1.5

                    gesture_data['primary_gesture'] = 'v_sign'
                    gesture_data['gesture_name'] = "✌️ CHỮ V (RESET GÓC NHÌN)"
                    cv2.putText(frame_bgr, "V-SIGN: RESET VIEW", (10, 65),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 100), 2)

                # F. KIỂM TRA LƯỚT TAY (Swipe) HOẶC BÀN TAY XÒE TỰ DO
                elif is_open_palm:
                    self.smooth_pointer_pos = None
                    self.fist_start_time = None
                    self.vsign_start_time = None
                    self.thumbs_up_start_time = None

                    # Nếu đang trong khoảng đệm vừa buông tay xoay/chỉ/nắm (0.25s), khóa tạm thời Swipe
                    if in_grace_period:
                        self.swipe_history.clear()
                        self.open_palm_start_time = None
                        gesture_data['gesture_name'] = "✋ BÀN TAY (SẴN SÀNG)"
                        gesture_data['primary_gesture'] = 'open_palm'
                    else:
                        # Vùng theo dõi rộng rãi (0.05 <= palm_x <= 0.95 và palm_y <= 0.95)
                        in_tracking_zone = (0.05 <= palm_x <= 0.95) and (palm_y <= 0.95)
                        if in_tracking_zone:
                            # Ghi nhận tọa độ tức thì vào lịch sử trượt (cửa sổ trượt 0.45s)
                            self.swipe_history.append((now, palm_x))
                            self.swipe_history = [(t, px) for (t, px) in self.swipe_history if now - t <= 0.45]

                            swiped = False
                            # Kiểm tra lướt khi đã có tối thiểu 3 frame và hết thời gian cooldown
                            if len(self.swipe_history) >= 3 and (now - self.last_swipe_time >= self.swipe_cooldown):
                                # Duyệt tìm cặp điểm (t_prev, x_prev) trong lịch sử thỏa mãn điều kiện lướt
                                for t_prev, x_prev in self.swipe_history:
                                    dt = now - t_prev
                                    if dt < 0.06:
                                        continue
                                    dx = palm_x - x_prev
                                    if abs(dx) >= self.swipe_min_distance:
                                        velocity = dx / dt
                                        if abs(velocity) >= self.swipe_min_velocity:
                                            swiped = True
                                            if dx < -self.swipe_min_distance:
                                                gesture_data['swipe_direction'] = 'left'
                                                self.active_swipe_label = "⬅️ LƯỚT TRÁI: HÌNH TIẾP THEO"
                                            else:
                                                gesture_data['swipe_direction'] = 'right'
                                                self.active_swipe_label = "➡️ LƯỚT PHẢI: HÌNH TRƯỚC ĐÓ"

                                            self.last_swipe_time = now
                                            self.last_active_gesture_time = now
                                            self.active_swipe_expire = now + 1.5
                                            self.swipe_history.clear()
                                            self.open_palm_start_time = None
                                            gesture_data['primary_gesture'] = 'swipe'
                                            break

                            if not swiped:
                                gesture_data['gesture_name'] = "🖐️ BÀN TAY XÒE (LƯỚT TRÁI/PHẢI ĐỔI HÌNH)"
                                gesture_data['primary_gesture'] = 'open_palm'
                        else:
                            gesture_data['gesture_name'] = "🖐️ BÀN TAY (NGOÀI VÙNG LƯỚT)"
                            gesture_data['primary_gesture'] = 'open_palm'

                else:
                    self.smooth_pointer_pos = None
                    self.fist_start_time = None
                    self.vsign_start_time = None
                    self.thumbs_up_start_time = None
                    self.open_palm_start_time = None
                    gesture_data['gesture_name'] = "🖐️ BÀN TAY TỰ DO"
                    gesture_data['primary_gesture'] = 'none'

        else:
            # Không phát hiện bàn tay
            self.is_pinching = False
            self.last_pinch_pos = None
            self.is_zoom_pinching = False
            self.last_zoom_pos = None
            self.is_two_hand_active = False
            self.last_two_hand_dist = None
            self.two_hand_frame_count = 0
            self.two_hand_lost_frames = 0
            self.fist_start_time = None
            self.vsign_start_time = None
            self.thumbs_up_start_time = None
            self.open_palm_start_time = None
            self.swipe_history.clear()
            self.smooth_pointer_pos = None
            gesture_data['gesture_name'] = "CHƯA PHÁT HIỆN TAY"
            gesture_data['primary_gesture'] = 'none'

        # Hiển thị Banner cử chỉ lướt tay / sự kiện vừa kích hoạt
        if now < self.active_swipe_expire and self.active_swipe_label:
            banner_y = h - 55
            cv2.rectangle(frame_bgr, (10, banner_y - 25), (w - 10, banner_y + 12), (0, 0, 0), -1)
            cv2.rectangle(frame_bgr, (10, banner_y - 25), (w - 10, banner_y + 12), (0, 240, 255), 2)
            cv2.putText(frame_bgr, to_ascii_hud(self.active_swipe_label), (20, banner_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 240, 255), 2)

        # Hiển thị trạng thái cử chỉ góc trên bên trái
        status_color = (0, 255, 0) if gesture_data['is_pinching'] else ((255, 255, 0) if gesture_data['is_two_hand_zoom'] else (0, 220, 255))
        hud_gesture = to_ascii_hud(gesture_data['gesture_name'])
        cv2.putText(frame_bgr, f"GESTURE: {hud_gesture}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, status_color, 2)

        return frame_bgr, gesture_data

