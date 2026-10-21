package com.baseball.commons.request;

import lombok.Data;

import javax.validation.constraints.Email;
import javax.validation.constraints.Size;
import java.time.LocalDate;

/**
 * 用户信息更新请求
 */
@Data
public class UserUpdateRequest {
    
    @Size(max = 50, message = "昵称长度不能超过50个字符")
    private String nickname;
    
    private String avatarUrl;
    
    private Integer gender;
    
    private LocalDate birthday;
    
    private String country;
    
    private String province;
    
    private String city;
    
    @Email(message = "邮箱格式不正确")
    private String email;
    
    private String preferences;
}
