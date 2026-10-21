package com.baseball.commons.dto;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 用户登录记录表 DTO
 */
@Data
@TableName("user_login_log")
public class UserLoginLogDTO {
    
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private Long userId;
    private String platform;
    private String loginType;
    private String ipAddress;
    private String userAgent;
    private String deviceInfo;
    private LocalDateTime loginTime;
}
