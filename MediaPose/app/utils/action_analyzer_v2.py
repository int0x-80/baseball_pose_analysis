"""
动作分析模块 v2 - 参考 pose_skeleton_advanced.py
支持详细数据分析、评分和 JSON 输出
包含挥棒速度和轨迹分析
"""
import numpy as np
import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from ..core.pose_detector import DetectionResult, POSE_LANDMARKS
from .advanced_analyzer import AdvancedMotionAnalyzer

# 关键点索引映射
KEYPOINTS = {
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_elbow": 13,
    "right_elbow": 14,
    "left_wrist": 15,
    "right_wrist": 16,
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

# 棒球棒典型长度（米）
BAT_LENGTH_METERS = 0.85


@dataclass
class MotionFrameData:
    """单帧运动数据"""
    frame_number: int
    timestamp_ms: int
    timestamp_sec: float
    arms: Dict
    hips: Dict
    torso: Dict
    swing: Dict  # 挥棒数据（速度、轨迹点）


class ActionAnalyzerV2:
    """动作分析器 v2 - 包含挥棒速度和轨迹分析"""

    def __init__(self, fps: int = 30, pixels_to_meters: float = 0.002):
        self.fps = fps
        self.dt = 1.0 / fps
        self.pixels_to_meters = pixels_to_meters

        # 历史数据
        self.left_wrist_history = []
        self.right_wrist_history = []
        self.hip_angle_history = []
        self.torso_twist_history = []

        # 所有帧数据
        self.all_frames_data: List[MotionFrameData] = []

        # 挥棒轨迹数据（完整轨迹）
        self.swing_trajectory_points: List[Dict] = []

        # 挥棒速度历史
        self.bat_speed_history: List[float] = []
        
        # 高级分析器
        self.advanced_analyzer = AdvancedMotionAnalyzer(fps=fps)

    def calculate_angle(self, a: np.ndarray, b: np.ndarray, c: np.ndarray) -> float:
        """计算三点角度（a-b-c，单位：度）"""
        try:
            ba = np.array([a[0] - b[0], a[1] - b[1]])
            bc = np.array([c[0] - b[0], c[1] - b[1]])
            cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
            angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
            return float(np.degrees(angle))
        except:
            return 0.0

    def calculate_line_angle(self, point1: np.ndarray, point2: np.ndarray) -> float:
        """计算线段与水平线的夹角（-180到180度）"""
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        angle = math.degrees(math.atan2(dy, dx))
        return angle

    def calculate_velocity(self, history: List[np.ndarray]) -> float:
        """计算速度（米/秒）"""
        if len(history) < 2:
            return 0.0
        prev_point = history[-2]
        curr_point = history[-1]
        dx = curr_point[0] - prev_point[0]
        dy = curr_point[1] - prev_point[1]
        distance_pixels = math.sqrt(dx**2 + dy**2)
        # 像素到米的转换 * 1000 是因为坐标是归一化的
        distance_meters = distance_pixels * self.pixels_to_meters * 1000
        velocity = distance_meters / self.dt
        return velocity

    def analyze_hip_rotation(self, landmarks: np.ndarray) -> Dict:
        """分析胯部/双腿扭转角度"""
        left_hip = landmarks[KEYPOINTS["left_hip"]]
        right_hip = landmarks[KEYPOINTS["right_hip"]]
        left_knee = landmarks[KEYPOINTS["left_knee"]]
        right_knee = landmarks[KEYPOINTS["right_knee"]]
        left_ankle = landmarks[KEYPOINTS["left_ankle"]]
        right_ankle = landmarks[KEYPOINTS["right_ankle"]]

        # 髋线角度
        hip_line_angle = self.calculate_line_angle(left_hip, right_hip)

        # 左腿角度（髋-膝-踝）
        left_leg_angle = self.calculate_angle(left_hip, left_knee, left_ankle)

        # 右腿角度
        right_leg_angle = self.calculate_angle(right_hip, right_knee, right_ankle)

        # 胯部深度差（前后位置差）
        hip_depth_diff = (left_hip[2] - right_hip[2]) * 1000

        return {
            'hip_line_angle': round(hip_line_angle, 2),
            'left_leg_angle': round(left_leg_angle, 2),
            'right_leg_angle': round(right_leg_angle, 2),
            'hip_depth_diff': round(hip_depth_diff, 2),
            'hip_rotation_amplitude': round(abs(hip_depth_diff), 2)
        }

    def analyze_torso_twist(self, landmarks: np.ndarray) -> Dict:
        """分析身体扭转角度（肩部vs髋部）"""
        left_shoulder = landmarks[KEYPOINTS["left_shoulder"]]
        right_shoulder = landmarks[KEYPOINTS["right_shoulder"]]
        left_hip = landmarks[KEYPOINTS["left_hip"]]
        right_hip = landmarks[KEYPOINTS["right_hip"]]

        # 肩线角度
        shoulder_line_angle = self.calculate_line_angle(left_shoulder, right_shoulder)

        # 髋线角度
        hip_line_angle = self.calculate_line_angle(left_hip, right_hip)

        # 身体扭转角度（肩线与髋线的夹角）
        torso_twist_angle = shoulder_line_angle - hip_line_angle

        # 肩部深度差
        shoulder_depth_diff = (left_shoulder[2] - right_shoulder[2]) * 1000

        return {
            'shoulder_line_angle': round(shoulder_line_angle, 2),
            'hip_line_angle': round(hip_line_angle, 2),
            'torso_twist_angle': round(torso_twist_angle, 2),
            'shoulder_depth_diff': round(shoulder_depth_diff, 2)
        }

    def analyze_swing(self, landmarks: np.ndarray, wrist_velocity: float) -> Dict:
        """分析挥棒数据：速度和轨迹"""
        # 使用手腕位置作为挥棒参考点
        # 优先使用右手腕，如果不可用则使用左手腕
        right_wrist = landmarks[KEYPOINTS["right_wrist"]]
        left_wrist = landmarks[KEYPOINTS["left_wrist"]]
        
        # 选择可见的手腕
        if right_wrist[0] > 0 and right_wrist[1] > 0:
            wrist_pos = right_wrist
            wrist_idx = "right"
        elif left_wrist[0] > 0 and left_wrist[1] > 0:
            wrist_pos = left_wrist
            wrist_idx = "left"
        else:
            return {
                'bat_speed_ms': 0.0,
                'bat_speed_km_h': 0.0,
                'wrist_speed_ms': wrist_velocity,
                'trajectory_point': None
            }
        
        # 计算棒头速度（手腕速度 + 棒长带来的额外速度）
        # 假设棒绕手腕旋转，棒头速度 = 手腕速度 + 角速度 × 棒长
        # 简化计算：棒头速度 ≈ 手腕速度 × (1 + 棒长/手臂长度)
        arm_length = 0.7  # 估算手臂长度（米）
        bat_speed_multiplier = 1 + BAT_LENGTH_METERS / arm_length
        bat_speed = wrist_velocity * bat_speed_multiplier
        
        # 记录轨迹点
        trajectory_point = {
            'x': float(wrist_pos[0]),
            'y': float(wrist_pos[1]),
            'z': float(wrist_pos[2]),
            'timestamp': len(self.swing_trajectory_points) * self.dt
        }
        self.swing_trajectory_points.append(trajectory_point)
        
        # 记录速度历史
        self.bat_speed_history.append(bat_speed)
        
        return {
            'bat_speed_ms': round(bat_speed, 2),
            'bat_speed_km_h': round(bat_speed * 3.6, 2),
            'wrist_speed_ms': round(wrist_velocity, 2),
            'wrist_side': wrist_idx,
            'trajectory_point': trajectory_point
        }

    def analyze_frame(self, result: DetectionResult, frame_number: int) -> Optional[MotionFrameData]:
        """分析单帧，返回所有运动参数"""
        if result.pose_landmarks is None:
            return None

        landmarks = result.pose_landmarks

        # 检查关键点是否有效
        if len(landmarks) < 33:
            return None

        # 手臂分析
        left_shoulder = landmarks[KEYPOINTS["left_shoulder"]]
        left_elbow = landmarks[KEYPOINTS["left_elbow"]]
        left_wrist = landmarks[KEYPOINTS["left_wrist"]]
        right_shoulder = landmarks[KEYPOINTS["right_shoulder"]]
        right_elbow = landmarks[KEYPOINTS["right_elbow"]]
        right_wrist = landmarks[KEYPOINTS["right_wrist"]]

        left_elbow_angle = self.calculate_angle(left_shoulder, left_elbow, left_wrist)
        right_elbow_angle = self.calculate_angle(right_shoulder, right_elbow, right_wrist)

        # 计算手腕速度
        self.left_wrist_history.append(left_wrist)
        self.right_wrist_history.append(right_wrist)

        left_wrist_velocity = self.calculate_velocity(self.left_wrist_history)
        right_wrist_velocity = self.calculate_velocity(self.right_wrist_history)
        
        # 使用较大的手腕速度作为挥棒参考
        max_wrist_velocity = max(left_wrist_velocity, right_wrist_velocity)

        # 腿部和身体分析
        hip_data = self.analyze_hip_rotation(landmarks)
        torso_data = self.analyze_torso_twist(landmarks)
        
        # 挥棒分析
        swing_data = self.analyze_swing(landmarks, max_wrist_velocity)

        # 保存到历史
        self.hip_angle_history.append(hip_data['hip_rotation_amplitude'])
        self.torso_twist_history.append(abs(torso_data['torso_twist_angle']))

        motion_data = {
            'arms': {
                'left_elbow_angle': round(left_elbow_angle, 2),
                'right_elbow_angle': round(right_elbow_angle, 2),
                'left_wrist_velocity': round(left_wrist_velocity, 2),
                'right_wrist_velocity': round(right_wrist_velocity, 2),
            },
            'hips': hip_data,
            'torso': torso_data,
            'swing': swing_data
        }

        frame_data = MotionFrameData(
            frame_number=frame_number,
            timestamp_ms=int(result.timestamp * 1000),
            timestamp_sec=result.timestamp,
            **motion_data
        )

        self.all_frames_data.append(frame_data)
        return frame_data

    def generate_raw_data(self) -> Dict:
        """
        生成原始分析数据（不包含评估）
        包含基础数据和高级分析数据

        Returns:
            原始数据字典，包含 arm_max_velocities, bat_speed, swing_trajectory, leg_analysis, torso_analysis
            以及高级分析数据：velocity_analysis, joint_analysis, symmetry_analysis, 
            action_phases, trajectory_smoothness, power_transfer
        """
        valid_frames = self.all_frames_data

        if not valid_frames:
            return {
                'error': '没有有效的骨架数据'
            }

        # 提取所有数据
        all_left_vel = [d.arms['left_wrist_velocity'] for d in valid_frames]
        all_right_vel = [d.arms['right_wrist_velocity'] for d in valid_frames]
        all_hip_rot = [d.hips['hip_rotation_amplitude'] for d in valid_frames]
        all_torso_twist = [d.torso['torso_twist_angle'] for d in valid_frames]
        all_torso_twist_abs = [abs(x) for x in all_torso_twist]

        # 挥棒数据
        all_bat_speeds = [d.swing.get('bat_speed_ms', 0) for d in valid_frames if d.swing.get('bat_speed_ms', 0) > 0]
        
        # 综合手腕速度（用于高级分析）
        combined_wrist_vel = [max(l, r) for l, r in zip(all_left_vel, all_right_vel)]

        # 1. 双手臂最大速度
        max_left_speed = max(all_left_vel) if all_left_vel else 0
        max_right_speed = max(all_right_vel) if all_right_vel else 0

        # 2. 挥棒速度分析
        max_bat_speed = max(all_bat_speeds) if all_bat_speeds else 0
        avg_bat_speed = np.mean(all_bat_speeds) if all_bat_speeds else 0

        # 3. 双腿扭转角度统计
        max_hip_rotation = max(all_hip_rot) if all_hip_rot else 0
        avg_hip_rotation = np.mean(all_hip_rot) if all_hip_rot else 0
        hip_rotation_std = np.std(all_hip_rot) if all_hip_rot else 0

        # 4. 身体扭转角度统计
        max_torso_twist = max(all_torso_twist_abs) if all_torso_twist_abs else 0
        avg_torso_twist = np.mean(all_torso_twist_abs) if all_torso_twist_abs else 0

        # 5. 挥棒轨迹分析
        swing_trajectory = self.analyze_swing_trajectory()
        
        # ========== 高级分析 ==========
        
        # 6. 速度曲线分析
        velocity_analysis = self.advanced_analyzer.analyze_velocity_curve(combined_wrist_vel)
        
        # 7. 关节角度分析
        frames_data_dicts = [asdict(f) for f in valid_frames]
        joint_analysis = self.advanced_analyzer.analyze_joint_angles(frames_data_dicts)
        
        # 8. 身体对称性分析
        symmetry_analysis = self.advanced_analyzer.analyze_body_symmetry(frames_data_dicts)
        
        # 9. 动作阶段检测
        action_phases = self.advanced_analyzer.detect_action_phases(combined_wrist_vel)
        
        # 10. 轨迹平滑度分析
        trajectory_smoothness = self.advanced_analyzer.analyze_trajectory_smoothness(
            self.swing_trajectory_points
        )
        
        # 11. 能量传递效率分析
        power_transfer = self.advanced_analyzer.calculate_power_transfer_efficiency(frames_data_dicts)

        return {
            # 基础数据
            'arm_max_velocities': {
                'left_m_s': round(max_left_speed, 2),
                'right_m_s': round(max_right_speed, 2),
                'left_km_h': round(max_left_speed * 3.6, 2),
                'right_km_h': round(max_right_speed * 3.6, 2)
            },
            'bat_speed': {
                'max_m_s': round(max_bat_speed, 2),
                'max_km_h': round(max_bat_speed * 3.6, 2),
                'avg_m_s': round(avg_bat_speed, 2),
                'avg_km_h': round(avg_bat_speed * 3.6, 2)
            },
            'swing_trajectory': swing_trajectory,
            'leg_analysis': {
                'max_hip_rotation_mm': round(max_hip_rotation, 2),
                'avg_hip_rotation_mm': round(avg_hip_rotation, 2),
                'hip_stability': round(hip_rotation_std, 2)
            },
            'torso_analysis': {
                'max_twist_angle_deg': round(max_torso_twist, 2),
                'avg_twist_angle_deg': round(avg_torso_twist, 2),
                'shoulder_hip_diff_deg': round(max_torso_twist, 2)
            },
            # 高级分析数据
            'velocity_analysis': velocity_analysis,
            'joint_analysis': joint_analysis,
            'symmetry_analysis': symmetry_analysis,
            'action_phases': action_phases,
            'trajectory_smoothness': trajectory_smoothness,
            'power_transfer': power_transfer
        }

    def analyze_swing_trajectory(self) -> Dict:
        """分析挥棒轨迹"""
        if len(self.swing_trajectory_points) < 2:
            return {
                'total_points': 0,
                'path_length': 0,
                'start_point': None,
                'end_point': None,
                'trajectory_type': 'unknown'
            }
        
        # 计算轨迹总长度
        total_length = 0
        for i in range(1, len(self.swing_trajectory_points)):
            p1 = self.swing_trajectory_points[i-1]
            p2 = self.swing_trajectory_points[i]
            dx = p2['x'] - p1['x']
            dy = p2['y'] - p1['y']
            total_length += math.sqrt(dx*dx + dy*dy)
        
        # 计算起点和终点
        start_point = self.swing_trajectory_points[0]
        end_point = self.swing_trajectory_points[-1]
        
        # 计算直线距离
        direct_distance = math.sqrt(
            (end_point['x'] - start_point['x'])**2 + 
            (end_point['y'] - start_point['y'])**2
        )
        
        # 判断轨迹类型
        # 如果轨迹长度远大于直线距离，说明是弧形轨迹
        path_ratio = total_length / (direct_distance + 1e-6)
        if path_ratio > 1.5:
            trajectory_type = 'arc'  # 弧形轨迹
        elif path_ratio > 1.2:
            trajectory_type = 'slight_curve'  # 轻微弧线
        else:
            trajectory_type = 'straight'  # 接近直线
        
        # 计算挥棒方向（从起点到终点的角度）
        dx = end_point['x'] - start_point['x']
        dy = end_point['y'] - start_point['y']
        swing_angle = math.degrees(math.atan2(dy, dx))
        
        return {
            'total_points': len(self.swing_trajectory_points),
            'path_length': round(total_length, 4),
            'direct_distance': round(direct_distance, 4),
            'path_ratio': round(path_ratio, 2),
            'start_point': {'x': start_point['x'], 'y': start_point['y']},
            'end_point': {'x': end_point['x'], 'y': end_point['y']},
            'swing_angle_deg': round(swing_angle, 2),
            'trajectory_type': trajectory_type,
            'trajectory_data': self.swing_trajectory_points  # 完整轨迹数据
        }

    def export_to_json(self, video_path: str, fps: int, width: int, height: int, total_frames: int) -> Dict:
        """导出完整的 JSON 分析结果（仅原始数据）"""
        raw_data = self.generate_raw_data()

        output_data = {
            'metadata': {
                'fps': fps,
                'resolution': {'width': width, 'height': height},
                'total_frames': total_frames,
                'analysis_date': datetime.now().isoformat()
            },
            'raw_data': raw_data
        }

        return output_data

    def detect_action_start_end(self, threshold_velocity: float = 5.0) -> Tuple[float, float]:
        """检测动作的起始和结束时间"""
        if not self.all_frames_data:
            return 0.0, 0.0

        velocities = [
            max(frame.arms['left_wrist_velocity'], frame.arms['right_wrist_velocity'])
            for frame in self.all_frames_data
        ]

        # 找到开始动作的帧
        start_idx = 0
        for i, vel in enumerate(velocities):
            if vel > threshold_velocity:
                start_idx = i
                break

        # 找到动作结束的帧
        end_idx = len(velocities)
        for i in range(len(velocities) - 1, -1, -1):
            if velocities[i] > threshold_velocity:
                end_idx = i + 1
                break

        start_time = self.all_frames_data[start_idx].timestamp_sec if start_idx < len(self.all_frames_data) else 0
        end_time = self.all_frames_data[min(end_idx, len(self.all_frames_data) - 1)].timestamp_sec if self.all_frames_data else 0

        return start_time, end_time