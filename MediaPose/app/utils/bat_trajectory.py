"""
棒头轨迹估算与击球速度计算
从手腕 + 肘部关键点估算棒头位置，计算逐帧棒头速度

原理：
  bat_tip = wrist + (wrist - elbow) * (BAT_LENGTH / ARM_LENGTH)
  棒头速度 = 平移速度（手腕速度） + 旋转速度（角速度 × 棒长）

使用标准 MediaPipe BlazePose 索引：
  13=left_elbow, 14=right_elbow
  15=left_wrist, 16=right_wrist
"""
import numpy as np
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

BAT_LENGTH_METERS = 0.85
ARM_LENGTH_METERS = 0.70
BAT_RATIO = BAT_LENGTH_METERS / ARM_LENGTH_METERS


def _estimate_bat_tip(wrist: np.ndarray, elbow: np.ndarray) -> np.ndarray:
    """沿前臂方向外推估算棒头位置"""
    arm_vec = wrist - elbow
    return wrist + arm_vec * BAT_RATIO


def _safe_norm(v: np.ndarray) -> float:
    return float(np.linalg.norm(v) + 1e-8)


class BatTrajectoryTracker:
    """
    棒头轨迹追踪器

    使用方式：
        tracker = BatTrajectoryTracker(fps=30)
        trajectory = tracker.compute_trajectory(detection_results)
        summary = tracker.get_trajectory_summary(trajectory)
    """

    def __init__(self, fps: int = 30):
        self.fps = fps
        self.dt = 1.0 / fps

    def compute_trajectory(self, results: list) -> List[Dict]:
        """
        计算所有帧的棒头位置和速度

        Args:
            results: DetectionResult 列表

        Returns:
            每帧的轨迹数据字典列表
        """
        trajectory: List[Dict] = []
        prev_tip = None

        for i, result in enumerate(results):
            if result.pose_landmarks is None or len(result.pose_landmarks) < 33:
                continue

            lm = result.pose_landmarks

            # 选择可见性较好的手臂（优先右手，否则左手）
            rw = lm[16]; re = lm[14]
            lw = lm[15]; le = lm[13]

            r_vis = rw[0] > 0 and rw[1] > 0 and re[0] > 0 and re[1] > 0
            l_vis = lw[0] > 0 and lw[1] > 0 and le[0] > 0 and le[1] > 0

            if r_vis:
                wrist, elbow = rw, re
            elif l_vis:
                wrist, elbow = lw, le
            else:
                continue

            bat_tip = _estimate_bat_tip(wrist, elbow)

            # 棒头速度 = 平移 + 旋转
            bat_tip_speed = 0.0
            if prev_tip is not None:
                delta = bat_tip[:2] - prev_tip[:2]
                translational = _safe_norm(delta) / self.dt

                # 旋转分量
                curr_dir = bat_tip - wrist
                prev_wrist = trajectory[-1].get('wrist_pos', wrist.tolist()) if trajectory else wrist.tolist()
                prev_dir = prev_tip - np.array(prev_wrist) if trajectory else curr_dir

                curr_norm = curr_dir[:2] / _safe_norm(curr_dir[:2])
                prev_norm = prev_dir[:2] / _safe_norm(prev_dir[:2])
                cross = abs(curr_norm[0] * prev_norm[1] - curr_norm[1] * prev_norm[0])
                angular_speed = cross / self.dt
                rotational = angular_speed * BAT_LENGTH_METERS

                bat_tip_speed = translational + rotational

            prev_tip = bat_tip.copy()
            trajectory.append({
                'frame_idx': i,
                'timestamp': round(i * self.dt, 4),
                'bat_tip_x': round(float(bat_tip[0]), 6),
                'bat_tip_y': round(float(bat_tip[1]), 6),
                'bat_tip_z': round(float(bat_tip[2]), 6),
                'wrist_x': round(float(wrist[0]), 6),
                'wrist_y': round(float(wrist[1]), 6),
                'elbow_x': round(float(elbow[0]), 6),
                'elbow_y': round(float(elbow[1]), 6),
                'wrist_pos': wrist.tolist(),
                'bat_tip_speed_ms': round(float(bat_tip_speed), 4),
                'bat_tip_speed_kmh': round(float(bat_tip_speed) * 3.6, 2),
            })

        # Savitzky-Golay 平滑速度
        if len(trajectory) > 7:
            self._smooth_speeds(trajectory)

        return trajectory

    def _smooth_speeds(self, trajectory: List[Dict]):
        """使用 Savitzky-Golay 滤波平滑速度"""
        try:
            from scipy.signal import savgol_filter
            speeds = np.array([t['bat_tip_speed_ms'] for t in trajectory])
            win = min(11, len(speeds) - 1 if len(speeds) % 2 == 0 else len(speeds))
            if win % 2 == 0:
                win -= 1
            if win >= 5:
                smoothed = savgol_filter(speeds, win, 3)
                for i, t in enumerate(trajectory):
                    t['bat_tip_speed_ms'] = round(float(max(0, smoothed[i])), 4)
                    t['bat_tip_speed_kmh'] = round(float(max(0, smoothed[i]) * 3.6), 2)
        except Exception as e:
            logger.warning(f"Savitzky-Golay 平滑失败，使用原始速度: {e}")

    def get_trajectory_summary(self, trajectory: List[Dict]) -> Dict:
        """轨迹汇总统计"""
        if not trajectory:
            return {'total_points': 0}

        tips = [(t['bat_tip_x'], t['bat_tip_y']) for t in trajectory]
        speeds = [t['bat_tip_speed_ms'] for t in trajectory]
        peak_idx = max(range(len(speeds)), key=lambda i: speeds[i])

        # 轨迹长度
        path_len = 0.0
        for i in range(1, len(tips)):
            dx = tips[i][0] - tips[i - 1][0]
            dy = tips[i][1] - tips[i - 1][1]
            path_len += np.sqrt(dx * dx + dy * dy)

        direct = np.sqrt(
            (tips[-1][0] - tips[0][0]) ** 2 + (tips[-1][1] - tips[0][1]) ** 2
        )

        return {
            'total_points': len(trajectory),
            'path_length': round(float(path_len), 4),
            'direct_distance': round(float(direct), 4),
            'path_efficiency': round(float(direct / (path_len + 1e-6)), 4),
            'peak_speed_ms': round(max(speeds), 2) if speeds else 0,
            'peak_speed_kmh': round(max(speeds) * 3.6, 2) if speeds else 0,
            'peak_speed_frame': trajectory[peak_idx]['frame_idx'] if trajectory else 0,
            'avg_speed_ms': round(float(np.mean(speeds)), 2) if speeds else 0,
        }
