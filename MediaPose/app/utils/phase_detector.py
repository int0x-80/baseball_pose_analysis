"""
挥棒阶段检测器
基于 MediaPipe BlazePose 33 关键点检测击球动作的 6 个阶段：
STANCE(准备站姿) -> LOAD(蓄力回拉) -> STRIDE(跨步转体)
-> SWING(挥棒加速) -> CONTACT(击球瞬间) -> FOLLOW_THROUGH(随挥收棒)

使用标准 MediaPipe BlazePose 索引：
  11=left_shoulder, 12=right_shoulder
  13=left_elbow,    14=right_elbow
  15=left_wrist,    16=right_wrist
  23=left_hip,      24=right_hip
  25=left_knee,     26=right_knee
  27=left_ankle,    28=right_ankle
  31=left_foot,     32=right_foot
"""
import numpy as np
from enum import Enum
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class SwingPhase(str, Enum):
    """挥棒阶段枚举"""
    STANCE = "STANCE"
    LOAD = "LOAD"
    STRIDE = "STRIDE"
    SWING = "SWING"
    CONTACT = "CONTACT"
    FOLLOW_THROUGH = "FOLLOW_THROUGH"

    @property
    def label_cn(self) -> str:
        labels = {
            'STANCE': '准备站姿',
            'LOAD': '蓄力回拉',
            'STRIDE': '跨步转体',
            'SWING': '挥棒加速',
            'CONTACT': '击球瞬间',
            'FOLLOW_THROUGH': '随挥收棒',
        }
        return labels.get(self.value, '')


@dataclass
class FrameMetrics:
    """单帧衍生指标（从归一化关键点计算）"""
    frame_idx: int
    knee_angle_L: float = 0.0
    knee_angle_R: float = 0.0
    hip_line_angle: float = 0.0
    shoulder_line_angle: float = 0.0
    shoulder_hip_separation: float = 0.0
    weight_balance: float = 0.0
    left_wrist_speed: float = 0.0
    right_wrist_speed: float = 0.0
    wrist_speed: float = 0.0
    hip_rotation: float = 0.0
    front_foot_y: float = 0.0
    front_foot_x: float = 0.0
    stance_width: float = 0.0
    hand_y: float = 0.0
    torso_twist: float = 0.0
    has_pose: bool = False


@dataclass
class PhaseBoundary:
    """阶段边界"""
    phase: SwingPhase
    start_frame: int
    end_frame: int
    start_time_sec: float
    end_time_sec: float
    duration_sec: float


@dataclass
class SwingCycle:
    """一次完整挥棒周期"""
    boundaries: List[PhaseBoundary]
    start_frame: int
    end_frame: int
    is_valid: bool = False
    peak_speed_kmh: float = 0.0


def _angle_2d(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
    """计算三点角度 a-b-c（度）"""
    ba = a[:2] - b[:2]
    bc = c[:2] - b[:2]
    cos_a = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    return float(np.degrees(np.arccos(np.clip(cos_a, -1.0, 1.0))))


def _line_angle_2d(p1: np.ndarray, p2: np.ndarray) -> float:
    """计算线段与水平线夹角（度）"""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return float(np.degrees(np.arctan2(dy, dx)))


class BattingPhaseDetector:
    """
    击球挥棒阶段检测器

    使用方式：
        detector = BattingPhaseDetector(fps=30)
        labels, boundaries, metrics = detector.detect_phases(detection_results)
    """

    def __init__(self, fps: int = 30):
        self.fps = fps
        self.dt = 1.0 / fps

        # 可调阈值（归一化坐标系下）
        self.knee_flexion_threshold = 160.0
        self.weight_shift_threshold = 0.015
        self.foot_lift_threshold = 0.025
        self.swing_hip_rotation_threshold = 5.0
        self.contact_velocity_drop_ratio = 0.85
        self.stability_threshold = 0.003
        self.min_phase_frames = 3
        self.smoothing_window = 5

    def _smooth(self, values: List[float]) -> List[float]:
        """移动平均平滑"""
        if len(values) < self.smoothing_window:
            return values
        kernel = np.ones(self.smoothing_window) / self.smoothing_window
        return list(np.convolve(values, kernel, mode='same'))

    def _compute_frame_metrics(
        self,
        landmarks: Optional[np.ndarray],
        prev_landmarks: Optional[np.ndarray]
    ) -> FrameMetrics:
        """从归一化关键点计算单帧衍生指标"""
        m = FrameMetrics(frame_idx=0)
        if landmarks is None or len(landmarks) < 33:
            return m
        m.has_pose = True

        ls = landmarks[11]; rs = landmarks[12]
        le = landmarks[13]; re = landmarks[14]
        lw = landmarks[15]; rw = landmarks[16]
        lh = landmarks[23]; rh = landmarks[24]
        lk = landmarks[25]; rk = landmarks[26]
        la = landmarks[27]; ra = landmarks[28]

        m.knee_angle_L = _angle_2d(lh, lk, la)
        m.knee_angle_R = _angle_2d(rh, rk, ra)
        m.hip_line_angle = _line_angle_2d(lh, rh)
        m.shoulder_line_angle = _line_angle_2d(ls, rs)
        m.shoulder_hip_separation = m.shoulder_line_angle - m.hip_line_angle
        m.torso_twist = abs(m.shoulder_hip_separation)

        hip_cx = (lh[0] + rh[0]) / 2
        ankle_cx = (la[0] + ra[0]) / 2
        m.weight_balance = hip_cx - ankle_cx
        m.stance_width = float(np.linalg.norm(la[:2] - ra[:2]))

        if prev_landmarks is not None and len(prev_landmarks) >= 33:
            plw = prev_landmarks[15]; prw = prev_landmarks[16]
            m.left_wrist_speed = float(np.linalg.norm(lw[:2] - plw[:2])) / self.dt
            m.right_wrist_speed = float(np.linalg.norm(rw[:2] - prw[:2])) / self.dt
            m.wrist_speed = max(m.left_wrist_speed, m.right_wrist_speed)

            prev_hip_angle = _line_angle_2d(prev_landmarks[23], prev_landmarks[24])
            m.hip_rotation = m.hip_line_angle - prev_hip_angle

        # 默认左脚为前脚（左打者常见）
        m.front_foot_y = la[1]
        m.front_foot_x = la[0]
        m.hand_y = (lw[1] + rw[1]) / 2

        return m

    def detect_phases(
        self,
        results: list
    ) -> Tuple[List[SwingPhase], List[PhaseBoundary], List[FrameMetrics]]:
        """
        检测所有帧的挥棒阶段

        Args:
            results: DetectionResult 列表

        Returns:
            (phase_labels, phase_boundaries, frame_metrics)
        """
        n = len(results)
        if n == 0:
            return [], [], []

        # ===== 第一步：计算所有帧衍生指标 =====
        metrics: List[FrameMetrics] = []
        for i in range(n):
            curr = results[i].pose_landmarks
            prev = results[i - 1].pose_landmarks if i > 0 else None
            fm = self._compute_frame_metrics(curr, prev)
            fm.frame_idx = i
            metrics.append(fm)

        ws = self._smooth([m.wrist_speed for m in metrics])
        hr = self._smooth([abs(m.hip_rotation) for m in metrics])
        for i in range(n):
            metrics[i].wrist_speed = ws[i]
            metrics[i].hip_rotation = hr[i]

        # ===== 第二步：找参考值 =====
        valid = [m for m in metrics if m.has_pose]
        if len(valid) < self.min_phase_frames * 3:
            logger.warning(f"有效帧不足 ({len(valid)})，全部标记为 STANCE")
            labels = [SwingPhase.STANCE] * n
            boundaries = [PhaseBoundary(
                SwingPhase.STANCE, 0, n - 1, 0, (n - 1) * self.dt, (n - 1) * self.dt
            )]
            return labels, boundaries, metrics

        init_n = min(10, len(valid))
        init_foot_y = np.mean([valid[i].front_foot_y for i in range(init_n)])
        init_balance = np.mean([valid[i].weight_balance for i in range(init_n)])

        peak_idx = max(range(n), key=lambda i: metrics[i].wrist_speed)

        # ===== 第三步：状态机 =====
        labels = [SwingPhase.STANCE] * n
        state = SwingPhase.STANCE
        ft_start_frame = 0  # FOLLOW_THROUGH 阶段起始帧
        min_ft_frames = int(self.fps * 1.5)  # FOLLOW_THROUGH 最少持续 1.5 秒

        for i in range(n):
            m = metrics[i]
            if not m.has_pose:
                labels[i] = state
                continue
            labels[i] = state

            if state == SwingPhase.STANCE:
                knee_flexed = m.knee_angle_L < self.knee_flexion_threshold
                weight_shifted = abs(m.weight_balance - init_balance) > self.weight_shift_threshold
                if knee_flexed or weight_shifted:
                    state = SwingPhase.LOAD
                    labels[i] = state

            elif state == SwingPhase.LOAD:
                foot_y_delta = abs(m.front_foot_y - init_foot_y)
                if foot_y_delta > self.foot_lift_threshold:
                    state = SwingPhase.STRIDE
                    labels[i] = state

            elif state == SwingPhase.STRIDE:
                foot_y_delta = abs(m.front_foot_y - init_foot_y)
                foot_planted = foot_y_delta < self.foot_lift_threshold * 0.5
                hip_accel = m.hip_rotation > self.swing_hip_rotation_threshold * self.dt
                past_half = i > n * 0.2
                if foot_planted and (hip_accel or past_half):
                    state = SwingPhase.SWING
                    labels[i] = state
                elif i >= peak_idx - self.min_phase_frames:
                    state = SwingPhase.SWING
                    labels[i] = state

            elif state == SwingPhase.SWING:
                peak_speed = metrics[peak_idx].wrist_speed
                if i >= peak_idx and peak_speed > 0:
                    if m.wrist_speed < peak_speed * self.contact_velocity_drop_ratio:
                        state = SwingPhase.CONTACT
                        labels[i] = state
                elif i > peak_idx + int(self.fps * 0.5):
                    state = SwingPhase.CONTACT
                    labels[i] = state

            elif state == SwingPhase.CONTACT:
                peak_speed = metrics[peak_idx].wrist_speed
                if m.wrist_speed < peak_speed * 0.3:
                    state = SwingPhase.FOLLOW_THROUGH
                    ft_start_frame = i
                    labels[i] = state
                elif i > peak_idx + int(self.fps * 0.5):
                    state = SwingPhase.FOLLOW_THROUGH
                    ft_start_frame = i
                    labels[i] = state

            elif state == SwingPhase.FOLLOW_THROUGH:
                # 持续至少 1.5 秒后，手腕稳定则重置回 STANCE（支持多次挥棒检测）
                if (i - ft_start_frame) >= min_ft_frames:
                    if m.wrist_speed < self.stability_threshold * 5:
                        state = SwingPhase.STANCE
                        labels[i] = state
                        # 更新参考基线
                        init_balance = m.weight_balance
                        init_foot_y = m.front_foot_y
                        # 重新计算后续峰值帧
                        future = [j for j in range(i, min(i + self.fps * 6, n))
                                  if metrics[j].has_pose]
                        if future:
                            peak_idx = max(future, key=lambda j: metrics[j].wrist_speed)

        # ===== 第四步：构建边界 =====
        boundaries = self._build_boundaries(labels)

        logger.info("阶段检测结果:")
        for b in boundaries:
            fc = b.end_frame - b.start_frame + 1
            logger.info(f"  {b.phase.value:16s} {b.phase.label_cn:8s}  "
                        f"帧 {b.start_frame:4d}-{b.end_frame:4d} ({fc}帧)  "
                        f"{b.start_time_sec:.2f}-{b.end_time_sec:.2f}s ({b.duration_sec:.2f}s)")

        return labels, boundaries, metrics

    def _build_boundaries(self, labels: List[SwingPhase]) -> List[PhaseBoundary]:
        """从逐帧标签构建阶段边界"""
        if not labels:
            return []
        boundaries = []
        current = labels[0]
        start = 0
        for i in range(1, len(labels)):
            if labels[i] != current:
                boundaries.append(PhaseBoundary(
                    phase=current, start_frame=start, end_frame=i - 1,
                    start_time_sec=start * self.dt,
                    end_time_sec=(i - 1) * self.dt,
                    duration_sec=(i - 1 - start) * self.dt
                ))
                current = labels[i]
                start = i
        boundaries.append(PhaseBoundary(
            phase=current, start_frame=start, end_frame=len(labels) - 1,
            start_time_sec=start * self.dt,
            end_time_sec=(len(labels) - 1) * self.dt,
            duration_sec=(len(labels) - 1 - start) * self.dt
        ))
        return boundaries

    def compute_phase_metrics(
        self,
        boundaries: List[PhaseBoundary],
        metrics: List[FrameMetrics]
    ) -> Dict:
        """计算每个阶段的汇总指标"""
        result = {}
        for b in boundaries:
            phase_m = metrics[b.start_frame:b.end_frame + 1]
            if not phase_m:
                continue
            p = b.phase
            if p == SwingPhase.STANCE:
                result['stance'] = self._stance_metrics(phase_m)
            elif p == SwingPhase.LOAD:
                result['load'] = self._load_metrics(phase_m)
            elif p == SwingPhase.STRIDE:
                result['stride'] = self._stride_metrics(phase_m)
            elif p == SwingPhase.SWING:
                result['swing'] = self._swing_metrics(phase_m)
            elif p == SwingPhase.CONTACT:
                result['contact'] = self._contact_metrics(phase_m)
            elif p == SwingPhase.FOLLOW_THROUGH:
                result['follow_through'] = self._follow_through_metrics(phase_m)
        return result

    def _stance_metrics(self, m: List[FrameMetrics]) -> Dict:
        widths = [f.stance_width for f in m]
        knees_L = [f.knee_angle_L for f in m]
        knees_R = [f.knee_angle_R for f in m]
        balances = [f.weight_balance for f in m]
        return {
            'stance_width_m': round(float(np.mean(widths)), 4),
            'knee_flexion_L_deg': round(float(np.mean(knees_L)), 2),
            'knee_flexion_R_deg': round(float(np.mean(knees_R)), 2),
            'torso_uprightness_deg': round(float(np.mean([abs(f.shoulder_line_angle) for f in m])), 2),
            'weight_balance': round(float(np.mean(balances)), 4),
        }

    def _load_metrics(self, m: List[FrameMetrics]) -> Dict:
        balances = [f.weight_balance for f in m]
        shifts = [abs(f.weight_balance - balances[0]) for f in m]
        seps = [abs(f.shoulder_hip_separation) for f in m]
        return {
            'weight_shift_ratio': round(float(max(shifts)), 4) if shifts else 0,
            'shoulder_hip_separation_deg': round(float(max(seps)), 2) if seps else 0,
            'load_duration_ms': round(len(m) * self.dt * 1000, 1),
        }

    def _stride_metrics(self, m: List[FrameMetrics]) -> Dict:
        foot_xs = [f.front_foot_x for f in m]
        foot_ys = [f.front_foot_y for f in m]
        stride_dx = foot_xs[-1] - foot_xs[0] if len(foot_xs) > 1 else 0
        stride_dy = foot_ys[-1] - foot_ys[0] if len(foot_ys) > 1 else 0
        stride_len = np.sqrt(stride_dx ** 2 + stride_dy ** 2)
        direction = float(np.degrees(np.arctan2(stride_dy, stride_dx)))
        knee_at_plant = m[-1].knee_angle_L if m else 0
        hip_rot_end = m[-1].shoulder_hip_separation if m else 0
        return {
            'stride_length': round(float(stride_len), 4),
            'stride_direction_deg': round(direction, 2),
            'hip_rotation_start_deg': round(hip_rot_end, 2),
            'front_knee_at_plant_deg': round(knee_at_plant, 2),
        }

    def _swing_metrics(self, m: List[FrameMetrics]) -> Dict:
        speeds = [f.wrist_speed for f in m]
        seps = [abs(f.shoulder_hip_separation) for f in m]
        peak_speed = max(speeds) if speeds else 0
        avg_speed = float(np.mean(speeds)) if speeds else 0
        peak_i = speeds.index(peak_speed) if speeds else 0
        bat_len = 0.85
        arm_len = 0.7
        ratio = 1 + bat_len / arm_len
        return {
            'peak_bat_speed_kmh': round(peak_speed * ratio * 3.6, 2),
            'avg_bat_speed_kmh': round(avg_speed * ratio * 3.6, 2),
            'peak_wrist_speed': round(peak_speed, 4),
            'shoulder_hip_max_separation_deg': round(max(seps), 2) if seps else 0,
            'swing_duration_ms': round(len(m) * self.dt * 1000, 1),
            'peak_frame_relative': round(peak_i / max(len(m) - 1, 1), 3),
        }

    def _contact_metrics(self, m: List[FrameMetrics]) -> Dict:
        seps = [abs(f.shoulder_hip_separation) for f in m]
        return {
            'contact_hip_rotation_deg': round(float(np.mean([abs(f.hip_line_angle) for f in m])), 2),
            'contact_torso_twist_deg': round(float(np.mean(seps)), 2) if seps else 0,
        }

    def _follow_through_metrics(self, m: List[FrameMetrics]) -> Dict:
        speeds = [f.wrist_speed for f in m]
        decel_rates = []
        for i in range(1, len(speeds)):
            decel_rates.append(speeds[i] - speeds[i - 1])
        balances = [abs(f.weight_balance) for f in m]
        return {
            'deceleration_smoothness': round(float(np.std(decel_rates)), 4) if decel_rates else 0,
            'balance_at_finish': round(float(balances[-1]), 4) if balances else 0,
            'follow_through_duration_ms': round(len(m) * self.dt * 1000, 1),
        }

    # ===== 挥棒周期检测与验证 =====

    def detect_swing_cycles(
        self, boundaries: List[PhaseBoundary]
    ) -> List[SwingCycle]:
        """
        从 boundaries 中切分出每一次挥棒周期。
        每当阶段从 FOLLOW_THROUGH 回到 STANCE 时，视为新周期起点。
        """
        if not boundaries:
            return []

        cycles: List[SwingCycle] = []
        current_group: List[PhaseBoundary] = [boundaries[0]]

        for i in range(1, len(boundaries)):
            prev_phase = boundaries[i - 1].phase
            curr_phase = boundaries[i].phase

            # FOLLOW_THROUGH → STANCE 表示周期边界
            if prev_phase == SwingPhase.FOLLOW_THROUGH and curr_phase == SwingPhase.STANCE:
                cycles.append(SwingCycle(
                    boundaries=list(current_group),
                    start_frame=current_group[0].start_frame,
                    end_frame=current_group[-1].end_frame,
                ))
                current_group = [boundaries[i]]
            else:
                current_group.append(boundaries[i])

        # 最后一组
        if current_group:
            cycles.append(SwingCycle(
                boundaries=list(current_group),
                start_frame=current_group[0].start_frame,
                end_frame=current_group[-1].end_frame,
            ))

        return cycles

    def validate_swing_cycles(
        self,
        cycles: List[SwingCycle],
        metrics: List[FrameMetrics],
    ) -> List[SwingCycle]:
        """
        验证每个周期是否为标准挥棒：
          - 包含全部 6 个阶段
          - SWING 阶段峰值腕速 ≥ 0.5（归一化坐标/秒）
        不满足条件的周期标记 is_valid=False，不显示轨迹。
        """
        MIN_PEAK_WRIST_SPEED = 0.5  # 归一化坐标/秒
        REQUIRED_PHASES = {
            SwingPhase.STANCE, SwingPhase.LOAD, SwingPhase.STRIDE,
            SwingPhase.SWING, SwingPhase.CONTACT, SwingPhase.FOLLOW_THROUGH,
        }

        for cycle in cycles:
            phases = {b.phase for b in cycle.boundaries}

            # 必须包含全部 6 个阶段
            if not REQUIRED_PHASES.issubset(phases):
                logger.info(f"周期 帧{cycle.start_frame}-{cycle.end_frame}: "
                            f"阶段不完整 {phases}，标记无效")
                cycle.is_valid = False
                continue

            # 找 SWING 阶段的峰值腕速
            swing_b = [b for b in cycle.boundaries if b.phase == SwingPhase.SWING]
            peak_wrist = 0.0
            if swing_b:
                sb = swing_b[0]
                swing_m = metrics[sb.start_frame:sb.end_frame + 1]
                if swing_m:
                    peak_wrist = max(m.wrist_speed for m in swing_m)

            cycle.peak_speed_kmh = round(peak_wrist * 2.214 * 3.6, 1)

            if peak_wrist < MIN_PEAK_WRIST_SPEED:
                logger.info(f"周期 帧{cycle.start_frame}-{cycle.end_frame}: "
                            f"峰值腕速 {peak_wrist:.2f} m/s 不足，标记无效")
                cycle.is_valid = False
            else:
                cycle.is_valid = True
                logger.info(f"周期 帧{cycle.start_frame}-{cycle.end_frame}: "
                            f"标准挥棒 (峰值 {cycle.peak_speed_kmh} km/h)")

        return cycles
