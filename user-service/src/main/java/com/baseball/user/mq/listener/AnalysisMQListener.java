package com.baseball.user.mq.listener;

import com.baseball.commons.constants.RabbitMQConstants;
import com.baseball.commons.dto.MQAnalysisMessage;
import com.baseball.commons.mq.handlers.MQMessageHandler;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * 通用 MQ 消息监听器
 * 监听 RabbitMQ 队列，根据消息类型分发到不同的处理器
 *
 * @author Wang Yinuo
 * @date 2026-06-29
 */
@Slf4j
@Component
public class AnalysisMQListener {

    @Autowired
    private List<MQMessageHandler> handlers;

    private Map<String, MQMessageHandler> handlerMap;

    /**
     * 初始化处理器映射
     */
    private void initHandlerMap() {
        if (handlerMap == null) {
            handlerMap = handlers.stream()
                .collect(Collectors.toMap(
                    MQMessageHandler::getSupportedMessageType,
                    Function.identity()
                ));
            log.info("已注册 {} 个 MQ 消息处理器: {}", handlers.size(), handlerMap.keySet());
        }
    }

    /**
     * 监听分析完成队列
     */
    @RabbitListener(queues = RabbitMQConstants.ANALYSIS_COMPLETED_QUEUE)
    public void handleAnalysisCompleted(MQAnalysisMessage message) {
        log.info("收到分析完成消息: messageId={}, recordId={}, userId={}",
            message.getMessageId(), message.getRecordId(), message.getUserId());

        try {
            // 根据消息状态确定消息类型
            String messageType = determineMessageType(message);

            // 初始化处理器映射
            initHandlerMap();

            // 查找对应的处理器
            MQMessageHandler handler = handlerMap.get(messageType);
            if (handler != null) {
                boolean success = handler.handle(message);
                if (success) {
                    log.info("消息处理成功: messageType={}, recordId={}", messageType, message.getRecordId());
                } else {
                    log.error("消息处理失败: messageType={}, recordId={}", messageType, message.getRecordId());
                }
            } else {
                log.warn("未找到消息处理器: messageType={}, recordId={}", messageType, message.getRecordId());
            }

        } catch (Exception e) {
            log.error("处理消息异常: messageId={}, recordId={}", message.getMessageId(), message.getRecordId(), e);
        }
    }

    /**
     * 监听分析失败队列
     */
    @RabbitListener(queues = RabbitMQConstants.ANALYSIS_FAILED_QUEUE)
    public void handleAnalysisFailed(MQAnalysisMessage message) {
        log.error("收到分析失败消息: messageId={}, recordId={}, error={}",
            message.getMessageId(), message.getRecordId(), message.getErrorMessage());

        // TODO: 处理失败消息，更新数据库状态为 FAILED
    }

    /**
     * 根据消息内容确定消息类型
     */
    private String determineMessageType(MQAnalysisMessage message) {
        // 目前只支持视频分析完成消息
        if (message.getAnalysisResult() != null) {
            return "VIDEO_ANALYSIS_COMPLETED";
        }
        return "UNKNOWN";
    }
}
