package com.baseball.user.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

/**
 * JWT 拦截器
 */
@Slf4j
@Component
public class JwtInterceptor implements HandlerInterceptor {
    
    @Autowired
    private JwtUtil jwtUtil;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // 放行 OPTIONS 请求（CORS 预检）
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }
        
        // 获取 Token
        String token = getTokenFromRequest(request);
        
        if (token == null || token.isEmpty()) {
            sendError(response, "401", "未提供认证Token");
            return false;
        }
        
        // 验证 Token
        if (!jwtUtil.validateToken(token)) {
            sendError(response, "401", "Token无效或已过期");
            return false;
        }
        
        // 将用户信息存入 request attribute
        Long userId = jwtUtil.getUserIdFromToken(token);
        String platform = jwtUtil.getPlatformFromToken(token);
        request.setAttribute("userId", userId);
        request.setAttribute("platform", platform);
        
        log.debug("用户认证通过，userId: {}, platform: {}", userId, platform);
        return true;
    }
    
    /**
     * 从请求中获取 Token
     */
    private String getTokenFromRequest(HttpServletRequest request) {
        // 优先从 Header 中获取
        String token = request.getHeader("Authorization");
        
        if (token != null && token.startsWith("Bearer ")) {
            return token.substring(7);
        }
        
        // 从参数中获取（备用）
        token = request.getParameter("token");
        
        return token;
    }
    
    /**
     * 发送错误响应
     */
    private void sendError(HttpServletResponse response, String code, String message) throws IOException {
        response.setContentType("application/json;charset=UTF-8");
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        
        Map<String, Object> result = new HashMap<>();
        result.put("code", code);
        result.put("message", message);
        result.put("data", null);
        
        response.getWriter().write(objectMapper.writeValueAsString(result));
    }
}
