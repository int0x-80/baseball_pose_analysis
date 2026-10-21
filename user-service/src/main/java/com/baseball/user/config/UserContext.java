package com.baseball.user.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

/**
 * 用户上下文工具类（user-service 版本）
 * 委托给 commons-api 的通用实现
 */
@Slf4j
@Component
public class UserContext {
    
    /**
     * 获取当前登录用户ID
     */
    public static Long getCurrentUserId() {
        return com.baseball.commons.util.UserContext.getCurrentUserId();
    }
    
    /**
     * 获取当前登录平台
     */
    public static String getCurrentPlatform() {
        return com.baseball.commons.util.UserContext.getCurrentPlatform();
    }
    
    /**
     * 检查当前是否已登录
     */
    public static boolean isLoggedIn() {
        return com.baseball.commons.util.UserContext.isLoggedIn();
    }
}
