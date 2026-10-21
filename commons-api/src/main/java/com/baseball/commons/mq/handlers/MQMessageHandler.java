package com.baseball.commons.mq.handlers;

import com.baseball.commons.dto.MQAnalysisMessage;

/**
 * MQ 消息处理器接口
 * 所有 MQ 消息处理器都需要实现此接口
 *
 * @author Wang Yinuo
 * @date 2026-06-29
 */
public interface MQMessageHandler {

    /**
     * 处理 MQ 消息
     *
     * @param message MQ 消息
     * @return 是否处理成功
     */
    boolean handle(MQAnalysisMessage message);

    /**
     * 获取处理器支持的消息类型
     *
     * @return 消息类型（如：VIDEO_ANALYSIS_COMPLETED）
     */
    String getSupportedMessageType();
}
