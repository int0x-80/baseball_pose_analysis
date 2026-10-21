package com.baseball.commons.config;

import com.alibaba.fastjson2.JSON;
import com.baseball.commons.constants.RabbitMQConstants;
import com.baseball.commons.dto.MQAnalysisMessage;
import org.springframework.amqp.core.*;
import org.springframework.amqp.rabbit.config.SimpleRabbitListenerContainerFactory;
import org.springframework.amqp.rabbit.connection.ConnectionFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConversionException;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * RabbitMQ 配置
 */
@Configuration
public class RabbitMQConfig {

    @Bean
    public Exchange analysisExchange() {
        return new DirectExchange(RabbitMQConstants.ANALYSIS_EXCHANGE);
    }

    @Bean
    public Queue analysisRequestQueue() {
        return QueueBuilder.durable(RabbitMQConstants.ANALYSIS_REQUEST_QUEUE).build();
    }

    @Bean
    public Queue analysisCompletedQueue() {
        return QueueBuilder.durable(RabbitMQConstants.ANALYSIS_COMPLETED_QUEUE).build();
    }

    @Bean
    public Queue analysisFailedQueue() {
        return QueueBuilder.durable(RabbitMQConstants.ANALYSIS_FAILED_QUEUE).build();
    }

    @Bean
    public Binding requestBinding(
            @Qualifier("analysisRequestQueue") Queue queue,
            @Qualifier("analysisExchange") Exchange exchange
    ) {
        return BindingBuilder.bind(queue)
                .to((DirectExchange) exchange)
                .with(RabbitMQConstants.ROUTING_KEY_REQUEST);
    }

    @Bean
    public Binding completedBinding(
            @Qualifier("analysisCompletedQueue") Queue queue,
            @Qualifier("analysisExchange") Exchange exchange
    ) {
        return BindingBuilder.bind(queue)
                .to((DirectExchange) exchange)
                .with(RabbitMQConstants.ROUTING_KEY_COMPLETED);
    }

    @Bean
    public Binding failedBinding(
            @Qualifier("analysisFailedQueue") Queue queue,
            @Qualifier("analysisExchange") Exchange exchange
    ) {
        return BindingBuilder.bind(queue)
                .to((DirectExchange) exchange)
                .with(RabbitMQConstants.ROUTING_KEY_FAILED);
    }

    @Bean
    public Jackson2JsonMessageConverter jsonConverter() {
        // Python 端发送的 JSON 消息没有 __TypeId__ 头，
        // 自定义 fromMessage：缺少类型信息时默认反序列化为 MQAnalysisMessage
        return new Jackson2JsonMessageConverter() {
            @Override
            public Object fromMessage(Message message) throws MessageConversionException {
                try {
                    String json = new String(message.getBody(), java.nio.charset.StandardCharsets.UTF_8);
                    return JSON.parseObject(json, MQAnalysisMessage.class);
                } catch (Exception e) {
                    throw new MessageConversionException("Failed to deserialize MQ message to MQAnalysisMessage", e);
                }
            }
        };
    }

    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory) {
        RabbitTemplate rabbitTemplate = new RabbitTemplate(connectionFactory);
        rabbitTemplate.setMessageConverter(jsonConverter());
        return rabbitTemplate;
    }

    /**
     * 配置 @RabbitListener 使用 Jackson 反序列化
     * 确保 Python 发来的 JSON 消息能正确转为 MQAnalysisMessage
     */
    @Bean
    public SimpleRabbitListenerContainerFactory rabbitListenerContainerFactory(
            ConnectionFactory connectionFactory) {
        SimpleRabbitListenerContainerFactory factory = new SimpleRabbitListenerContainerFactory();
        factory.setConnectionFactory(connectionFactory);
        factory.setMessageConverter(jsonConverter());
        return factory;
    }
}