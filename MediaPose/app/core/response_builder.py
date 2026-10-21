"""
响应格式构建器
对齐 Java 端 BaseResponse<T> 格式
"""
import json
from typing import Dict, Any, Optional, List


def build_success_response(data: Any, message: str = "success") -> Dict[str, Any]:
    return {
        "code": "200",
        "message": message,
        "data": data
    }


def build_fail_response(message: str, code: str = "500", data: Any = None) -> Dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": data
    }


def build_video_metadata(
    user_id: int,
    record_id: str,
    message_id: str,
    video_url: str = "",
    skeleton_video_url: str = "",
    status: int = 0,
    skeleton_video_name: str = "",
    analysis_json_name: str = "",
    fps: int = 0,
    video_width: int = 0,
    video_height: int = 0,
    total_frames: int = 0
) -> Dict[str, Any]:
    return {
        "userId": user_id,
        "recordId": record_id,
        "messageId": message_id,
        "videoUrl": video_url,
        "skeletonVideoUrl": skeleton_video_url,
        "status": status,
        "skeletonVideoName": skeleton_video_name,
        "analysisJsonName": analysis_json_name,
        "fps": fps,
        "videoWidth": video_width,
        "videoHeight": video_height,
        "totalFrames": total_frames
    }


def build_video_analysis_result(
    record_id: str,
    user_id: int,
    action_type: str,
    raw_data: Dict[str, Any],
    batting_report: Optional[Dict] = None,
    keyframe_urls: Optional[List[Dict]] = None,
    clip_info: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    构建 VideoAnalysisResult 对象

    Args:
        record_id: 记录ID
        user_id: 用户ID
        action_type: 动作类型
        raw_data: 原始分析数据（ActionAnalyzerV2 输出）
        batting_report: 击球专项分析报告（BattingAnalyzer 输出）
        keyframe_urls: 关键帧上传信息列表
        clip_info: 挥棒片段裁剪信息
    """
    # 基础分析数据
    data = raw_data.get('raw_data', {})
    arm_velocities = data.get('arm_max_velocities', {})
    bat_speed = data.get('bat_speed', {})
    swing_trajectory = data.get('swing_trajectory', {})
    leg_analysis = data.get('leg_analysis', {})
    torso_analysis = data.get('torso_analysis', {})

    velocity_analysis = data.get('velocity_analysis', {})
    joint_analysis = data.get('joint_analysis', {})
    symmetry_analysis = data.get('symmetry_analysis', {})
    action_phases = data.get('action_phases', {})
    trajectory_smoothness = data.get('trajectory_smoothness', {})
    power_transfer = data.get('power_transfer', {})

    result = {
        "recordId": record_id,
        "userId": user_id,
        "actionType": action_type,

        # 手臂速度
        "leftSpeedMs": arm_velocities.get('left_m_s', 0.0),
        "rightSpeedMs": arm_velocities.get('right_m_s', 0.0),
        "leftSpeedKmH": arm_velocities.get('left_km_h', 0.0),
        "rightSpeedKmH": arm_velocities.get('right_km_h', 0.0),

        # 挥棒速度
        "maxBatSpeedKmH": bat_speed.get('max_km_h', 0.0),
        "avgBatSpeedKmH": bat_speed.get('avg_km_h', 0.0),

        # 轨迹
        "pathLength": swing_trajectory.get('path_length', 0.0),
        "swingAngleDeg": swing_trajectory.get('swing_angle_deg', 0.0),

        # 腿部分析
        "maxHipRotationMm": leg_analysis.get('max_hip_rotation_mm', 0.0),
        "avgHipRotationMm": leg_analysis.get('avg_hip_rotation_mm', 0.0),

        # 躯干分析
        "maxTwistAngleDeg": torso_analysis.get('max_twist_angle_deg', 0.0),
        "avgTwistAngleDeg": torso_analysis.get('avg_twist_angle_deg', 0.0),
        "shoulderHipDiffDeg": torso_analysis.get('shoulder_hip_diff_deg', 0.0),

        # 高级分析数据（JSON 字符串）
        "velocityAnalysis": json.dumps(velocity_analysis, ensure_ascii=False) if velocity_analysis else None,
        "jointAnalysis": json.dumps(joint_analysis, ensure_ascii=False) if joint_analysis else None,
        "symmetryAnalysis": json.dumps(symmetry_analysis, ensure_ascii=False) if symmetry_analysis else None,
        "actionPhases": json.dumps(action_phases, ensure_ascii=False) if action_phases else None,
        "trajectorySmoothness": json.dumps(trajectory_smoothness, ensure_ascii=False) if trajectory_smoothness else None,
        "powerTransfer": json.dumps(power_transfer, ensure_ascii=False) if power_transfer else None,

        # 完整原始数据
        "rawData": json.dumps(data, ensure_ascii=False) if data else None,
    }

    # ===== 击球专项分析数据 =====
    if batting_report:
        contact_speed = batting_report.get('contactSpeed', {})
        bat_traj = batting_report.get('batTrajectory', {})
        batting_metrics = batting_report.get('battingMetrics', {})
        phase_timeline = batting_report.get('phaseTimeline', [])

        # 击球速度（棒头峰值速度）
        result['contactBatSpeedKmH'] = contact_speed.get('speed_kmh', 0.0)
        result['contactBatSpeedMs'] = contact_speed.get('speed_ms', 0.0)

        # 棒头轨迹
        result['batTrajectoryPathLength'] = bat_traj.get('path_length', 0.0)
        result['batTrajectoryEfficiency'] = bat_traj.get('path_efficiency', 0.0)
        result['batTrajectoryPeakSpeedKmH'] = bat_traj.get('peak_speed_kmh', 0.0)

        # 阶段时间线（JSON 字符串）
        result['battingPhaseTimeline'] = json.dumps(phase_timeline, ensure_ascii=False)

        # 各阶段指标（JSON 字符串）
        result['battingMetrics'] = json.dumps(batting_metrics, ensure_ascii=False)

        # 逐帧速度曲线（JSON 字符串）
        bat_speed_curve = batting_report.get('batSpeedCurve', {})
        result['batSpeedCurve'] = json.dumps(bat_speed_curve, ensure_ascii=False)

        # 关键帧
        if keyframe_urls:
            result['battingKeyFrames'] = json.dumps(keyframe_urls, ensure_ascii=False)

    # ===== 挥棒片段裁剪数据 =====
    if clip_info:
        result['swingClipObjectName'] = clip_info.get('objectName', '')
        result['swingClipDurationSec'] = clip_info.get('durationSec', 0.0)
        result['swingClipDurationMs'] = clip_info.get('durationMs', 0.0)
        result['swingClipFrameCount'] = clip_info.get('frameCount', 0)
        result['swingClipStartFrame'] = clip_info.get('startFrame', 0)
        result['swingClipEndFrame'] = clip_info.get('endFrame', 0)
        # 阶段在片段中的相对位置标记
        phase_markers = clip_info.get('phaseMarkers', [])
        if phase_markers:
            result['swingClipPhaseMarkers'] = json.dumps(phase_markers, ensure_ascii=False)

    return result
