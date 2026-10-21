package com.baseball.commons.util;

import com.baseball.commons.config.JwtConfig.JwtContextHolder;
import io.jsonwebtoken.*;
import lombok.extern.slf4j.Slf4j;

import java.util.Date;
import java.util.HashMap;
import java.util.Map;

/**
 * JWT 工具类（通用版本）
 * 可在所有微服务中使用
 *
 * 密钥和过期时间由 JwtConfig 从 application.yml 注入
 * jwt.secret   - 签名密钥
 * jwt.expiration - 过期时间（毫秒）
 */
@Slf4j
public class JwtUtil {

    /**
     * 生成 JWT Token
     */
    public static String generateToken(Long userId, String platform) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("userId", userId);
        claims.put("platform", platform);

        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + JwtContextHolder.expiration);

        return Jwts.builder()
                .setClaims(claims)
                .setSubject(String.valueOf(userId))
                .setIssuedAt(now)
                .setExpiration(expiryDate)
                .signWith(JwtContextHolder.secretKey, SignatureAlgorithm.HS256)
                .compact();
    }
    
    /**
     * 从 Token 中获取用户ID
     */
    public static Long getUserIdFromToken(String token) {
        try {
            Claims claims = parseToken(token);
            return Long.valueOf(claims.getSubject());
        } catch (Exception e) {
            log.error("解析Token失败: {}", e.getMessage());
            return null;
        }
    }
    
    /**
     * 从 Token 中获取平台信息
     */
    public static String getPlatformFromToken(String token) {
        try {
            Claims claims = parseToken(token);
            return (String) claims.get("platform");
        } catch (Exception e) {
            log.error("解析Token失败: {}", e.getMessage());
            return null;
        }
    }
    
    /**
     * 验证 Token 是否有效
     */
    public static boolean validateToken(String token) {
        try {
            parseToken(token);
            return true;
        } catch (ExpiredJwtException e) {
            log.error("Token 已过期: {}", e.getMessage());
        } catch (MalformedJwtException e) {
            log.error("Token 格式错误: {}", e.getMessage());
        } catch (SignatureException e) {
            log.error("Token 签名无效: {}", e.getMessage());
        } catch (Exception e) {
            log.error("Token 验证失败: {}", e.getMessage());
        }
        return false;
    }
    
    /**
     * 解析 Token
     */
    private static Claims parseToken(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(JwtContextHolder.secretKey)
                .build()
                .parseClaimsJws(token)
                .getBody();
    }
}
