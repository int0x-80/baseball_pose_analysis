#!/usr/bin/env python3
"""
MediaPose RabbitMQ 消费者
从 analysis-request 队列接收视频分析请求，执行姿态分析后将结果发布到 analysis-completed 队列
"""
import json
import logging
import sys
import time
import uuid
import urllib.request
from pathlib import Path

import cv2

from app.core.config import settings
from app.core.pose_detector import PoseDetector
from app.utils.action_analyzer_v2 import ActionAnalyzerV2
from app.core.message_builder import build_analysis_result, build_analysis_failed
from app.core.storage_client import storage_client
from .rabbitmq_client import RabbitMQClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_video(url: str, save_path: Path) -> Path:
    """从 URL 下载视频文件到本地"""
    logger.info(f"正在下载视频: {url}")
    urllib.request.urlretrieve(url, str(save_path))
    logger.info(f"视频已下载到: {save_path}")
    return save_path


def analyze_video(video_path: Path) -> dict:
    """
    执行视频姿态分析

    Args:
        video_path: 视频文件路径

    Returns:
        final_analysis 字典
    """
    output_video_path = settings.OUTPUT_DIR / f"{video_path.stem}_skeleton.mp4"

    detector = PoseDetector()

    cap = cv2.VideoCapture(str(video_path))
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    cap.release()

    results, _, trajectory = detector.process_video(str(video_path), str(output_video_path))
    detector.cleanup()

    analyzer = ActionAnalyzerV2(fps=fps, pixels_to_meters=0.002)
    for frame_idx, result in enumerate(results):
        analyzer.analyze_frame(result, frame_idx + 1)

    raw_data = analyzer.generate_raw_data()
    return raw_data


def process_request(ch, method, properties, body):
    """
    处理分析请求的回调函数
    """
    request_msg = {}
    try:
        request_msg = json.loads(body)
        logger.info(f"收到分析请求: messageId={request_msg.get('messageId')}, recordId={request_msg.get('recordId')}")

        message_id = request_msg.get("messageId", str(uuid.uuid4()))
        record_id = request_msg.get("recordId", "")
        user_id = request_msg.get("userId", 0)
        action_type = request_msg.get("actionType", "batting")
        video_url = request_msg.get("videoUrl", "")

        if not video_url:
            raise ValueError("消息中缺少 videoUrl 字段")

        # 下载视频
        ext = video_url.rsplit(".", 1)[-1] if "." in video_url else "mp4"
        video_path = settings.UPLOAD_DIR / f"{record_id}.{ext}"
        download_video(video_url, video_path)

        # 执行分析
        logger.info(f"开始分析视频: {record_id}")
        final_analysis = analyze_video(video_path)

        # 清理下载的视频
        video_path.unlink(missing_ok=True)

        # 上传骨骼视频到 MinIO
        output_video_path = settings.OUTPUT_DIR / f"{record_id}_skeleton.mp4"
        logger.info(f"[{message_id}] 上传骨骼视频到 MinIO")
        video_upload_result = storage_client.upload_video(output_video_path)
        skeleton_video_url = video_upload_result["downloadUrl"] if video_upload_result else ""

        # 保存并上传 JSON 到 MinIO
        output_json_path = settings.OUTPUT_DIR / f"{record_id}_analysis.json"
        output_data = {
            "recordId": record_id,
            "userId": user_id,
            "actionType": action_type,
            "raw_data": final_analysis
        }
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        logger.info(f"[{message_id}] 上传分析结果 JSON 到 MinIO")
        json_upload_result = storage_client.upload_json(output_json_path)
        analysis_json_url = json_upload_result["downloadUrl"] if json_upload_result else ""

        # 构造成功响应
        result_message = build_analysis_result(
            message_id=message_id,
            record_id=record_id,
            user_id=user_id,
            action_type=action_type,
            video_url=video_url,
            raw_data=final_analysis,
            skeleton_video_url=skeleton_video_url,
            analysis_json_url=analysis_json_url
        )

        # 发送成功结果到 completed 队列
        client = RabbitMQClient(url=settings.RABBITMQ_URL)
        if client.connect():
            client.publish_message(
                queue=settings.RABBITMQ_COMPLETED_QUEUE,
                message=result_message,
                routing_key=settings.RABBITMQ_ROUTING_KEY_COMPLETED
            )
            client.close()

        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"分析完成: recordId={record_id}")

    except Exception as e:
        logger.error(f"处理请求时出错: {e}")

        # 构造失败响应
        error_message = build_analysis_failed(
            message_id=request_msg.get("messageId", str(uuid.uuid4())),
            record_id=request_msg.get("recordId", ""),
            user_id=request_msg.get("userId", 0),
            error=str(e),
            error_code="ANALYSIS_ERROR"
        )

        try:
            client = RabbitMQClient(url=settings.RABBITMQ_URL)
            if client.connect():
                client.publish_message(
                    queue=settings.RABBITMQ_FAILED_QUEUE,
                    message=error_message,
                    routing_key=settings.RABBITMQ_ROUTING_KEY_FAILED
                )
                client.close()
        except Exception as send_error:
            logger.error(f"发送错误消息失败: {send_error}")

        ch.basic_ack(delivery_tag=method.delivery_tag)


def main():
    """主函数：启动消费者"""
    logger.info("启动 MediaPose RabbitMQ 消费者...")

    client = RabbitMQClient(url=settings.RABBITMQ_URL)

    if not client.connect():
        logger.error("无法连接到 RabbitMQ，退出程序")
        sys.exit(1)

    try:
        logger.info(f"开始监听队列: {settings.RABBITMQ_REQUEST_QUEUE}")
        client.consume(
            queue=settings.RABBITMQ_REQUEST_QUEUE,
            callback=process_request,
            auto_ack=False
        )
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭...")
    finally:
        client.close()
        logger.info("消费者已关闭")


if __name__ == "__main__":
    main()
