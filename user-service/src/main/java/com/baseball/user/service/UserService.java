package com.baseball.user.service;

import com.baseball.commons.dto.UserDTO;
import com.baseball.commons.request.PhoneLoginRequest;
import com.baseball.commons.request.UserRegisterRequest;
import com.baseball.commons.request.UserUpdateRequest;
import com.baseball.commons.request.WechatLoginRequest;
import com.baseball.commons.response.LoginResponse;
import com.baseball.commons.response.UserResponse;

/**
 * 用户服务接口
 */
public interface UserService  {
    
    /**
     * 微信登录
     */
    LoginResponse wechatLogin(WechatLoginRequest request, String platform);
    
    /**
     * 手机号登录
     */
    LoginResponse phoneLogin(PhoneLoginRequest request, String platform);
    
    /**
     * 用户注册
     */
    LoginResponse register(UserRegisterRequest request, String platform);
    
    /**
     * 获取用户信息
     */
    UserResponse getUserInfo(Long userId);
    
    /**
     * 更新用户信息
     */
    void updateUser(Long userId, UserUpdateRequest request);
    
    /**
     * 增加分析次数
     */
    void incrementAnalysisCount(Long userId);
    
    /**
     * 根据手机号查询用户
     */
    UserDTO getUserByPhone(String phone);
    
    /**
     * 根据微信OpenID查询用户
     */
    UserDTO getUserByOpenIdWechat(String openIdWechat);
}
