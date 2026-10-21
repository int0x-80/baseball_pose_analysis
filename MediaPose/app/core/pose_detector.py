"""
MediaPipe Pose 和 Hand 检测核心模块
使用 MediaPipe Tasks API
"""
import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, List, Tuple
from dataclasses import dataclass, field
from .config import settings
from pathlib import Path

# MediaPipe BlazePose 标准关键点索引（33 个点）
POSE_LANDMARKS = {
    "nose": 0,
    "left_eye": 1,
    "right_eye": 2,
    "left_ear": 3,
    "right_ear": 4,
    "left_shoulder": 5,
    "right_shoulder": 6,
    "left_elbow": 7,
    "right_elbow": 8,
    "left_wrist": 9,
    "right_wrist": 10,
    "left_pinky": 17,
    "right_pinky": 18,
    "left_index": 19,
    "right_index": 20,
    "left_thumb": 21,
    "right_thumb": 22,
    "left_hip": 23,
    "right_hip": 24,
    "left_knee": 25,
    "right_knee": 26,
    "left_ankle": 27,
    "right_ankle": 28,
    "left_heel": 29,
    "right_heel": 30,
    "left_foot_index": 31,
    "right_foot_index": 32,
}

HAND_LANDMARKS = {
    "wrist": 0,
    "thumb_cmc": 1,
    "thumb_mcp": 2,
    "thumb_ip": 3,
    "thumb_tip": 4,
    "index_mcp": 5,
    "index_pip": 6,
    "index_dip": 7,
    "index_tip": 8,
    "middle_mcp": 9,
    "middle_pip": 10,
    "middle_dip": 11,
    "middle_tip": 12,
    "ring_mcp": 13,
    "ring_pip": 14,
    "ring_dip": 15,
    "ring_tip": 16,
    "pinky_mcp": 17,
    "pinky_pip": 18,
    "pinky_dip": 19,
    "pinky_tip": 20,
}

# Pose 连接（用于绘制），对齐 MediaPipe BlazePose 标准
POSE_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),  # 面部
    (5, 6),  # 肩线
    (5, 7), (7, 9), (6, 8), (8, 10),  # 上肢（肩-肘-腕）
    (9, 17), (9, 19), (9, 21), (10, 18), (10, 20), (10, 22),  # 手指（腕-pinky/index/thumb）
    (5, 23), (6, 24), (23, 24),  # 躯干（肩-髋 + 髋线）
    (23, 25), (25, 27), (24, 26), (26, 28),  # 下肢（髋-膝-踝）
    (27, 29), (29, 31), (28, 30), (30, 32),  # 脚（踝-跟-脚尖）
]

# Hand 连接
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),  # 拇指
    (0, 5), (5, 6), (6, 7), (7, 8),  # 食指
    (0, 9), (9, 10), (10, 11), (11, 12),  # 中指
    (0, 13), (13, 14), (14, 15), (15, 16),  # 无名指
    (0, 17), (17, 18), (18, 19), (19, 20),  # 小指
]

# 阶段 → 骨架颜色 (BGR)
PHASE_COLORS = {
    'STANCE': (255, 255, 255),
    'LOAD': (255, 150, 0),
    'STRIDE': (0, 255, 100),
    'SWING': (0, 50, 255),
    'CONTACT': (0, 255, 255),
    'FOLLOW_THROUGH': (255, 200, 0),
}

# 阶段中英文标签
PHASE_LABELS = {
    'STANCE': ('STANCE', '准备站姿'),
    'LOAD': ('LOAD', '蓄力回拉'),
    'STRIDE': ('STRIDE', '跨步转体'),
    'SWING': ('SWING', '挥棒加速'),
    'CONTACT': ('CONTACT', '击球瞬间'),
    'FOLLOW_THROUGH': ('FOLLOW', '随挥收棒'),
}

# 骨架连接（标准 MediaPipe 索引，用于绘制）
SKELETON_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),  # 上肢
    (11, 23), (12, 24), (23, 24),                        # 躯干
    (23, 25), (25, 27), (24, 26), (26, 28),              # 下肢
    (27, 29), (29, 31), (28, 30), (30, 32),              # 脚
]


@dataclass
class DetectionResult:
    """检测结果"""
    pose_landmarks: Optional[np.ndarray]  # (33, 3) normalized - [x, y, z]
    world_landmarks: Optional[np.ndarray]  # (33, 3) meters - [x, y, z]
    left_hand_landmarks: Optional[np.ndarray]  # (21, 3)
    right_hand_landmarks: Optional[np.ndarray]  # (21, 3)
    left_hand_handedness: Optional[str]
    right_hand_handedness: Optional[str]
    timestamp: float


class PoseDetector:
    """MediaPipe Pose 和 Hand 检测器"""

    def __init__(self):
        self.mp_image = mp.Image

        pose_model_path = self._get_pose_model_path()
        hand_model_path = self._get_hand_model_path()

        # Pose 检测器
        base_options = mp.tasks.BaseOptions(model_asset_path=pose_model_path)
        pose_options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=base_options,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.pose_detector = mp.tasks.vision.PoseLandmarker.create_from_options(pose_options)

        # Hand 检测器
        base_options_hand = mp.tasks.BaseOptions(model_asset_path=hand_model_path)
        hand_options = mp.tasks.vision.HandLandmarkerOptions(
            base_options=base_options_hand,
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_hands=2,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.hand_detector = mp.tasks.vision.HandLandmarker.create_from_options(hand_options)

    def _get_pose_model_path(self) -> str:
        model_dir = settings.TEMP_DIR / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / "pose_landmarker_lite.task"
        if not model_path.exists():
            import urllib.request
            import ssl
            print("下载 Pose 模型...")
            url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            urllib.request.urlretrieve(url, model_path)
            print("Pose 模型下载完成")
        return str(model_path)

    def _get_hand_model_path(self) -> str:
        model_dir = settings.TEMP_DIR / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / "hand_landmarker.task"
        if not model_path.exists():
            import urllib.request
            import ssl
            print("下载 Hand 模型...")
            url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            urllib.request.urlretrieve(url, model_path)
            print("Hand 模型下载完成")
        return str(model_path)

    def detect_frame(self, frame: np.ndarray, timestamp: float = 0.0) -> DetectionResult:
        """检测单帧的姿态和手部"""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = self.mp_image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        # Pose 检测
        pose_landmarks = None
        world_landmarks = None
        pose_result = self.pose_detector.detect_for_video(mp_image, int(timestamp * 1000))

        if pose_result.pose_landmarks:
            pose_landmarks = self._extract_pose_landmarks(pose_result.pose_landmarks[0])

        # 提取 world_landmarks（米制 3D 坐标，髋部中心为原点）
        if hasattr(pose_result, 'pose_world_landmarks') and pose_result.pose_world_landmarks:
            world_landmarks = self._extract_world_landmarks(pose_result.pose_world_landmarks[0])

        # Hand 检测
        left_hand_landmarks = None
        right_hand_landmarks = None
        left_hand_handedness = None
        right_hand_handedness = None

        hand_result = self.hand_detector.detect_for_video(mp_image, int(timestamp * 1000))

        if hand_result.hand_landmarks:
            for i, landmarks in enumerate(hand_result.hand_landmarks):
                handedness = hand_result.handedness[i][0].display_name.lower()
                landmarks_array = self._extract_hand_landmarks(landmarks)
                if handedness == "left":
                    left_hand_landmarks = landmarks_array
                    left_hand_handedness = "left"
                else:
                    right_hand_landmarks = landmarks_array
                    right_hand_handedness = "right"

        return DetectionResult(
            pose_landmarks=pose_landmarks,
            world_landmarks=world_landmarks,
            left_hand_landmarks=left_hand_landmarks,
            right_hand_landmarks=right_hand_landmarks,
            left_hand_handedness=left_hand_handedness,
            right_hand_handedness=right_hand_handedness,
            timestamp=timestamp
        )

    def _extract_pose_landmarks(self, pose_landmarks) -> np.ndarray:
        """提取 33 个 Pose 关键点（归一化坐标）"""
        landmarks = np.zeros((33, 3))
        for i, lm in enumerate(pose_landmarks):
            landmarks[i] = [lm.x, lm.y, lm.z]
        return landmarks

    def _extract_world_landmarks(self, world_landmarks) -> np.ndarray:
        """提取 33 个 World 关键点（米制坐标，髋部中心为原点）"""
        landmarks = np.zeros((33, 3))
        for i, lm in enumerate(world_landmarks):
            landmarks[i] = [lm.x, lm.y, lm.z]
        return landmarks

    def _extract_hand_landmarks(self, hand_landmarks) -> np.ndarray:
        """提取 21 个 Hand 关键点"""
        landmarks = np.zeros((21, 3))
        for i, lm in enumerate(hand_landmarks):
            landmarks[i] = [lm.x, lm.y, lm.z]
        return landmarks

    def draw_landmarks(self, frame: np.ndarray, result: DetectionResult, trajectory_points: list = None) -> np.ndarray:
        """在帧上绘制简化标记（兼容旧版调用）"""
        annotated_frame = frame.copy()
        height, width = frame.shape[:2]

        if result.pose_landmarks is not None:
            nose = result.pose_landmarks[0][:2]
            if nose[0] > 0 and nose[1] > 0:
                cv2.circle(annotated_frame, (int(nose[0] * width), int(nose[1] * height)), 8, (0, 255, 255), -1)

            for idx in [9, 10]:
                if idx < len(result.pose_landmarks):
                    x, y = result.pose_landmarks[idx][:2]
                    if x > 0 and y > 0:
                        cv2.circle(annotated_frame, (int(x * width), int(y * height)), 5, (0, 255, 0), -1)

            left_hip = result.pose_landmarks[23][:2]
            right_hip = result.pose_landmarks[24][:2]
            if left_hip[0] > 0 and left_hip[1] > 0 and right_hip[0] > 0 and right_hip[1] > 0:
                center_x = (left_hip[0] + right_hip[0]) / 2
                center_y = (left_hip[1] + right_hip[1]) / 2
                cv2.circle(annotated_frame, (int(center_x * width), int(center_y * height)), 5, (0, 0, 255), -1)

        if trajectory_points and len(trajectory_points) > 1:
            for i in range(1, len(trajectory_points)):
                pt1 = trajectory_points[i - 1]
                pt2 = trajectory_points[i]
                alpha = i / len(trajectory_points)
                color = (int(255 * (1 - alpha)), int(100 * alpha), int(255 * alpha))
                thickness = max(1, int(3 * alpha))
                cv2.line(
                    annotated_frame,
                    (int(pt1[0] * width), int(pt1[1] * height)),
                    (int(pt2[0] * width), int(pt2[1] * height)),
                    color, thickness
                )
            start_pt = trajectory_points[0]
            cv2.circle(annotated_frame, (int(start_pt[0] * width), int(start_pt[1] * height)), 8, (0, 255, 0), -1)
            end_pt = trajectory_points[-1]
            cv2.circle(annotated_frame, (int(end_pt[0] * width), int(end_pt[1] * height)), 8, (0, 0, 255), -1)

        return annotated_frame

    def draw_phase_aware(
        self,
        frame: np.ndarray,
        result: DetectionResult,
        phase: Optional[str] = None,
        bat_trajectory: List[dict] = None,
        frame_idx: int = 0,
        total_frames: int = 0,
        fps: int = 30,
        show_trajectory: bool = False,
    ) -> np.ndarray:
        """
        阶段感知绘制：骨架 + 阶段标注 + 棒头轨迹（仅标准挥棒帧）+ 速度叠加

        Args:
            frame: 原始 BGR 帧
            result: 检测结果
            phase: 当前阶段名称 (SwingPhase.value)
            bat_trajectory: 棒头轨迹数据列表
            frame_idx: 当前帧号
            total_frames: 总帧数
            fps: 帧率
            show_trajectory: 当前帧是否显示轨迹（由挥棒周期验证决定）
        """
        h, w = frame.shape[:2]
        annotated = frame.copy()
        color = PHASE_COLORS.get(phase, (255, 255, 255)) if phase else (255, 255, 255)

        # 1. 绘制骨架
        if result.pose_landmarks is not None:
            self._draw_phase_skeleton(annotated, result.pose_landmarks, color, w, h)

        # 2. 仅标准挥棒帧绘制扇形轨迹 + 速度
        if show_trajectory and bat_trajectory and frame_idx < len(bat_trajectory):
            self._draw_bat_trajectory(annotated, bat_trajectory, frame_idx, w, h)
            speed = bat_trajectory[frame_idx].get('bat_tip_speed_kmh', 0)
            if speed > 1:
                cv2.putText(annotated, f"Bat: {speed:.0f} km/h",
                            (w - 280, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

        # 3. 阶段标签
        if phase:
            self._draw_phase_banner(annotated, phase, color)

        # 4. 帧号
        if total_frames > 0:
            cv2.putText(annotated, f"Frame {frame_idx}/{total_frames}",
                        (w - 220, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

        return annotated

    def _draw_phase_skeleton(
        self, frame: np.ndarray, landmarks: np.ndarray,
        color: tuple, w: int, h: int,
    ):
        """绘制阶段着色的骨架（仅身体关节，头部只用鼻子单点）"""
        for s, e in SKELETON_CONNECTIONS:
            if s < len(landmarks) and e < len(landmarks):
                p1 = (int(landmarks[s][0] * w), int(landmarks[s][1] * h))
                p2 = (int(landmarks[e][0] * w), int(landmarks[e][1] * h))
                if 0 < p1[0] < w and 0 < p1[1] < h and 0 < p2[0] < w and 0 < p2[1] < h:
                    cv2.line(frame, p1, p2, color, 2)

        # 只绘制身体关节点（11-16 上肢, 23-28 下肢, 29-32 脚），跳过面部(0-10)和手指(17-22)
        body_joints = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
        big_joints = {11, 12, 23, 24}  # 肩髋用大圆
        for i in body_joints:
            if i < len(landmarks):
                x, y = int(landmarks[i][0] * w), int(landmarks[i][1] * h)
                if 0 < x < w and 0 < y < h:
                    r = 6 if i in big_joints else 4
                    cv2.circle(frame, (x, y), r, color, -1)

        # 头部 - 仅鼻子一个黄色大点
        nose = landmarks[0][:2]
        if nose[0] > 0 and nose[1] > 0:
            cv2.circle(frame, (int(nose[0] * w), int(nose[1] * h)), 8, (0, 255, 255), -1)

    def _draw_bat_trajectory(
        self, frame: np.ndarray, trajectory: List[dict],
        current_idx: int, w: int, h: int,
    ):
        """绘制棒头扇形轨迹 + 当前棒体（精简版，减少视觉干扰）"""
        trail_len = 30  # 与 ±15 帧窗口匹配
        start = max(0, current_idx - trail_len)
        end = min(current_idx + 1, len(trajectory))

        if end - start < 3:
            # 帧太少，只画当前棒体
            if current_idx < len(trajectory):
                t = trajectory[current_idx]
                wp = (int(t['wrist_x'] * w), int(t['wrist_y'] * h))
                tp = (int(t['bat_tip_x'] * w), int(t['bat_tip_y'] * h))
                cv2.line(frame, wp, tp, (255, 255, 255), 3)
                cv2.circle(frame, tp, 6, (0, 0, 255), -1)
            return

        # 收集可见窗口内的棒头像素坐标
        tips = []
        speeds = []
        for i in range(start, end):
            t = trajectory[i]
            tips.append((int(t['bat_tip_x'] * w), int(t['bat_tip_y'] * h)))
            speeds.append(t.get('bat_tip_speed_kmh', 0))

        # 旋转中心 = 当前手腕位置
        if current_idx < len(trajectory):
            ct = trajectory[current_idx]
            pivot = (int(ct['wrist_x'] * w), int(ct['wrist_y'] * h))
        else:
            pivot = tips[-1]

        # ===== 1. 扇形填充（半透明）=====
        overlay = frame.copy()

        # 下采样保持多边形平滑
        step = max(1, len(tips) // 40)
        sampled = tips[::step]
        if tips[-1] not in sampled:
            sampled.append(tips[-1])

        # 多边形: pivot → 旧棒头 → ... → 新棒头 → pivot
        fan_pts = [pivot] + sampled + [pivot]
        fan_arr = np.array(fan_pts, dtype=np.int32).reshape((-1, 1, 2))

        # 整体速度决定扇形色调（更鲜艳）
        avg_speed = np.mean(speeds) if speeds else 0
        if avg_speed > 60:
            fill_color = (0, 0, 255)       # 纯红
        elif avg_speed > 30:
            fill_color = (0, 140, 255)     # 亮橙
        else:
            fill_color = (0, 220, 255)     # 金黄

        cv2.fillPoly(overlay, [fan_arr], fill_color)
        cv2.addWeighted(overlay, 0.50, frame, 0.50, 0, frame)

        # ===== 2. 当前帧棒体 =====
        if current_idx < len(trajectory):
            t = trajectory[current_idx]
            wp = (int(t['wrist_x'] * w), int(t['wrist_y'] * h))
            tp = (int(t['bat_tip_x'] * w), int(t['bat_tip_y'] * h))
            cv2.line(frame, wp, tp, (255, 255, 255), 3)
            cv2.circle(frame, tp, 7, (0, 0, 255), -1)

    def _draw_phase_banner(self, frame: np.ndarray, phase: str, color: tuple):
        """绘制阶段标签横幅"""
        en, cn = PHASE_LABELS.get(phase, (phase, ''))
        text = f"{en} {cn}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        (tw, th), _ = cv2.getTextSize(text, font, 0.8, 2)
        padding = 10
        overlay = frame.copy()
        cv2.rectangle(overlay, (5, 5), (tw + padding * 2 + 5, th + padding * 2 + 5),
                      (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        cv2.putText(frame, text, (padding + 5, th + padding + 5),
                    font, 0.8, color, 2)

    def process_video(
        self, video_path: str, output_path: Optional[str] = None
    ) -> Tuple[List[DetectionResult], int, list]:
        """处理整个视频，返回检测结果、FPS和挥棒轨迹点（旧版接口）"""
        import subprocess
        import os

        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        results = []
        trajectory_points = []

        temp_video = None
        if output_path:
            temp_video = output_path + ".tmp.avi"
            fourcc = cv2.VideoWriter_fourcc(*'MJPG')
            video_writer = cv2.VideoWriter(temp_video, fourcc, fps, (frame_width, frame_height))
        else:
            video_writer = None

        frame_idx = 0
        swing_trajectory = []

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            timestamp = frame_idx / fps
            result = self.detect_frame(frame, timestamp)
            results.append(result)

            wrist_pos = None
            if result.right_hand_landmarks is not None:
                wrist_pos = result.right_hand_landmarks[0][:2]
            elif result.left_hand_landmarks is not None:
                wrist_pos = result.left_hand_landmarks[0][:2]
            if wrist_pos is None or wrist_pos[0] <= 0 or wrist_pos[1] <= 0:
                if result.pose_landmarks is not None:
                    wrist_idx = 10 if result.pose_landmarks[10][0] > 0 else 9
                    if wrist_idx < len(result.pose_landmarks):
                        wrist_pos = result.pose_landmarks[wrist_idx][:2]
            if wrist_pos is not None and wrist_pos[0] > 0 and wrist_pos[1] > 0:
                swing_trajectory.append(wrist_pos.copy())
                if len(swing_trajectory) > 30:
                    swing_trajectory.pop(0)

            if video_writer:
                annotated = self.draw_landmarks(frame, result, swing_trajectory.copy())
                video_writer.write(annotated)

            frame_idx += 1
            if frame_idx % 30 == 0:
                print(f"处理进度: {frame_idx}/{frame_count} ({frame_idx/frame_count*100:.1f}%)")

        cap.release()
        if video_writer:
            video_writer.release()

        if output_path and temp_video:
            print(f"正在转换视频格式...")
            try:
                subprocess.run([
                    'ffmpeg', '-y', '-i', temp_video,
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                    output_path
                ], check=True, capture_output=True)
                os.remove(temp_video)
                print(f"视频转换完成: {output_path}")
            except subprocess.CalledProcessError as e:
                print(f"FFmpeg 转换失败: {e.stderr.decode()}")
                os.rename(temp_video, output_path.replace('.mp4', '.avi'))

        return results, fps, swing_trajectory

    def process_video_phase_aware(
        self,
        video_path: str,
        output_path: str,
        phase_labels: list,
        bat_trajectory: List[dict] = None,
        trajectory_valid_frames: set = None,
    ) -> None:
        """
        第二遍处理：读取视频帧，绘制阶段感知的骨架 + 轨迹标注

        Args:
            video_path: 原始视频路径
            output_path: 输出骨架视频路径
            phase_labels: 逐帧阶段标签列表 (SwingPhase 或 str)
            bat_trajectory: 棒头轨迹数据列表
            trajectory_valid_frames: 允许显示轨迹的帧号集合（仅标准挥棒的 SWING/CONTACT）
        """
        import subprocess
        import os

        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        temp_video = output_path + ".tmp.avi"
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        writer = cv2.VideoWriter(temp_video, fourcc, fps, (frame_width, frame_height))

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            timestamp = frame_idx / fps
            result = self.detect_frame(frame, timestamp)

            # 获取当前阶段
            phase = None
            if frame_idx < len(phase_labels):
                p = phase_labels[frame_idx]
                phase = p.value if hasattr(p, 'value') else str(p)

            annotated = self.draw_phase_aware(
                frame, result, phase, bat_trajectory,
                frame_idx, frame_count, fps,
                show_trajectory=(
                    trajectory_valid_frames is not None
                    and frame_idx in trajectory_valid_frames
                ),
            )
            writer.write(annotated)

            frame_idx += 1
            if frame_idx % 30 == 0:
                print(f"阶段视频进度: {frame_idx}/{frame_count} ({frame_idx/frame_count*100:.1f}%)")

        cap.release()
        writer.release()

        # FFmpeg 转码
        print(f"正在转换阶段视频格式...")
        try:
            subprocess.run([
                'ffmpeg', '-y', '-i', temp_video,
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                output_path
            ], check=True, capture_output=True)
            os.remove(temp_video)
            print(f"阶段视频转换完成: {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg 转换失败: {e.stderr.decode()}")
            os.rename(temp_video, output_path.replace('.mp4', '.avi'))

    def read_frame_at(self, video_path: str, frame_idx: int) -> Optional[np.ndarray]:
        """读取指定帧（用于关键帧提取）"""
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        cap.release()
        return frame if ret else None

    def get_keypoint(self, result: DetectionResult, key: str) -> Optional[np.ndarray]:
        """获取指定关键点的坐标"""
        if key in POSE_LANDMARKS and result.pose_landmarks is not None:
            return result.pose_landmarks[POSE_LANDMARKS[key]]
        elif key in HAND_LANDMARKS:
            if result.left_hand_landmarks is not None and result.left_hand_handedness == "left":
                return result.left_hand_landmarks[HAND_LANDMARKS[key]]
            if result.right_hand_landmarks is not None:
                return result.right_hand_landmarks[HAND_LANDMARKS[key]]
        return None

    def cleanup(self):
        """清理资源"""
        self.pose_detector.close()
        self.hand_detector.close()
