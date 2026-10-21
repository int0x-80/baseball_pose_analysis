"""
关键帧提取与标注模块
从每个挥棒阶段选取 1 张代表性关键帧，叠加骨架 + 角度/速度标注
"""
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

from .phase_detector import SwingPhase, PhaseBoundary, FrameMetrics

logger = logging.getLogger(__name__)


@dataclass
class KeyFrame:
    """关键帧数据"""
    phase: SwingPhase
    frame_idx: int
    timestamp_sec: float
    metrics: Dict
    image: Optional[np.ndarray] = None


# 阶段 → 绘制颜色 (BGR)
PHASE_COLORS = {
    SwingPhase.STANCE: (255, 255, 255),
    SwingPhase.LOAD: (255, 150, 0),
    SwingPhase.STRIDE: (0, 255, 100),
    SwingPhase.SWING: (0, 50, 255),
    SwingPhase.CONTACT: (0, 255, 255),
    SwingPhase.FOLLOW_THROUGH: (255, 200, 0),
}


class KeyFrameExtractor:
    """
    关键帧提取器

    使用方式：
        extractor = KeyFrameExtractor()
        keyframes = extractor.extract_keyframes(video_path, boundaries, frame_metrics)
    """

    def extract_keyframes(
        self,
        video_path: str,
        boundaries: List[PhaseBoundary],
        frame_metrics: List[FrameMetrics],
    ) -> List[KeyFrame]:
        """
        从每个阶段提取代表性关键帧

        选取策略：
          STANCE         → 阶段中间帧
          LOAD           → 重心偏移最大帧
          STRIDE         → 前脚着地帧（阶段末尾）
          SWING          → 手腕速度峰值帧
          CONTACT        → 阶段中间帧
          FOLLOW_THROUGH → 阶段 70% 位置帧
        """
        keyframes: List[KeyFrame] = []

        for b in boundaries:
            fm = frame_metrics[b.start_frame:b.end_frame + 1]
            if not fm:
                continue

            if b.phase == SwingPhase.STANCE:
                idx = b.start_frame + (b.end_frame - b.start_frame) // 2
            elif b.phase == SwingPhase.LOAD:
                shifts = [abs(f.weight_balance) for f in fm]
                idx = b.start_frame + shifts.index(max(shifts))
            elif b.phase == SwingPhase.STRIDE:
                idx = b.end_frame
            elif b.phase == SwingPhase.SWING:
                speeds = [f.wrist_speed for f in fm]
                idx = b.start_frame + speeds.index(max(speeds))
            elif b.phase == SwingPhase.CONTACT:
                idx = b.start_frame + len(fm) // 2
            else:  # FOLLOW_THROUGH
                idx = b.start_frame + int((b.end_frame - b.start_frame) * 0.7)

            idx = max(b.start_frame, min(idx, b.end_frame))
            metrics = self._collect_metrics(fm, idx - b.start_frame)

            keyframes.append(KeyFrame(
                phase=b.phase,
                frame_idx=idx,
                timestamp_sec=idx / 30.0,
                metrics=metrics,
            ))

        return keyframes

    def _collect_metrics(self, phase_metrics: List[FrameMetrics], rel_idx: int) -> Dict:
        """收集关键帧的标注指标"""
        if rel_idx < 0 or rel_idx >= len(phase_metrics):
            return {}
        m = phase_metrics[rel_idx]
        return {
            'knee_angle': round(m.knee_angle_L, 1),
            'hip_sep': round(abs(m.shoulder_hip_separation), 1),
            'torso_twist': round(m.torso_twist, 1),
            'wrist_speed': round(m.wrist_speed, 2),
            'stance_width': round(m.stance_width, 4),
            'weight_balance': round(m.weight_balance, 4),
        }

    def annotate_keyframe(
        self,
        frame: np.ndarray,
        keyframe: KeyFrame,
        landmarks: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        在关键帧上绘制骨架 + 角度/速度标注

        Args:
            frame: 原始 BGR 帧
            keyframe: 关键帧数据
            landmarks: 归一化关键点 (33, 3)

        Returns:
            标注后的 BGR 帧
        """
        h, w = frame.shape[:2]
        annotated = frame.copy()
        color = PHASE_COLORS.get(keyframe.phase, (255, 255, 255))

        # 骨架
        if landmarks is not None and len(landmarks) >= 33:
            self._draw_skeleton(annotated, landmarks, color, w, h)

        # 半透明背景
        overlay = annotated.copy()
        cv2.rectangle(overlay, (10, 10), (380, 220), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, annotated, 0.4, 0, annotated)

        # 阶段标题
        phase_text = f"{keyframe.phase.value} {keyframe.phase.label_cn}"
        cv2.putText(annotated, phase_text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        # 指标
        y = 70
        for label, value in [
            ('Knee', f"{keyframe.metrics.get('knee_angle', 0):.0f}deg"),
            ('Hip-Sep', f"{keyframe.metrics.get('hip_sep', 0):.0f}deg"),
            ('Twist', f"{keyframe.metrics.get('torso_twist', 0):.0f}deg"),
            ('Speed', f"{keyframe.metrics.get('wrist_speed', 0):.1f} u/s"),
            ('Stance', f"{keyframe.metrics.get('stance_width', 0):.3f}"),
        ]:
            cv2.putText(annotated, f"{label}: {value}", (20, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
            y += 25

        # 帧号
        cv2.putText(annotated, f"Frame: {keyframe.frame_idx}", (20, h - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        return annotated

    def _draw_skeleton(
        self, frame: np.ndarray, landmarks: np.ndarray,
        color: Tuple[int, int, int], w: int, h: int,
    ):
        """在帧上绘制身体骨架（仅关节 + 鼻子单点）"""
        connections = [
            (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
            (11, 23), (12, 24), (23, 24),
            (23, 25), (25, 27), (24, 26), (26, 28),
            (27, 29), (29, 31), (28, 30), (30, 32),
        ]
        for s, e in connections:
            if s < len(landmarks) and e < len(landmarks):
                p1 = (int(landmarks[s][0] * w), int(landmarks[s][1] * h))
                p2 = (int(landmarks[e][0] * w), int(landmarks[e][1] * h))
                if 0 < p1[0] < w and 0 < p1[1] < h and 0 < p2[0] < w and 0 < p2[1] < h:
                    cv2.line(frame, p1, p2, color, 2)

        body_joints = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
        big_joints = {11, 12, 23, 24}
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
