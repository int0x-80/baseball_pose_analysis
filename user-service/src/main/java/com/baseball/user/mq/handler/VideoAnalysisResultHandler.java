package com.baseball.user.mq.handler;

import com.baomidou.mybatisplus.core.conditions.update.UpdateWrapper;
import com.baseball.commons.dto.MQAnalysisMessage;
import com.baseball.commons.dto.VideoAnalysisResult;
import com.baseball.commons.dto.VideoMetadata;
import com.baseball.commons.mq.handlers.MQMessageHandler;
import com.baseball.user.mapper.VideoMetadataMapper;
import com.baseball.user.mapper.VideoAnalysisResultMapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import java.time.LocalDateTime;

/**
 * 视频分析结果处理器
 * 处理视频分析完成的消息，将结果存储到数据库
 *
 * @author Wang Yinuo
 * @date 2026-06-29
 */
@Slf4j
@Component
public class VideoAnalysisResultHandler implements MQMessageHandler {

    @Autowired
    private VideoMetadataMapper videoMetadataMapper;

    @Autowired
    private VideoAnalysisResultMapper videoAnalysisResultMapper;


    @Override
    public boolean handle(MQAnalysisMessage message) {
        try {
            log.info("开始处理视频分析结果: recordId={}", message.getRecordId());

            // 保存视频元数据
            saveVideoMetadata(message);

            // 保存分析结果
            saveVideoAnalysisResult(message);

            log.info("视频分析结果处理完成: recordId={}", message.getRecordId());
            return true;

        } catch (Exception e) {
            log.error("处理视频分析结果失败: recordId={}", message.getRecordId(), e);
            return false;
        }
    }

    @Override
    public String getSupportedMessageType() {
        return "VIDEO_ANALYSIS_COMPLETED";
    }

    /**
     * 保存视频元数据
     */
    private void saveVideoMetadata(MQAnalysisMessage message) {
        VideoMetadata metadata = message.getVideoMetadata();
        if (metadata == null) {
            log.warn("视频元数据为空: recordId={}", message.getRecordId());
            return;
        }

        // 检查是否已存在
        VideoMetadata existingMetadata = videoMetadataMapper.selectByRecordId(message.getRecordId());

        if (existingMetadata != null) {
            // 只更新分析结果相关字段，不覆盖 video_url / skeleton_video_url / type 等上传时已确定的字段
            videoMetadataMapper.update(null, new UpdateWrapper<VideoMetadata>()
                    .eq("record_id", message.getRecordId())
                    .set("status", metadata.getStatus())
                    .set("skeleton_video_name", metadata.getSkeletonVideoName())
                    .set("analysis_json_name", metadata.getAnalysisJsonName())
                    .set("fps", metadata.getFps())
                    .set("video_width", metadata.getVideoWidth())
                    .set("video_height", metadata.getVideoHeight())
                    .set("total_frames", metadata.getTotalFrames())
                    .set("update_time", LocalDateTime.now())
            );
            log.info("更新视频元数据: recordId={}", message.getRecordId());
        } else {
            // 插入新记录
            metadata.setCreateTime(LocalDateTime.now());
            metadata.setUpdateTime(LocalDateTime.now());
            videoMetadataMapper.insert(metadata);
            log.info("插入视频元数据: recordId={}", message.getRecordId());
        }
    }

    /**
     * 保存视频分析结果
     */
    private void saveVideoAnalysisResult(MQAnalysisMessage message) {
        VideoAnalysisResult analysisResult = message.getAnalysisResult();
        if (analysisResult == null) {
            log.warn("分析结果为空: recordId={}", message.getRecordId());
            return;
        }

        // 检查是否已存在
        VideoAnalysisResult existingResult = videoAnalysisResultMapper.selectByRecordId(message.getRecordId());

        try {
            if (existingResult != null) {
                // 更新现有记录
                analysisResult.setId(existingResult.getId());
                analysisResult.setUpdateTime(LocalDateTime.now());
                videoAnalysisResultMapper.updateById(analysisResult);
                log.info("更新视频分析结果: recordId={}", message.getRecordId());
            } else {
                // 插入新记录
                analysisResult.setCreateTime(LocalDateTime.now());
                analysisResult.setUpdateTime(LocalDateTime.now());
                videoAnalysisResultMapper.insert(analysisResult);
                log.info("插入视频分析结果: recordId={}", message.getRecordId());
            }
        } catch (Exception e) {
            log.error("保存视频分析结果失败: recordId={}", message.getRecordId(), e);
        }
    }
}
