"""
动作分析模块 - 计算速度、角度、轨迹和评分
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from ..core.pose_detector import DetectionResult, POSE_LANDMARKS
from ..models.pose_data import SwingData, BodyTwist, ActionScore

# 假设摄像机到人的距离为 3 米
DISTANCE_METERS = 3.0


@dataclass
class HandTrajectory:
    """手部轨迹数据"""
    x: List[float]
    y: List[float]
    z: List[float]
    timestamps: List[float]


class ActionAnalyzer:
    """动作分析器"""

    def __init__(self, fps: int = 30):
        self.fps = fps
        self.dt = 1.0 / fps

    def analyze_swing(self, results: List[DetectionResult], hand: str = "right") -> SwingData:
        """分析挥动动作（速度）"""
        trajectory = self._extract_hand_trajectory(results, hand)

        if not trajectory.x or len(trajectory.x) < 2:
            return SwingData(
                hand=hand,
                max_speed=0.0,
                avg_speed=0.0,
                peak_time=0.0,
                trajectory=[]
            )

        # 计算每个时间点的速度
        speeds = []
        trajectory_points = []

        for i in range(1, len(trajectory.x)):
            dx = (trajectory.x[i] - trajectory.x[i-1]) * DISTANCE_METERS
            dy = (trajectory.y[i] - trajectory.y[i-1]) * DISTANCE_METERS
            dz = (trajectory.z[i] - trajectory.z[i-1]) * DISTANCE_METERS

            distance = np.sqrt(dx**2 + dy**2 + dz**2)
            speed = distance / self.dt
            speeds.append(speed)

            trajectory_points.append({
                "x": trajectory.x[i],
                "y": trajectory.y[i],
                "z": trajectory.z[i],
                "timestamp": trajectory.timestamps[i],
                "speed": speed
            })

        if not speeds:
            return SwingData(
                hand=hand,
                max_speed=0.0,
                avg_speed=0.0,
                peak_time=0.0,
                trajectory=[]
            )

        max_speed = max(speeds)
        avg_speed = np.mean(speeds)
        peak_time_idx = speeds.index(max_speed)
        peak_time = trajectory.timestamps[peak_time_idx + 1] if peak_time_idx + 1 < len(trajectory.timestamps) else 0

        return SwingData(
            hand=hand,
            max_speed=float(max_speed),
            avg_speed=float(avg_speed),
            peak_time=float(peak_time),
            trajectory=trajectory_points
        )

    def analyze_body_twist(self, results: List[DetectionResult]) -> BodyTwist:
        """分析身体扭转角度"""
        twist_angles = []

        for result in results:
            if result.pose_landmarks is None:
                twist_angles.append(0.0)
                continue

            # 获取肩部关键点
            left_shoulder = result.pose_landmarks[POSE_LANDMARKS["left_shoulder"]]
            right_shoulder = result.pose_landmarks[POSE_LANDMARKS["right_shoulder"]]

            # 获取臀部关键点
            left_hip = result.pose_landmarks[POSE_LANDMARKS["left_hip"]]
            right_hip = result.pose_landmarks[POSE_LANDMARKS["right_hip"]]

            # 计算肩部角度
            shoulder_angle = self._calculate_twist_angle(left_shoulder, right_shoulder)

            # 计算臀部角度
            hip_angle = self._calculate_twist_angle(left_hip, right_hip)

            # 身体扭转角度 = 肩部角度 - 臀部角度
            twist_angle = abs(shoulder_angle - hip_angle)
            twist_angles.append(twist_angle)

        if not twist_angles:
            return BodyTwist(
                max_twist_angle=0.0,
                avg_twist_angle=0.0,
                twist_timeline=[]
            )

        return BodyTwist(
            max_twist_angle=float(max(twist_angles)),
            avg_twist_angle=float(np.mean(twist_angles)),
            twist_timeline=[float(a) for a in twist_angles]
        )

    def calculate_action_score(
        self,
        left_swing: Optional[SwingData],
        right_swing: Optional[SwingData],
        body_twist: BodyTwist
    ) -> ActionScore:
        """计算动作评分"""
        suggestions = []

        # 速度评分 (基准: 职业选手击球速度约 40-50 m/s)
        target_speed = 45.0
        main_swing = right_swing if right_swing and right_swing.max_speed > (left_swing.max_speed if left_swing else 0) else left_swing

        if main_swing:
            speed_score = min(100, (main_swing.max_speed / target_speed) * 100)
            if speed_score < 60:
                suggestions.append("挥动速度偏慢，建议增加发力")
        else:
            speed_score = 0
            suggestions.append("未检测到有效挥动动作")

        # 扭转角度评分 (基准: 职业选手扭转约 45-60 度)
        target_twist = 50.0
        angle_score = min(100, (body_twist.max_twist_angle / target_twist) * 100)

        if angle_score < 50:
            suggestions.append("身体扭转不足，建议增加腰部发力")
        elif angle_score > 100:
            suggestions.append("身体扭转过度，注意保持平衡")

        # 一致性评分 (基于轨迹的平滑度)
        if main_swing and len(main_swing.trajectory) > 10:
            consistency_score = self._calculate_consistency_score(main_swing.trajectory)
            if consistency_score < 70:
                suggestions.append("动作轨迹不够稳定，建议练习一致性")
        else:
            consistency_score = 60

        # 总体评分
        overall_score = (speed_score * 0.4 + angle_score * 0.3 + consistency_score * 0.3)

        return ActionScore(
            overall_score=float(round(overall_score, 2)),
            speed_score=float(round(speed_score, 2)),
            angle_score=float(round(angle_score, 2)),
            consistency_score=float(round(consistency_score, 2)),
            suggestions=suggestions
        )

    def analyze_trajectory_consistency(
        self,
        trajectory1: List[Dict[str, float]],
        trajectory2: List[Dict[str, float]]
    ) -> float:
        """计算两条轨迹的相似度 (0-100)"""
        if not trajectory1 or not trajectory2:
            return 0.0

        # 对齐轨迹时间
        min_len = min(len(trajectory1), len(trajectory2))

        # 使用 DTW (Dynamic Time Warping) 或简单插值
        distances = []
        for i in range(min_len):
            p1 = trajectory1[i]
            p2 = trajectory2[i]

            dx = p1["x"] - p2["x"]
            dy = p1["y"] - p2["y"]
            dz = p1["z"] - p2["z"]

            distance = np.sqrt(dx**2 + dy**2 + dz**2)
            distances.append(distance)

        avg_distance = np.mean(distances)
        # 距离越小，相似度越高
        similarity = max(0, 100 - avg_distance * 500)

        return float(similarity)

    def _extract_hand_trajectory(self, results: List[DetectionResult], hand: str) -> HandTrajectory:
        """提取手部轨迹"""
        x, y, z, timestamps = [], [], [], []

        for result in results:
            if result.pose_landmarks is None:
                continue

            if hand == "left":
                keypoint = result.pose_landmarks[POSE_LANDMARKS["left_wrist"]]
            else:
                keypoint = result.pose_landmarks[POSE_LANDMARKS["right_wrist"]]

            if keypoint is not None:
                x.append(keypoint[0])
                y.append(keypoint[1])
                z.append(keypoint[2])
                timestamps.append(result.timestamp)

        return HandTrajectory(x=x, y=y, z=z, timestamps=timestamps)

    def _calculate_twist_angle(self, left_point: np.ndarray, right_point: np.ndarray) -> float:
        """计算两点连线的角度（与水平线的夹角）"""
        dx = right_point[0] - left_point[0]
        dy = right_point[1] - left_point[1]

        angle_rad = np.arctan2(dy, dx)
        angle_deg = np.degrees(angle_rad)

        return angle_deg

    def _calculate_consistency_score(self, trajectory: List[Dict[str, float]]) -> float:
        """计算轨迹一致性评分"""
        if len(trajectory) < 3:
            return 0.0

        # 计算速度变化的平滑度
        speeds = [p["speed"] for p in trajectory if "speed" in p]

        if len(speeds) < 2:
            return 60.0

        # 计算速度变化的标准差
        speed_std = np.std(speeds)
        speed_mean = np.mean(speeds)

        if speed_mean == 0:
            return 60.0

        # 变异系数越小，动作越稳定
        cv = speed_std / speed_mean if speed_mean > 0 else 0

        # 转换为 0-100 分数
        consistency_score = max(0, 100 - cv * 200)

        return float(consistency_score)

    def estimate_ball_speed(self, swing_data: SwingData, bat_length: float = 1.07) -> float:
        """估算击球速度 (m/s)

        Args:
            swing_data: 挥动数据
            bat_length: 球棒长度 (米，标准约 1.07m)
        """
        # 假设球棒长度为 bat_length，击球点距离手握处约 2/3 的长度
        effective_length = bat_length * 0.67

        # 击球速度 ≈ 挥动速度 × 杠杆比率
        ball_speed = swing_data.max_speed * (1 + effective_length / 0.3)

        return float(ball_speed)

    def detect_action_start_end(
        self,
        results: List[DetectionResult],
        hand: str = "right",
        threshold: float = 0.05
    ) -> Tuple[float, float]:
        """检测动作的起始和结束时间"""
        trajectory = self._extract_hand_trajectory(results, hand)

        if len(trajectory.x) < 10:
            return 0.0, 0.0

        # 计算速度
        speeds = []
        for i in range(1, len(trajectory.x)):
            dx = trajectory.x[i] - trajectory.x[i-1]
            dy = trajectory.y[i] - trajectory.y[i-1]
            speed = np.sqrt(dx**2 + dy**2)
            speeds.append(speed)

        # 找到开始动作的帧（速度超过阈值）
        start_idx = 0
        for i, speed in enumerate(speeds):
            if speed > threshold:
                start_idx = i
                break

        # 找到动作结束的帧（速度降到阈值以下）
        end_idx = len(speeds)
        for i in range(len(speeds) - 1, -1, -1):
            if speeds[i] > threshold:
                end_idx = i + 1
                break

        start_time = trajectory.timestamps[start_idx] if start_idx < len(trajectory.timestamps) else 0
        end_time = trajectory.timestamps[min(end_idx, len(trajectory.timestamps) - 1)] if trajectory.timestamps else 0

        return start_time, end_time