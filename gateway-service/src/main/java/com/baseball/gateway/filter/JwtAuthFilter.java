package com.baseball.gateway.filter;

import com.baseball.commons.util.JwtUtil;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.Arrays;
import java.util.List;

/**
 * JWT 认证过滤器
 * 在 Gateway 层统一解析 Token，并将用户信息传递给下游服务
 */
@Slf4j
@Component
public class JwtAuthFilter implements GlobalFilter, Ordered {
    
    // 不需要认证的白名单路径
    private static final List<String> WHITE_LIST = Arrays.asList(
            "/api/user/login",
            "/api/user/register",
            "/api/health",
            "/swagger-resources",
            "/v2/api-docs",
            "/webjars"
    );
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getURI().getPath();
        
        // 白名单路径直接放行
        if (isWhiteListed(path)) {
            return chain.filter(exchange);
        }
        
        // 获取 Token
        String token = getTokenFromRequest(request);
        
        if (token == null || token.isEmpty()) {
            log.warn("未提供认证Token，路径: {}", path);
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
        
        // 验证 Token
        if (!JwtUtil.validateToken(token)) {
            log.warn("Token验证失败，路径: {}", path);
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
        
        // 解析用户信息
        Long userId = JwtUtil.getUserIdFromToken(token);
        String platform = JwtUtil.getPlatformFromToken(token);
        
        if (userId == null) {
            log.warn("无法从Token中解析用户ID，路径: {}", path);
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
        
        log.debug("用户认证成功，userId: {}, platform: {}, path: {}", userId, platform, path);
        
        // 将用户信息添加到 Header，传递给下游服务
        ServerHttpRequest mutatedRequest = request.mutate()
                .header("X-User-Id", String.valueOf(userId))
                .header("X-Platform", platform != null ? platform : "unknown")
                .build();
        
        return chain.filter(exchange.mutate().request(mutatedRequest).build());
    }
    
    @Override
    public int getOrder() {
        // 过滤器执行顺序，数字越小优先级越高
        return -100;
    }
    
    /**
     * 检查路径是否在白名单中
     */
    private boolean isWhiteListed(String path) {
        return WHITE_LIST.stream().anyMatch(path::startsWith);
    }
    
    /**
     * 从请求中获取 Token
     */
    private String getTokenFromRequest(ServerHttpRequest request) {
        // 从 Authorization Header 获取
        String authHeader = request.getHeaders().getFirst("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            return authHeader.substring(7);
        }
        
        // 从 URL 参数获取（备用）
        String token = request.getQueryParams().getFirst("token");
        return token;
    }
}
