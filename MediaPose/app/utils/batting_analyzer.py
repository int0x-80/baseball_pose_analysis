"""
棒球击球分析模块
整合阶段检测、生物力学指标、棒头轨迹，生成完整的击球分析报告
"""
import numpy as np
from typing import List, Dict, Optional
import logging

from .phase_detector import BattingPhaseDetector, SwingPhase, PhaseBoundary, FrameMetrics
from .bat_trajectory import BatTrajectoryTracker
from ..core.pose_detector import DetectionResult

logger = logging.getLogger(__name__)


class BattingAnalyzer:
    """
    棒球击球分析器

    使用方式：
        analyzer = BattingAnalyzer(fps=30)
        report = analyzer.analyze(detection_results)
    """

    def __init__(self, fps: int = 30):
        self.fps = fps
        self.dt = 1.0 / fps
        self.phase_detector = BattingPhaseDetector(fps=fps)
        self.trajectory_tracker = BatTrajectoryTracker(fps=fps)

    def analyze(self, results: List[DetectionResult]) -> Dict:
        """
        执行完整的击球分析

        Args:
            results: 所有帧的 DetectionResult 列表

        Returns:
            完整的击球分析报告
        """
        logger.info("开始击球专项分析...")

        # 1. 阶段检测
        labels, boundaries, frame_metrics = self.phase_detector.detect_phases(results)
        if not boundaries:
            logger.warning("未检测到有效阶段")
            return {'error': '未检测到有效的挥棒动作'}

        # 2. 各阶段指标
        phase_metrics = self.phase_detector.compute_phase_metrics(boundaries, frame_metrics)

        # 3. 棒头轨迹
        trajectory = self.trajectory_tracker.compute_trajectory(results)
        trajectory_summary = self.trajectory_tracker.get_trajectory_summary(trajectory)

        # 4. 击球速度（swing + contact 阶段的棒头速度峰值）
        contact_speed = self._extract_contact_speed(boundaries, trajectory)

        # 5. 逐帧棒头速度曲线
        bat_speed_curve = self._build_speed_curve(trajectory)

        # 6. 阶段时间线
        phase_timeline = self._build_phase_timeline(boundaries)

        report = {
            'phaseTimeline': phase_timeline,
            'battingMetrics': phase_metrics,
            'batTrajectory': trajectory_summary,
            'contactSpeed': contact_speed,
            'batSpeedCurve': bat_speed_curve,
        }

        logger.info(f"击球分析完成: {len(boundaries)} 个阶段, "
                     f"{len(trajectory)} 个轨迹点, "
                     f"击球速度 {contact_speed.get('speed_kmh', 0):.1f} km/h")
        return report

    def _extract_contact_speed(
        self,
        boundaries: List[PhaseBoundary],
        trajectory: List[Dict]
    ) -> Dict:
        """从 swing+contact 阶段提取击球速度（棒头峰值速度）"""
        target_frames = set()
        for b in boundaries:
            if b.phase in (SwingPhase.SWING, SwingPhase.CONTACT):
                for fi in range(b.start_frame, b.end_frame + 1):
                    target_frames.add(fi)

        if not trajectory:
            return {'speed_ms': 0, 'speed_kmh': 0, 'frame_idx': 0}

        # 取目标帧范围内的轨迹点
        speed_frames = [t for t in trajectory if t['frame_idx'] in target_frames]
        if not speed_frames:
            speed_frames = trajectory  # fallback: 全局

        peak = max(speed_frames, key=lambda t: t.get('bat_tip_speed_ms', 0))
        speed_ms = peak.get('bat_tip_speed_ms', 0)
        return {
            'speed_ms': round(speed_ms, 2),
            'speed_kmh': round(speed_ms * 3.6, 2),
            'frame_idx': peak.get('frame_idx', 0),
            'timestamp_sec': peak.get('timestamp', 0),
        }

    def _build_speed_curve(self, trajectory: List[Dict]) -> Dict:
        """构建逐帧棒头速度曲线"""
        if not trajectory:
            return {'frames': [], 'speeds_ms': [], 'speeds_kmh': []}
        frames = [t['frame_idx'] for t in trajectory]
        speeds_ms = [round(t.get('bat_tip_speed_ms', 0), 2) for t in trajectory]
        speeds_kmh = [round(s * 3.6, 2) for s in speeds_ms]
        return {
            'frames': frames,
            'speeds_ms': speeds_ms,
            'speeds_kmh': speeds_kmh,
            'peak_speed_kmh': max(speeds_kmh) if speeds_kmh else 0,
            'avg_speed_kmh': round(float(np.mean(speeds_kmh)), 2) if speeds_kmh else 0,
        }

    def _build_phase_timeline(self, boundaries: List[PhaseBoundary]) -> List[Dict]:
        """构建阶段时间线"""
        return [
            {
                'phase': b.phase.value,
                'phaseLabelCn': b.phase.label_cn,
                'startFrame': b.start_frame,
                'endFrame': b.end_frame,
                'startMs': round(b.start_time_sec * 1000, 1),
                'endMs': round(b.end_time_sec * 1000, 1),
                'durationMs': round(b.duration_sec * 1000, 1),
            }
            for b in boundaries
        ]

    def get_phase_labels_and_boundaries(
        self, results: List[DetectionResult]
    ) -> tuple:
        """获取阶段标签、边界和帧指标"""
        return self.phase_detector.detect_phases(results)
