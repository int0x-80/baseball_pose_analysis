package com.baseball.commons.util;

import lombok.extern.slf4j.Slf4j;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import javax.servlet.http.HttpServletRequest;

/**
 * 用户上下文工具类（通用版本）
 * 用于获取当前登录用户信息
 * 
 * 使用方式：
 * Long userId = UserContext.getCurrentUserId();
 * String platform = UserContext.getCurrentPlatform();
 */
@Slf4j
public class UserContext {
    
    // Header 常量定义
    public static final String HEADER_USER_ID = "X-User-Id";
    public static final String HEADER_PLATFORM = "X-Platform";
    public static final String HEADER_AUTHORIZATION = "Authorization";
    
    /**
     * 获取当前登录用户ID
     * 优先级：Header > Token > null
     */
    public static Long getCurrentUserId() {
        HttpServletRequest request = getCurrentRequest();
        if (request == null) {
            return null;
        }
        
        // 优先从 Header 获取（Gateway 已解析）
        String userIdStr = request.getHeader(HEADER_USER_ID);
        if (userIdStr != null && !userIdStr.isEmpty()) {
            try {
                return Long.valueOf(userIdStr);
            } catch (NumberFormatException e) {
                log.warn("Header中的userId格式错误: {}", userIdStr);
            }
        }
        
        // 兜底：从 Token 解析
        String token = getTokenFromRequest(request);
        if (token != null) {
            return JwtUtil.getUserIdFromToken(token);
        }
        
        return null;
    }
    
    /**
     * 获取当前登录平台
     * 优先级：Header > Token > null
     */
    public static String getCurrentPlatform() {
        HttpServletRequest request = getCurrentRequest();
        if (request == null) {
            return null;
        }
        
        // 优先从 Header 获取
        String platform = request.getHeader(HEADER_PLATFORM);
        if (platform != null && !platform.isEmpty()) {
            return platform;
        }
        
        // 兜底：从 Token 解析
        String token = getTokenFromRequest(request);
        if (token != null) {
            return JwtUtil.getPlatformFromToken(token);
        }
        
        return null;
    }
    
    /**
     * 获取当前请求
     */
    public static HttpServletRequest getCurrentRequest() {
        ServletRequestAttributes attributes = 
            (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        if (attributes == null) {
            return null;
        }
        return attributes.getRequest();
    }
    
    /**
     * 从请求中获取 Token
     */
    private static String getTokenFromRequest(HttpServletRequest request) {
        String token = request.getHeader(HEADER_AUTHORIZATION);
        if (token != null && token.startsWith("Bearer ")) {
            return token.substring(7);
        }
        return request.getParameter("token");
    }
    
    /**
     * 检查当前是否已登录
     */
    public static boolean isLoggedIn() {
        return getCurrentUserId() != null;
    }
    
    /**
     * 检查当前用户是否来自指定平台
     */
    public static boolean isFromPlatform(String platform) {
        String currentPlatform = getCurrentPlatform();
        return platform != null && platform.equals(currentPlatform);
    }
    
    /**
     * 检查当前用户是否来自微信小程序
     */
    public static boolean isFromWechat() {
        return isFromPlatform("wechat");
    }
    
    /**
     * 检查当前用户是否来自APP
     */
    public static boolean isFromApp() {
        return isFromPlatform("app");
    }
}
