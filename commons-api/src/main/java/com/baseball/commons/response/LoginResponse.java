package com.baseball.commons.response;

import lombok.Data;

/**
 * 登录响应
 */
@Data
public class LoginResponse {
    
    private String token;
    
    private Long userId;
    
    private String nickname;
    
    private String avatarUrl;
    
    private Integer vipLevel;
    
    private Integer points;
    
    private Boolean isNewUser;
    
    private String platform;
}
