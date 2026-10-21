package com.baseball.commons.constants;

/**
 * RabbitMQ 常量
 */
public class RabbitMQConstants {

    // Exchange
    public static final String ANALYSIS_EXCHANGE = "analysis-exchange";

    // Queue
    public static final String ANALYSIS_REQUEST_QUEUE = "analysis-request";
    public static final String ANALYSIS_COMPLETED_QUEUE = "analysis-completed";
    public static final String ANALYSIS_FAILED_QUEUE = "analysis-failed";

    // Routing Key
    public static final String ROUTING_KEY_REQUEST = "request";
    public static final String ROUTING_KEY_COMPLETED = "completed";
    public static final String ROUTING_KEY_FAILED = "failed";

    // Dead Letter
    public static final String DLX_EXCHANGE = "analysis.dlx";
    public static final String DLX_QUEUE = "analysis.dlx.queue";

    private RabbitMQConstants() {}
}