"""
挥棒片段裁剪工具
从完整视频中截取一次完整击球过程（STANCE → FOLLOW_THROUGH），
前后各加缓冲帧，过滤掉无关片段。

输出：独立的挥棒片段 MP4 视频
"""
import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import subprocess
import os
import logging

from .phase_detector import PhaseBoundary, SwingPhase

logger = logging.getLogger(__name__)

# 前后缓冲帧数（秒数 × fps）
BUFFER_SECONDS_BEFORE = 0.5
BUFFER_SECONDS_AFTER = 0.8


class BattingClipExtractor:
    """
    击球片段裁剪器

    使用方式：
        extractor = BattingClipExtractor(fps=30)
        clip_info = extractor.extract_clip(video_path, output_path, boundaries)
    """

    def __init__(self, fps: int = 30):
        self.fps = fps
        self.buffer_before = int(BUFFER_SECONDS_BEFORE * fps)
        self.buffer_after = int(BUFFER_SECONDS_AFTER * fps)

    def compute_clip_range(
        self,
        boundaries: List[PhaseBoundary],
        total_frames: int,
    ) -> Optional[Tuple[int, int]]:
        """
        根据阶段边界计算裁剪帧范围

        Args:
            boundaries: 阶段边界列表
            total_frames: 视频总帧数

        Returns:
            (start_frame, end_frame) 或 None（无有效阶段时）
        """
        if not boundaries:
            return None

        # 只取第一段完整挥棒（STANCE → FOLLOW_THROUGH）
        swing_end = None
        for b in boundaries:
            if b.phase == SwingPhase.FOLLOW_THROUGH:
                swing_end = b.end_frame
                break

        if swing_end is None:
            # 没有 FOLLOW_THROUGH，退化为所有边界范围
            swing_end = boundaries[-1].end_frame

        swing_start = boundaries[0].start_frame

        # 加缓冲
        start = max(0, swing_start - self.buffer_before)
        end = min(total_frames - 1, swing_end + self.buffer_after)

        if end - start < self.fps * 0.5:
            logger.warning(f"裁剪范围过短 ({end - start} 帧)，跳过")
            return None

        return (start, end)

    def extract_clip(
        self,
        video_path: str,
        output_path: str,
        boundaries: List[PhaseBoundary],
        total_frames: int = 0,
    ) -> Optional[Dict]:
        """
        从视频中提取完整挥棒片段

        Args:
            video_path: 原始视频路径
            output_path: 输出片段路径 (.mp4)
            boundaries: 阶段边界列表
            total_frames: 总帧数（0 则自动检测）

        Returns:
            片段信息字典 或 None
        """
        cap = cv2.VideoCapture(video_path)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        if total_frames == 0:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        clip_range = self.compute_clip_range(boundaries, total_frames)
        if clip_range is None:
            cap.release()
            return None

        start_frame, end_frame = clip_range
        frame_count = end_frame - start_frame + 1

        logger.info(f"裁剪片段: 帧 {start_frame}-{end_frame} ({frame_count}帧, "
                     f"{frame_count/fps:.2f}s)")

        # 用临时 AVI 写入原始帧
        temp_path = output_path + ".tmp.avi"
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        writer = cv2.VideoWriter(temp_path, fourcc, fps, (width, height))

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        frames_written = 0

        for frame_idx in range(start_frame, end_frame + 1):
            ret, frame = cap.read()
            if not ret:
                break
            writer.write(frame)
            frames_written += 1

        cap.release()
        writer.release()

        if frames_written == 0:
            logger.error("裁剪片段无有效帧")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None

        # FFmpeg 转 MP4
        try:
            subprocess.run([
                'ffmpeg', '-y', '-i', temp_path,
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                output_path
            ], check=True, capture_output=True)
            os.remove(temp_path)
            logger.info(f"片段视频已保存: {output_path}")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg 裁剪转码失败: {e.stderr.decode()[:200]}")
            if os.path.exists(temp_path):
                os.rename(temp_path, output_path.replace('.mp4', '.avi'))

        # 计算阶段在片段视频中的相对位置
        phase_markers = []
        for b in boundaries:
            rel_start = max(0, b.start_frame - start_frame)
            rel_end = min(frames_written - 1, b.end_frame - start_frame)
            phase_markers.append({
                'phase': b.phase.value,
                'phaseLabelCn': b.phase.label_cn,
                'startFrame': rel_start,
                'endFrame': rel_end,
                'startMs': round(rel_start / fps * 1000, 1),
                'endMs': round(rel_end / fps * 1000, 1),
            })

        return {
            'startFrame': start_frame,
            'endFrame': end_frame,
            'frameCount': frames_written,
            'durationSec': round(frames_written / fps, 2),
            'durationMs': round(frames_written / fps * 1000, 1),
            'fps': fps,
            'resolution': {'width': width, 'height': height},
            'phaseMarkers': phase_markers,
        }
