package com.baseball.commons.request;

import lombok.Data;

import javax.validation.constraints.NotBlank;
import javax.validation.constraints.Pattern;
import javax.validation.constraints.Size;

/**
 * 用户注册请求
 */
@Data
public class UserRegisterRequest {
    
    @NotBlank(message = "手机号不能为空")
    @Pattern(regexp = "^1[3-9]\\d{9}$", message = "手机号格式不正确")
    private String phone;
    
    @NotBlank(message = "验证码不能为空")
    private String code;
    
    @Size(min = 6, max = 20, message = "密码长度必须在6-20位之间")
    private String password;
    
    private String nickname;
    
    private String avatarUrl;
    
    private Integer gender;
}
