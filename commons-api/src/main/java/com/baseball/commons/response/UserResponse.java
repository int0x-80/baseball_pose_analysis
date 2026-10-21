package com.baseball.commons.response;

import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 用户信息响应
 */
@Data
public class UserResponse {
    
    private Long id;
    
    // 基础信息
    private String nickname;
    private String avatarUrl;
    private Integer gender;
    private LocalDate birthday;
    private String country;
    private String province;
    private String city;
    private String language;
    
    // 状态与统计
    private Integer status;
    private Integer isVerified;
    private Integer vipLevel;
    private LocalDateTime vipExpireTime;
    private Integer points;
    private Integer totalAnalysisCount;
    private LocalDateTime lastLoginTime;
    private LocalDateTime registerTime;
    
    // 扩展字段
    private String preferences;
    private String tags;
}
