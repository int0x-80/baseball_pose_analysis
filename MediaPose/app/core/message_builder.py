"""
消息格式构建器
对齐 Java 端消息格式
"""
import time
from typing import Dict, Any, Optional


def build_analysis_completed_message(
    message_id: str,
    record_id: str,
    user_id: int,
    video_metadata: Dict[str, Any],
    analysis_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    构建分析完成消息，对齐 Java 端 AnalysisCompletedMessage

    Args:
        message_id: 消息ID
        record_id: 记录ID
        user_id: 用户ID
        video_metadata: VideoMetadata 对象
        analysis_result: VideoAnalysisResult 对象

    Returns:
        符合 Java AnalysisCompletedMessage 格式的消息字典
    """
    return {
        'messageId': message_id,
        'recordId': record_id,
        'userId': user_id,
        'status': 'COMPLETED',
        'videoMetadata': video_metadata,
        'analysisResult': analysis_result,
        'timestamp': int(time.time() * 1000)
    }


def build_analysis_failed_message(
    message_id: str,
    record_id: str,
    user_id: int,
    error: str,
    error_code: str = 'ANALYSIS_ERROR'
) -> Dict[str, Any]:
    """
    构建分析失败消息，对齐 Java 端 AnalysisFailedMessage

    Args:
        message_id: 消息ID
        record_id: 记录ID
        user_id: 用户ID
        error: 错误信息
        error_code: 错误码

    Returns:
        符合 Java AnalysisFailedMessage 格式的消息字典
    """
    return {
        'messageId': message_id,
        'recordId': record_id,
        'userId': user_id,
        'status': 'FAILED',
        'error': error,
        'errorCode': error_code,
        'timestamp': int(time.time() * 1000)
    }
