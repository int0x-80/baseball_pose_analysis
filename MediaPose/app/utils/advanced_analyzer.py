"""
高级动作分析模块
使用 scipy 和 pandas 进行更深入的运动学分析
"""
import numpy as np
from scipy import signal, interpolate
from scipy.ndimage import gaussian_filter1d
import pandas as pd
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class AdvancedMotionAnalyzer:
    """高级运动分析器"""
    
    def __init__(self, fps: int = 30):
        self.fps = fps
        self.dt = 1.0 / fps
        
    def analyze_velocity_curve(self, velocities: List[float]) -> Dict:
        """
        分析速度曲线
        
        Returns:
            包含峰值、加速度、平滑度等指标
        """
        if len(velocities) < 3:
            return {
                'peak_velocity': 0.0,
                'peak_time': 0.0,
                'max_acceleration': 0.0,
                'max_deceleration': 0.0,
                'smoothness': 0.0,
                'velocity_profile': 'unknown'
            }
        
        # 转换为 numpy 数组
        vel_array = np.array(velocities)
        
        # 平滑处理（高斯滤波）
        smoothed_vel = gaussian_filter1d(vel_array, sigma=2)
        
        # 找峰值
        peak_idx = np.argmax(smoothed_vel)
        peak_velocity = float(smoothed_vel[peak_idx])
        peak_time = peak_idx * self.dt
        
        # 计算加速度
        acceleration = np.gradient(smoothed_vel, self.dt)
        max_acceleration = float(np.max(acceleration))
        max_deceleration = float(np.min(acceleration))
        
        # 计算平滑度（加速度的标准差，越小越平滑）
        smoothness = float(np.std(acceleration))
        
        # 判断速度曲线类型
        velocity_profile = self._classify_velocity_profile(smoothed_vel, peak_idx)
        
        return {
            'peak_velocity': round(peak_velocity, 2),
            'peak_velocity_km_h': round(peak_velocity * 3.6, 2),
            'peak_time_sec': round(peak_time, 3),
            'max_acceleration': round(max_acceleration, 2),
            'max_deceleration': round(max_deceleration, 2),
            'smoothness': round(smoothness, 2),
            'velocity_profile': velocity_profile,
            'velocity_curve': smoothed_vel.tolist()  # 平滑后的速度曲线
        }
    
    def _classify_velocity_profile(self, velocities: np.ndarray, peak_idx: int) -> str:
        """分类速度曲线类型"""
        if len(velocities) < 10:
            return 'unknown'
        
        # 计算加速阶段和减速阶段的比例
        accel_phase = peak_idx / len(velocities)
        
        if accel_phase < 0.3:
            return 'explosive'  # 爆发型（快速加速）
        elif accel_phase < 0.5:
            return 'balanced'  # 平衡型
        else:
            return 'gradual'  # 渐进型
    
    def analyze_joint_angles(self, frames_data: List[Dict]) -> Dict:
        """
        分析关节角度变化
        
        Returns:
            关节角度范围、变化率、流畅性指标
        """
        if not frames_data:
            return {}
        
        # 提取各关节角度
        left_elbow_angles = [f['arms']['left_elbow_angle'] for f in frames_data if f['arms']['left_elbow_angle'] > 0]
        right_elbow_angles = [f['arms']['right_elbow_angle'] for f in frames_data if f['arms']['right_elbow_angle'] > 0]
        
        result = {}
        
        # 左肘分析
        if left_elbow_angles:
            result['left_elbow'] = {
                'min_angle': round(min(left_elbow_angles), 2),
                'max_angle': round(max(left_elbow_angles), 2),
                'range': round(max(left_elbow_angles) - min(left_elbow_angles), 2),
                'avg_angle': round(np.mean(left_elbow_angles), 2)
            }
        
        # 右肘分析
        if right_elbow_angles:
            result['right_elbow'] = {
                'min_angle': round(min(right_elbow_angles), 2),
                'max_angle': round(max(right_elbow_angles), 2),
                'range': round(max(right_elbow_angles) - min(right_elbow_angles), 2),
                'avg_angle': round(np.mean(right_elbow_angles), 2)
            }
        
        return result
    
    def analyze_body_symmetry(self, frames_data: List[Dict]) -> Dict:
        """
        分析身体对称性
        
        Returns:
            左右侧速度差异、角度差异等
        """
        if not frames_data:
            return {}
        
        left_velocities = [f['arms']['left_wrist_velocity'] for f in frames_data]
        right_velocities = [f['arms']['right_wrist_velocity'] for f in frames_data]
        
        # 计算平均速度
        avg_left = np.mean(left_velocities) if left_velocities else 0
        avg_right = np.mean(right_velocities) if right_velocities else 0
        
        # 计算最大速度
        max_left = max(left_velocities) if left_velocities else 0
        max_right = max(right_velocities) if right_velocities else 0
        
        # 计算对称性指标（0-100，100为完全对称）
        if avg_left > 0 or avg_right > 0:
            avg_symmetry = 100 - (abs(avg_left - avg_right) / max(avg_left, avg_right, 1)) * 100
            max_symmetry = 100 - (abs(max_left - max_right) / max(max_left, max_right, 1)) * 100
        else:
            avg_symmetry = 0
            max_symmetry = 0
        
        return {
            'left_avg_velocity': round(float(avg_left), 2),
            'right_avg_velocity': round(float(avg_right), 2),
            'left_max_velocity': round(float(max_left), 2),
            'right_max_velocity': round(float(max_right), 2),
            'avg_symmetry_score': round(float(avg_symmetry), 2),
            'max_symmetry_score': round(float(max_symmetry), 2),
            'dominant_side': 'left' if avg_left > avg_right else 'right'
        }
    
    def detect_action_phases(self, velocities: List[float], threshold_ratio: float = 0.3) -> Dict:
        """
        检测动作阶段（准备、挥棒、跟随）
        
        Args:
            velocities: 速度序列
            threshold_ratio: 阈值比例（相对于最大速度）
        """
        if len(velocities) < 10:
            return {
                'phases': [],
                'total_duration': 0.0
            }
        
        max_vel = max(velocities)
        threshold = max_vel * threshold_ratio
        
        # 找到动作开始和结束
        action_start = 0
        action_end = len(velocities) - 1
        
        for i, vel in enumerate(velocities):
            if vel > threshold:
                action_start = i
                break
        
        for i in range(len(velocities) - 1, -1, -1):
            if velocities[i] > threshold:
                action_end = i
                break
        
        # 找到速度峰值
        peak_idx = velocities.index(max_vel)
        
        # 划分阶段
        phases = []
        
        # 准备阶段
        if action_start < peak_idx:
            phases.append({
                'name': 'preparation',
                'start_frame': action_start,
                'end_frame': peak_idx,
                'start_time': round(action_start * self.dt, 3),
                'end_time': round(peak_idx * self.dt, 3),
                'duration': round((peak_idx - action_start) * self.dt, 3)
            })
        
        # 挥棒阶段（峰值前后各一段时间）
        swing_start = max(action_start, peak_idx - int(len(velocities) * 0.1))
        swing_end = min(action_end, peak_idx + int(len(velocities) * 0.1))
        
        phases.append({
            'name': 'swing',
            'start_frame': swing_start,
            'end_frame': swing_end,
            'start_time': round(swing_start * self.dt, 3),
            'end_time': round(swing_end * self.dt, 3),
            'duration': round((swing_end - swing_start) * self.dt, 3),
            'peak_time': round(peak_idx * self.dt, 3)
        })
        
        # 跟随阶段
        if swing_end < action_end:
            phases.append({
                'name': 'follow_through',
                'start_frame': swing_end,
                'end_frame': action_end,
                'start_time': round(swing_end * self.dt, 3),
                'end_time': round(action_end * self.dt, 3),
                'duration': round((action_end - swing_end) * self.dt, 3)
            })
        
        return {
            'phases': phases,
            'total_duration': round((action_end - action_start) * self.dt, 3),
            'action_start_frame': action_start,
            'action_end_frame': action_end,
            'peak_frame': peak_idx
        }
    
    def analyze_trajectory_smoothness(self, trajectory_points: List[Dict]) -> Dict:
        """
        分析轨迹平滑度
        
        Returns:
            平滑度指标、曲率变化等
        """
        if len(trajectory_points) < 5:
            return {
                'smoothness_score': 0,
                'curvature_variance': 0,
                'is_smooth': False
            }
        
        # 提取 x, y 坐标
        x_coords = np.array([p['x'] for p in trajectory_points])
        y_coords = np.array([p['y'] for p in trajectory_points])
        
        # 计算曲率（简化版：使用二阶导数）
        dx = np.gradient(x_coords)
        dy = np.gradient(y_coords)
        ddx = np.gradient(dx)
        ddy = np.gradient(dy)
        
        # 曲率 = |x'y'' - y'x''| / (x'^2 + y'^2)^(3/2)
        numerator = np.abs(dx * ddy - dy * ddx)
        denominator = (dx**2 + dy**2)**1.5 + 1e-6
        curvature = numerator / denominator
        
        # 计算曲率的标准差（越小越平滑）
        curvature_std = float(np.std(curvature))
        
        # 平滑度评分（0-100）
        smoothness_score = max(0, 100 - curvature_std * 1000)
        
        return {
            'smoothness_score': round(smoothness_score, 2),
            'curvature_variance': round(curvature_std, 4),
            'max_curvature': round(float(np.max(curvature)), 4),
            'avg_curvature': round(float(np.mean(curvature)), 4),
            'is_smooth': smoothness_score > 70
        }
    
    def calculate_power_transfer_efficiency(self, frames_data: List[Dict]) -> Dict:
        """
        计算能量传递效率
        
        分析从腿部->躯干->手臂的能量传递链
        """
        if len(frames_data) < 10:
            return {
                'efficiency_score': 0,
                'kinetic_chain_quality': 'unknown'
            }
        
        # 提取各部位的速度/角度变化
        hip_rotations = [f['hips']['hip_rotation_amplitude'] for f in frames_data]
        torso_twists = [abs(f['torso']['torso_twist_angle']) for f in frames_data]
        wrist_velocities = [max(f['arms']['left_wrist_velocity'], f['arms']['right_wrist_velocity']) for f in frames_data]
        
        # 找到各部位的峰值时间
        hip_peak_idx = hip_rotations.index(max(hip_rotations)) if hip_rotations else 0
        torso_peak_idx = torso_twists.index(max(torso_twists)) if torso_twists else 0
        wrist_peak_idx = wrist_velocities.index(max(wrist_velocities)) if wrist_velocities else 0
        
        # 检查时序是否正确（髋部->躯干->手腕）
        timing_correct = hip_peak_idx <= torso_peak_idx <= wrist_peak_idx
        
        # 计算时序得分
        if timing_correct:
            timing_score = 100
        else:
            # 时序错误，根据偏差扣分
            deviation = abs(hip_peak_idx - torso_peak_idx) + abs(torso_peak_idx - wrist_peak_idx)
            timing_score = max(0, 100 - deviation * 10)
        
        # 计算整体效率得分
        efficiency_score = timing_score * 0.7 + 30  # 基础分30
        
        # 判断动力链质量
        if efficiency_score >= 80:
            quality = 'excellent'
        elif efficiency_score >= 60:
            quality = 'good'
        elif efficiency_score >= 40:
            quality = 'fair'
        else:
            quality = 'poor'
        
        return {
            'efficiency_score': round(efficiency_score, 2),
            'kinetic_chain_quality': quality,
            'timing_correct': timing_correct,
            'hip_peak_time': round(hip_peak_idx * self.dt, 3),
            'torso_peak_time': round(torso_peak_idx * self.dt, 3),
            'wrist_peak_time': round(wrist_peak_idx * self.dt, 3)
        }
