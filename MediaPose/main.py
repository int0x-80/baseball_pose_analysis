"""
FastAPI 主应用
"""
import uuid
import logging
import threading
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Query
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import uvicorn
import time

from app.core.config import settings
from app.core.pose_detector import PoseDetector
from app.utils.action_analyzer_v2 import ActionAnalyzerV2
from app.utils.batting_analyzer import BattingAnalyzer
from app.utils.keyframe_extractor import KeyFrameExtractor
from app.utils.clip_extractor import BattingClipExtractor
from app.api import setup_nacos_registry
from app.consumer.rabbitmq_client import RabbitMQClient
from app.core.message_builder import build_analysis_completed_message, build_analysis_failed_message
from app.core.response_builder import (
    build_success_response,
    build_fail_response,
    build_video_metadata,
    build_video_analysis_result
)
from app.core.storage_client import storage_client
import cv2
import json

logger = logging.getLogger(__name__)

app = FastAPI(
    title="MediaPose Service",
    description="棒球动作分析微服务",
    version="1.0.0"
)

setup_nacos_registry(app)


def get_detector():
    return PoseDetector()


def get_analyzer(fps: int = 30):
    return ActionAnalyzerV2(fps=fps, pixels_to_meters=0.002)


def get_timestamp_filename(original_name: str, ext: str) -> str:
    timestamp = int(time.time() * 1000)
    stem = Path(original_name).stem
    return f"{timestamp}_{stem}.{ext}"


def publish_analysis_result(
    message_id: str, record_id: str, user_id: int,
    action_type: str, video_metadata: dict, analysis_result: dict
):
    try:
        client = RabbitMQClient(url=settings.RABBITMQ_URL)
        if not client.connect():
            logger.error("无法连接 RabbitMQ，跳过消息发布")
            return
        result_message = build_analysis_completed_message(
            message_id=message_id, record_id=record_id, user_id=user_id,
            video_metadata=video_metadata, analysis_result=analysis_result
        )
        success = client.publish_message(
            queue=settings.RABBITMQ_COMPLETED_QUEUE,
            message=result_message, routing_key=settings.RABBITMQ_ROUTING_KEY_COMPLETED
        )
        client.close()
        if success:
            logger.info(f"分析结果已发布到 RabbitMQ: messageId={message_id}")
        else:
            logger.error(f"发布分析结果到 RabbitMQ 失败: messageId={message_id}")
    except Exception as e:
        logger.error(f"发布分析结果到 RabbitMQ 异常: {e}")


def publish_analysis_failed(message_id: str, record_id: str, user_id: int, error: str):
    try:
        client = RabbitMQClient(url=settings.RABBITMQ_URL)
        if not client.connect():
            logger.error("无法连接 RabbitMQ，跳过失败消息发布")
            return
        fail_message = build_analysis_failed_message(
            message_id=message_id, record_id=record_id, user_id=user_id, error=error
        )
        success = client.publish_message(
            queue=settings.RABBITMQ_FAILED_QUEUE,
            message=fail_message, routing_key=settings.RABBITMQ_ROUTING_KEY_FAILED
        )
        client.close()
        if success:
            logger.info(f"失败消息已发布到 RabbitMQ: messageId={message_id}")
        else:
            logger.error(f"发布失败消息到 RabbitMQ 失败: messageId={message_id}")
    except Exception as e:
        logger.error(f"发布失败消息到 RabbitMQ 异常: {e}")


def run_analysis(
    message_id: str, record_id: str, user_id: int,
    action_type: str, upload_path: Path,
    output_video_path: Path, output_json_path: Path
):
    """后台线程：执行视频分析，上传到 MinIO，并发布结果到 RabbitMQ"""
    step_start = time.time()
    try:
        logger.info(f"{'='*60}")
        logger.info(f"[{message_id}] 开始视频分析任务")
        logger.info(f"[{message_id}] recordId={record_id}, userId={user_id}, actionType={action_type}")
        logger.info(f"{'='*60}")

        is_batting = action_type.lower() in ('batting', 'bat')
        date_str = datetime.now().strftime("%Y%m%d")
        ts_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"{user_id}_{action_type}_{ts_str}"
        storage_video_prefix = f"{user_id}/{date_str}/video"
        storage_pic_prefix = f"{user_id}/{date_str}/pic"

        # ========== 步骤1: 读取视频信息 ==========
        logger.info(f"[{message_id}] [步骤1/6] 读取视频信息...")
        step_start = time.time()

        cap = cv2.VideoCapture(str(upload_path))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        full_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        logger.info(f"[{message_id}] 视频信息: {width}x{height}, {fps}fps, {full_frame_count}帧")
        logger.info(f"[{message_id}] [步骤1/6] 完成，耗时: {time.time() - step_start:.2f}s")

        # ========== 步骤2: 全视频姿态检测 ==========
        logger.info(f"[{message_id}] [步骤2/6] 开始全视频姿态检测...")
        step_start = time.time()

        detector = get_detector()
        full_results, _, _ = detector.process_video(str(upload_path), output_path=None)
        detector.cleanup()

        logger.info(f"[{message_id}] 检测到 {len(full_results)} 帧关键点")
        logger.info(f"[{message_id}] [步骤2/6] 完成，耗时: {time.time() - step_start:.2f}s")

        # ========== 步骤3: 阶段检测 + 裁剪片段（仅 batting） ==========
        clip_path = None
        clip_range = None       # (start_frame, end_frame) 原始视频中的帧范围
        clip_results = None     # 片段范围内的检测结果切片
        clip_frame_count = 0
        boundaries = None
        frame_metrics = None

        if is_batting:
            logger.info(f"[{message_id}] [步骤3/6] 阶段检测 + 裁剪挥棒片段...")
            step_start = time.time()

            try:
                # 快速阶段检测（仅用于定位挥棒范围）
                from app.utils.phase_detector import BattingPhaseDetector
                quick_detector = BattingPhaseDetector(fps=fps)
                phase_labels_full, boundaries_full, metrics_full = quick_detector.detect_phases(full_results)

                # 计算裁剪范围
                clip_extractor = BattingClipExtractor(fps=fps)
                clip_range = clip_extractor.compute_clip_range(boundaries_full, full_frame_count)

                if clip_range:
                    start_f, end_f = clip_range
                    clip_frame_count = end_f - start_f + 1

                    # 裁剪视频文件
                    clip_filename = f"{base_name}_clip.mp4"
                    clip_path = settings.OUTPUT_DIR / clip_filename

                    clip_info_raw = clip_extractor.extract_clip(
                        str(upload_path), str(clip_path), boundaries_full, full_frame_count
                    )

                    if clip_info_raw and clip_path.exists():
                        # 切片检测结果（用于后续分析）
                        clip_results = full_results[start_f:end_f + 1]

                        # 重新对片段做阶段检测（更精准的阶段边界）
                        boundaries, frame_metrics = None, None
                        # 使用切片后的 phase_labels 和 metrics
                        # 但阶段边界需要相对于片段视频的帧号
                        clip_phase_labels = phase_labels_full[start_f:end_f + 1]
                        # 重建 boundaries 为片段相对帧号
                        from app.utils.phase_detector import PhaseBoundary
                        boundaries = []
                        current_phase = clip_phase_labels[0]
                        seg_start = 0
                        for i in range(1, len(clip_phase_labels)):
                            if clip_phase_labels[i] != current_phase:
                                boundaries.append(PhaseBoundary(
                                    phase=current_phase,
                                    start_frame=seg_start, end_frame=i - 1,
                                    start_time_sec=seg_start / fps,
                                    end_time_sec=(i - 1) / fps,
                                    duration_sec=(i - 1 - seg_start) / fps
                                ))
                                current_phase = clip_phase_labels[i]
                                seg_start = i
                        boundaries.append(PhaseBoundary(
                            phase=current_phase,
                            start_frame=seg_start, end_frame=len(clip_phase_labels) - 1,
                            start_time_sec=seg_start / fps,
                            end_time_sec=(len(clip_phase_labels) - 1) / fps,
                            duration_sec=(len(clip_phase_labels) - 1 - seg_start) / fps
                        ))

                        # frame_metrics 也切片
                        frame_metrics = metrics_full[start_f:end_f + 1]
                        for fm in frame_metrics:
                            fm.frame_idx = fm.frame_idx - start_f  # 重映射帧号

                        logger.info(f"[{message_id}] 片段裁剪完成: 帧 {start_f}-{end_f} "
                                     f"({clip_frame_count}帧, {clip_frame_count/fps:.2f}s), "
                                     f"{len(boundaries)} 个阶段")
                    else:
                        logger.warning(f"[{message_id}] 片段裁剪失败，回退到全视频分析")
                        clip_results = full_results
                        clip_frame_count = full_frame_count
                else:
                    logger.warning(f"[{message_id}] 未检测到有效挥棒范围，回退到全视频分析")
                    clip_results = full_results
                    clip_frame_count = full_frame_count

            except Exception as e:
                logger.error(f"[{message_id}] 阶段检测/裁剪异常: {e}")
                import traceback
                traceback.print_exc()
                clip_results = full_results
                clip_frame_count = full_frame_count

            logger.info(f"[{message_id}] [步骤3/6] 完成，耗时: {time.time() - step_start:.2f}s")
        else:
            logger.info(f"[{message_id}] [步骤3/6] 非击球类型 ({action_type})，跳过裁剪")
            clip_results = full_results
            clip_frame_count = full_frame_count

        # 后续分析统一使用 clip_results（片段或全视频）
        results = clip_results
        analysis_frame_count = clip_frame_count
        # 分析用的视频路径：如果有片段就用片段，否则用原视频
        analysis_video_path = clip_path if clip_path and clip_path.exists() else upload_path

        # ========== 步骤4: 基础动作分析（基于片段） ==========
        logger.info(f"[{message_id}] [步骤4/6] 基础动作分析 ({analysis_frame_count}帧)...")
        step_start = time.time()

        analyzer = get_analyzer(fps)
        for frame_idx, result in enumerate(results):
            analyzer.analyze_frame(result, frame_idx + 1)
        output_data = analyzer.export_to_json(
            str(analysis_video_path), fps, width, height, analysis_frame_count
        )

        logger.info(f"[{message_id}] 基础分析完成")
        logger.info(f"[{message_id}] [步骤4/6] 完成，耗时: {time.time() - step_start:.2f}s")

        # ========== 步骤5: 击球专项分析 + 骨架视频 + 关键帧（仅 batting） ==========
        batting_report = None
        bat_trajectory = None
        keyframe_urls = []
        clip_info = None
        phase_labels = None
        trajectory_valid_frames = set()

        if is_batting:
            logger.info(f"[{message_id}] [步骤5/6] 击球专项分析 + 骨架视频 + 关键帧...")
            step_start = time.time()

            # ---- 5a: 击球专项分析（基于片段数据） ----
            try:
                batting_analyzer = BattingAnalyzer(fps=fps)
                batting_report = batting_analyzer.analyze(results)
                bat_trajectory = batting_analyzer.trajectory_tracker.compute_trajectory(results)

                # 阶段标签（如果步骤3已经计算了就用现有的，否则重新检测）
                if boundaries is not None and frame_metrics is not None:
                    # 从步骤3的切片重建 phase_labels
                    phase_labels = []
                    for b in boundaries:
                        for _ in range(b.start_frame, b.end_frame + 1):
                            phase_labels.append(b.phase)
                    # 确保长度匹配
                    while len(phase_labels) < len(results):
                        phase_labels.append(boundaries[-1].phase if boundaries else None)
                    phase_labels = phase_labels[:len(results)]
                else:
                    phase_labels, boundaries, frame_metrics = \
                        batting_analyzer.get_phase_labels_and_boundaries(results)

                output_data['batting_analysis'] = batting_report

                # 计算轨迹显示范围：击球点（棒头峰值速度帧）前后各 15 帧
                TRAJECTORY_WINDOW = 15
                trajectory_valid_frames = set()

                contact_frame = None
                if bat_trajectory:
                    peak_t = max(bat_trajectory,
                                 key=lambda t: t.get('bat_tip_speed_ms', 0))
                    contact_frame = peak_t.get('frame_idx', None)

                if contact_frame is None:
                    contact_frame = batting_report.get('contactSpeed', {}).get('frame_idx', None)

                if contact_frame is not None:
                    traj_start = max(0, contact_frame - TRAJECTORY_WINDOW)
                    traj_end = contact_frame + TRAJECTORY_WINDOW
                    for f in range(traj_start, traj_end + 1):
                        trajectory_valid_frames.add(f)
                    logger.info(f"[{message_id}] 击球点帧={contact_frame}, "
                                f"轨迹范围 {traj_start}-{traj_end} ({len(trajectory_valid_frames)} 帧)")
                else:
                    logger.warning(f"[{message_id}] 未找到击球点帧，不显示轨迹")

                logger.info(f"[{message_id}] 击球分析完成: "
                             f"{len(boundaries) if boundaries else 0} 个阶段, "
                             f"击球速度 {batting_report.get('contactSpeed', {}).get('speed_kmh', 0):.1f} km/h")
            except Exception as e:
                logger.error(f"[{message_id}] 击球分析异常: {e}")
                import traceback
                traceback.print_exc()

            # ---- 5b: 阶段感知骨架视频（从片段视频生成） ----
            if phase_labels is not None:
                detector2 = get_detector()
                try:
                    detector2.process_video_phase_aware(
                        video_path=str(analysis_video_path),
                        output_path=str(output_video_path),
                        phase_labels=phase_labels,
                        bat_trajectory=bat_trajectory,
                        trajectory_valid_frames=trajectory_valid_frames,
                    )
                    logger.info(f"[{message_id}] 阶段骨架视频已保存: {output_video_path.name}")
                finally:
                    detector2.cleanup()

            # ---- 5c: 关键帧提取（从片段视频） ----
            if boundaries is not None and frame_metrics is not None:
                try:
                    extractor = KeyFrameExtractor()
                    keyframes = extractor.extract_keyframes(
                        str(analysis_video_path), boundaries, frame_metrics
                    )

                    detector3 = get_detector()
                    for kf in keyframes:
                        frame_img = detector3.read_frame_at(str(analysis_video_path), kf.frame_idx)
                        if frame_img is not None:
                            # 只保存原图，不叠加骨架
                            kf_filename = f"{base_name}_kf_{kf.phase.value.lower()}.png"
                            kf_path = settings.OUTPUT_DIR / kf_filename
                            cv2.imwrite(str(kf_path), frame_img)

                            kf_object_name = f"{storage_pic_prefix}/{kf_filename}"
                            upload_result = storage_client.upload_image(kf_path, object_name=kf_object_name)
                            if upload_result:
                                keyframe_urls.append({
                                    'phase': kf.phase.value,
                                    'phaseLabelCn': kf.phase.label_cn,
                                    'frameIndex': kf.frame_idx,
                                    'imageUrl': upload_result.get('objectName', ''),
                                    'metrics': kf.metrics,
                                })
                                logger.info(f"[{message_id}] 关键帧上传成功: {kf.phase.value}")
                    detector3.cleanup()

                    output_data['keyframes'] = keyframe_urls
                    logger.info(f"[{message_id}] 提取并上传 {len(keyframe_urls)} 张关键帧")
                except Exception as e:
                    logger.error(f"[{message_id}] 关键帧处理异常: {e}")
                    import traceback
                    traceback.print_exc()

            # ---- 5d: 上传片段视频信息 ----
            if clip_path and clip_path.exists() and boundaries is not None:
                try:
                    clip_object_name = f"{storage_video_prefix}/{base_name}_clip.mp4"
                    clip_upload = storage_client.upload_video(clip_path, object_name=clip_object_name)
                    if clip_upload:
                        # 构建片段信息（含各阶段在片段中的相对位置）
                        phase_markers = []
                        for b in boundaries:
                            phase_markers.append({
                                'phase': b.phase.value,
                                'phaseLabelCn': b.phase.label_cn,
                                'startFrame': b.start_frame,
                                'endFrame': b.end_frame,
                                'startMs': round(b.start_time_sec * 1000, 1),
                                'endMs': round(b.end_time_sec * 1000, 1),
                            })

                        clip_info = {
                            'objectName': clip_upload.get('objectName', ''),
                            'downloadUrl': clip_upload.get('downloadUrl', ''),
                            'startFrame': clip_range[0] if clip_range else 0,
                            'endFrame': clip_range[1] if clip_range else 0,
                            'frameCount': analysis_frame_count,
                            'durationSec': round(analysis_frame_count / fps, 2),
                            'durationMs': round(analysis_frame_count / fps * 1000, 1),
                            'fps': fps,
                            'phaseMarkers': phase_markers,
                        }
                        output_data['swing_clip'] = clip_info
                        logger.info(f"[{message_id}] 挥棒片段上传成功: {clip_info['objectName']} "
                                     f"({clip_info['frameCount']}帧, {clip_info['durationSec']}s)")
                    else:
                        logger.warning(f"[{message_id}] 挥棒片段上传失败")
                except Exception as e:
                    logger.error(f"[{message_id}] 片段上传异常: {e}")

            logger.info(f"[{message_id}] [步骤5/6] 完成，耗时: {time.time() - step_start:.2f}s")
        else:
            # 非击球模式：使用旧版骨架视频生成
            logger.info(f"[{message_id}] [步骤5/6] 生成骨架视频...")
            step_start = time.time()
            detector2 = get_detector()
            try:
                detector2.process_video(str(upload_path), str(output_video_path))
                logger.info(f"[{message_id}] 骨架视频已保存: {output_video_path.name}")
            finally:
                detector2.cleanup()
            logger.info(f"[{message_id}] [步骤5/6] 完成，耗时: {time.time() - step_start:.2f}s")

        # ========== 步骤6: 保存、上传、发布 ==========
        logger.info(f"[{message_id}] [步骤6/6] 保存分析结果并上传到 MinIO...")
        step_start = time.time()

        output_data['output_video'] = output_video_path.name

        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        logger.info(f"[{message_id}] JSON 结果已保存: {output_json_path.name}")

        upload_path.unlink(missing_ok=True)
        logger.info(f"[{message_id}] 已删除上传的原视频文件")

        skeleton_object_name = f"{storage_video_prefix}/{base_name}_skeleton.mp4"
        json_object_name = f"{storage_video_prefix}/{base_name}_analysis.json"

        video_upload_result = storage_client.upload_video(output_video_path, object_name=skeleton_object_name)
        skeleton_video_name = video_upload_result["objectName"] if video_upload_result else ""
        if skeleton_video_name:
            logger.info(f"[{message_id}] 骨骼视频上传成功: {skeleton_video_name}")
        else:
            logger.warning(f"[{message_id}] 骨骼视频上传失败")

        json_upload_result = storage_client.upload_json(output_json_path, object_name=json_object_name)
        analysis_json_name = json_upload_result["objectName"] if json_upload_result else ""
        if analysis_json_name:
            logger.info(f"[{message_id}] JSON 上传成功: {analysis_json_name}")
        else:
            logger.warning(f"[{message_id}] JSON 上传失败")

        logger.info(f"[{message_id}] [步骤6/6] 完成，耗时: {time.time() - step_start:.2f}s")

        # 构建结果并发布到 RabbitMQ
        video_metadata = build_video_metadata(
            user_id=user_id, record_id=record_id, message_id=message_id,
            video_url="", skeleton_video_url="", status=1,
            skeleton_video_name=skeleton_video_name,
            analysis_json_name=analysis_json_name,
            fps=fps, video_width=width, video_height=height, total_frames=analysis_frame_count
        )

        analysis_result = build_video_analysis_result(
            record_id=record_id, user_id=user_id,
            action_type=action_type, raw_data=output_data,
            batting_report=batting_report,
            keyframe_urls=keyframe_urls,
            clip_info=clip_info,
        )

        publish_analysis_result(
            message_id=message_id, record_id=record_id, user_id=user_id,
            action_type=action_type, video_metadata=video_metadata,
            analysis_result=analysis_result
        )

        logger.info(f"{'='*60}")
        logger.info(f"[{message_id}] 视频分析任务全部完成!")
        logger.info(f"{'='*60}")

    except Exception as e:
        logger.error(f"[{message_id}] [错误] 分析失败: {e}")
        logger.error(f"[{message_id}] 当前步骤耗时: {time.time() - step_start:.2f}s")
        import traceback
        traceback.print_exc()
        publish_analysis_failed(
            message_id=message_id, record_id=record_id,
            user_id=user_id, error=str(e)
        )


@app.get("/health")
async def health_check():
    return build_success_response({
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    })


@app.post("/baseballPoseAnalyst")
async def analyze_baseball_action(
    video: UploadFile = File(...),
    userId: int = Form(default=0),
    actionType: str = Form(default="batting"),
    recordId: str = Form(default=None)
):
    """
    棒球动作分析接口（异步）
    参数:
        video: 视频文件
        userId: 用户ID
        actionType: 动作类型 (batting/pitching)
        recordId: 记录ID
    """
    request_time = time.time()
    logger.info(f"{'='*60}")
    logger.info(f"[收到请求] POST /baseballPoseAnalyst")
    logger.info(f"[收到请求] 文件名: {video.filename}, 类型: {video.content_type}, 大小: {video.size} bytes")
    logger.info(f"[收到请求] userId: {userId}, actionType: {actionType}, recordId: {recordId}")
    logger.info(f"{'='*60}")

    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"}
    file_ext = Path(video.filename).suffix.lower()
    if not video.content_type.startswith("video/") and file_ext not in allowed_extensions:
        return JSONResponse(build_fail_response("只支持视频文件", "400"))

    message_id = str(uuid.uuid4())
    record_id = recordId if recordId else f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"

    upload_path = settings.UPLOAD_DIR / get_timestamp_filename(video.filename, video.filename.split('.')[-1])
    output_video_path = settings.OUTPUT_DIR / get_timestamp_filename(video.filename, "mp4")
    output_json_path = settings.OUTPUT_DIR / get_timestamp_filename(video.filename, "json")

    try:
        with open(upload_path, "wb") as f:
            content = await video.read()
            f.write(content)
        logger.info(f"[收到请求] 视频已保存: {upload_path}")
    except Exception as e:
        logger.error(f"[收到请求] 文件保存失败: {e}")
        return JSONResponse(build_fail_response(f"文件保存失败: {str(e)}", "500"))

    video_metadata = build_video_metadata(
        user_id=userId, record_id=record_id, message_id=message_id, status=0
    )

    thread = threading.Thread(
        target=run_analysis,
        args=(message_id, record_id, userId, actionType, upload_path, output_video_path, output_json_path),
        daemon=True
    )
    thread.start()
    logger.info(f"[收到请求] 后台分析线程已启动")
    logger.info(f"[收到请求] 响应耗时: {time.time() - request_time:.3f}s")

    return JSONResponse(build_success_response(video_metadata, "已接收，分析中"))


@app.get("/download/{filename}")
async def download_video(filename: str):
    file_path = settings.OUTPUT_DIR / filename
    if not file_path.exists():
        return JSONResponse(build_fail_response("文件不存在", "404"))
    return FileResponse(path=file_path, media_type="video/mp4", filename=filename)


@app.get("/analysis/{filename}")
async def get_analysis_result(filename: str):
    file_path = settings.OUTPUT_DIR / filename
    if not file_path.exists():
        return JSONResponse(build_fail_response("文件不存在", "404"))
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return JSONResponse(build_success_response(data))


@app.get("/api/outputs")
async def list_outputs():
    files = []
    if settings.OUTPUT_DIR.exists():
        for file in settings.OUTPUT_DIR.iterdir():
            if file.is_file():
                files.append({
                    "name": file.name,
                    "size": file.stat().st_size,
                    "modified": file.stat().st_mtime
                })
    return JSONResponse(build_success_response(files))


if __name__ == "__main__":
    print(settings.PORT)
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
