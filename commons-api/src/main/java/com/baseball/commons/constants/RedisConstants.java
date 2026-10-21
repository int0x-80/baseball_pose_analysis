package com.baseball.commons.constants;

/**
 * Redis Key 常量
 */
public class RedisConstants {
    // 用户信息缓存
    public static final String USER_INFO = "user:info:";

    // 分析结果缓存
    public static final String ANALYSIS_RESULT = "analysis:result:";

    // 上传token
    public static final String UPLOAD_TOKEN = "upload:token:";

    // 分布式锁
    public static final String LOCK_ANALYSIS = "lock:analysis:";
    public static final String LOCK_CARD = "lock:card:";

    // 限流
    public static final String RATE_LIMIT = "rate:limit:";

    // 每日登录去重
    public static final String LOGIN = "login-";

    private RedisConstants() {}
}