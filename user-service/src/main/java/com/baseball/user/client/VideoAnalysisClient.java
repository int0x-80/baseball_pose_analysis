package com.baseball.user.client;

import com.baseball.commons.domain.BaseResponse;
import com.baseball.commons.dto.VideoAnalysisResult;
import com.baseball.commons.dto.VideoMetadata;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

/**
 * MediaPipe 分析服务客户端
 * 通过 Nacos 服务发现调用 Python 服务
 */
@FeignClient(name = "baseball-pose-analyst")
public interface VideoAnalysisClient {

    /**
     * 调用 Python 服务的视频分析接口
     * Python 服务接收后立即返回 messageId，后台异步分析，
     * 分析完成后通过 RabbitMQ 返回结果
     *
     * @param video      视频文件
     * @param userId     用户ID
     * @param actionType 动作类型 (batting/pitching)
     * @param recordId   记录ID（由 Java 端生成，保证一致性）
     * @return 响应包含 messageId 和 recordId
     */
    @PostMapping(value = "/baseballPoseAnalyst", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    BaseResponse<VideoMetadata> analyzeVideo(
            @RequestPart("video") MultipartFile video,
            @RequestPart("userId") Long userId,
            @RequestPart("actionType") String actionType,
            @RequestPart("recordId") String recordId
    );
}
