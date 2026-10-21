package com.baseball.commons.config;

import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;

/**
 * JWT 配置
 * 从 application.yml 读取 jwt.secret 和 jwt.expiration
 * 初始化 JwtUtil 的静态字段，保持静态方法调用方式不变
 */
@Slf4j
@Component
public class JwtConfig {

    @Value("${jwt.secret:baseball_pose_analysis_secret_key_2026_very_long_secret}")
    private String secret;

    @Value("${jwt.expiration:86400000}")
    private long expiration;

    @PostConstruct
    public void init() {
        JwtContextHolder.secretKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        JwtContextHolder.expiration = expiration;
        log.info("JWT 配置已加载: expiration={}ms", expiration);
    }

    /**
     * JWT 配置持有者（供 JwtUtil 使用）
     */
    public static class JwtContextHolder {
        public static SecretKey secretKey;
        public static long expiration;
    }
}
