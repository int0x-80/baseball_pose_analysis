"""
视频处理模块 - 简化版（仅用于测试）
"""
import cv2
from typing import Tuple


class VideoProcessor:
    """视频处理器"""

    @staticmethod
    def get_video_info(video_path: str) -> Tuple[int, float, Tuple[int, int]]:
        """获取视频信息

        Returns:
            (fps, duration, (width, height))
        """
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        duration = frame_count / fps if fps > 0 else 0
        return fps, duration, (width, height)