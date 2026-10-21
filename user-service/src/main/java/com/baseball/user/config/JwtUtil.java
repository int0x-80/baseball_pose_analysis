package com.baseball.user.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

/**
 * JWT 工具类（user-service 版本）
 * 委托给 commons-api 的通用实现
 */
@Slf4j
@Component
public class JwtUtil {
    
    /**
     * 生成 JWT Token
     */
    public String generateToken(Long userId, String platform) {
        return com.baseball.commons.util.JwtUtil.generateToken(userId, platform);
    }
    
    /**
     * 从 Token 中获取用户ID
     */
    public Long getUserIdFromToken(String token) {
        return com.baseball.commons.util.JwtUtil.getUserIdFromToken(token);
    }
    
    /**
     * 从 Token 中获取平台信息
     */
    public String getPlatformFromToken(String token) {
        return com.baseball.commons.util.JwtUtil.getPlatformFromToken(token);
    }
    
    /**
     * 验证 Token 是否有效
     */
    public boolean validateToken(String token) {
        return com.baseball.commons.util.JwtUtil.validateToken(token);
    }
}
