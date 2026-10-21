package com.baseball.commons.dto;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 用户表 DTO
 */
@Data
@TableName("user")
public class UserDTO {
    
    @TableId(type = IdType.AUTO)
    private Long id;
    
    // 核心身份
    private String unionId;
    private String openIdWechat;
    private String openIdApp;
    private String phone;
    private String email;
    private String passwordHash;
    
    // 基础信息
    private String nickname;
    private String avatarUrl;
    private Integer gender;
    private LocalDate birthday;
    private String country;
    private String province;
    private String city;
    private String language;
    
    // 平台特定
    private String wechatSessionKey;
    private String wechatUnionId;
    private String appleId;
    private String googleId;
    private String lastLoginPlatform;
    private String deviceInfo;
    
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
    private String extraData;
    
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
