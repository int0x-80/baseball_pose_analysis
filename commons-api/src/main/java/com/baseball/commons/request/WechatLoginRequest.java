package com.baseball.commons.request;

import lombok.Data;

import javax.validation.constraints.NotBlank;

/**
 * 微信登录请求
 */
@Data
public class WechatLoginRequest {
    
    @NotBlank(message = "微信code不能为空")
    private String code;
    
    private String userInfo;
    
    private String encryptedData;
    
    private String iv;
    
    private String rawData;
    
    private String signature;
}
