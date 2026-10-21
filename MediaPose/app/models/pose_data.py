"""
姿态数据和动作分析结果模型
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
import numpy as np


class ActionType(str, Enum):
    """动作类型"""
    BATTING = "batting"  # 击球
    PITCHING = "pitching"  # 投球


class Landmark(BaseModel):
    """单个关键点"""
    x: float = Field(..., ge=0, le=1)
    y: float = Field(..., ge=0, le=1)
    z: float = Field(default=0)
    visibility: float = Field(default=1.0, ge=0, le=1)

    @classmethod
    def from_mediapipe(cls, landmark):
        """从 MediaPipe Landmark 转换"""
        return cls(
            x=landmark.x,
            y=landmark.y,
            z=landmark.z if hasattr(landmark, 'z') else 0,
            visibility=landmark.visibility if hasattr(landmark, 'visibility') else 1.0
        )


class PoseLandmarks(BaseModel):
    """全身骨骼关键点 (33个)"""
    landmarks: List[Landmark] = Field(default_factory=list)

    @classmethod
    def from_mediapipe(cls, pose_landmarks):
        """从 MediaPipe PoseLandmarks 转换"""
        return cls(
            landmarks=[
                Landmark.from_mediapipe(lm) for lm in pose_landmarks.landmark
            ]
        )


class HandLandmarks(BaseModel):
    """手部骨骼关键点 (21个)"""
    handedness: str  # "left" 或 "right"
    landmarks: List[Landmark] = Field(default_factory=list)

    @classmethod
    def from_mediapipe(cls, hand_landmarks, handedness):
        return cls(
            handedness=handedness,
            landmarks=[
                Landmark.from_mediapipe(lm) for lm in hand_landmarks.landmark
            ]
        )


class SwingData(BaseModel):
    """挥动数据"""
    hand: str  # "left" 或 "right"
    max_speed: float  # 最大速度 (m/s)
    avg_speed: float  # 平均速度
    peak_time: float  # 峰值时间 (秒)
    trajectory: List[Dict[str, float]]  # 轨迹点序列


class BodyTwist(BaseModel):
    """身体扭转数据"""
    max_twist_angle: float  # 最大扭转角度 (度)
    avg_twist_angle: float  # 平均扭转角度
    twist_timeline: List[float]  # 扭转角度时间序列


class ActionScore(BaseModel):
    """动作评分"""
    overall_score: float = Field(..., ge=0, le=100)
    speed_score: float = Field(..., ge=0, le=100)
    angle_score: float = Field(..., ge=0, le=100)
    consistency_score: float = Field(..., ge=0, le=100)
    suggestions: List[str] = Field(default_factory=list)


class VideoAnalysisResult(BaseModel):
    """视频分析结果"""
    video_id: str
    action_type: ActionType
    duration: float  # 视频时长 (秒)
    frame_count: int
    fps: int

    # 姿态数据
    pose_landmarks: Optional[List[PoseLandmarks]] = None
    hand_landmarks: Optional[List[List[HandLandmarks]]] = None

    # 动作分析数据
    left_swing: Optional[SwingData] = None
    right_swing: Optional[SwingData] = None
    body_twist: Optional[BodyTwist] = None

    # 动作评分
    action_score: Optional[ActionScore] = None

    # 视频输出
    processed_video_path: Optional[str] = None  # 带骨骼的视频
    clip_paths: List[str] = Field(default_factory=list)  # 动作片段视频

    # 元数据
    created_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ClipRequest(BaseModel):
    """视频片段裁剪请求"""
    video_id: str
    start_time: float
    end_time: float
    output_name: Optional[str] = None


class ConsistencyAnalysis(BaseModel):
    """一致性分析结果"""
    comparison_id: str
    video_ids: List[str]  # 比较的视频ID列表
    speed_consistency: float  # 速度一致性分数 (0-100)
    angle_consistency: float  # 角度一致性分数
    trajectory_similarity: float  # 轨迹相似度分数
    overall_consistency: float  # 总体一致性分数
    details: Dict[str, Any] = Field(default_factory=dict)