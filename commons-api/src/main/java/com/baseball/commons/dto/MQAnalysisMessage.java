package com.baseball.commons.dto;

import lombok.Data;
import java.io.Serializable;
import java.util.Map;

/**
 * MQ 分析消息通用类
 * 用于 Python 服务和 Java 服务之间的消息传递
 *
 * @author Wang Yinuo
 * @date 2026-06-29
 */
@Data
public class MQAnalysisMessage implements Serializable {

    private static final long serialVersionUID = 1L;

    /**
     * 消息ID
     */
    private String messageId;

    /**
     * 记录ID
     */
    private String recordId;

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 消息状态: COMPLETED/FAILED
     */
    private String status;

    /**
     * 视频元数据
     */
    private VideoMetadata videoMetadata;

    /**
     * 视频分析结果
     */
    private VideoAnalysisResult analysisResult;

    /**
     * 错误信息（失败时使用）
     */
    private String errorMessage;

    /**
     * 错误码（失败时使用）
     */
    private String errorCode;

    /**
     * 时间戳
     */
    private Long timestamp;

    /**
     * 扩展字段（用于未来扩展）
     */
    private Map<String, Object> extensions;
}

