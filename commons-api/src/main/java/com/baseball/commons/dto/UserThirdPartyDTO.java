package com.baseball.commons.dto;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 第三方账号绑定表 DTO
 */
@Data
@TableName("user_third_party")
public class UserThirdPartyDTO {
    
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private Long userId;
    private String platform;
    private String thirdPartyId;
    private String unionId;
    private String accessToken;
    private String refreshToken;
    private LocalDateTime tokenExpireTime;
    private LocalDateTime bindTime;
    private LocalDateTime unbindTime;
}
