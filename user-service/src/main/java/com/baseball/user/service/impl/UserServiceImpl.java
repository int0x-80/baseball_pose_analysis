package com.baseball.user.service.impl;

import com.alibaba.cloud.commons.lang.StringUtils;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.baseball.commons.constants.RedisConstants;
import com.baseball.commons.constants.UserConstants;
import com.baseball.commons.dto.UserDTO;
import com.baseball.commons.dto.UserLoginLogDTO;
import com.baseball.commons.request.PhoneLoginRequest;
import com.baseball.commons.request.UserRegisterRequest;
import com.baseball.commons.request.UserUpdateRequest;
import com.baseball.commons.request.WechatLoginRequest;
import com.baseball.commons.response.LoginResponse;
import com.baseball.commons.response.UserResponse;
import com.baseball.commons.util.RedisUtils;
import com.baseball.user.config.JwtUtil;
import com.baseball.user.mapper.UserLoginLogMapper;
import com.baseball.user.mapper.UserMapper;
import com.baseball.user.service.UserService;
import lombok.extern.slf4j.Slf4j;
import org.apache.catalina.User;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.DigestUtils;

import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.concurrent.TimeUnit;

import static com.baseball.commons.util.RedisUtils.secondsUntilMidnight;

/**
 * 用户服务实现类
 */
@Slf4j
@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, UserDTO> implements UserService {
    
    @Autowired
    private UserMapper userMapper;
    
    @Autowired
    private UserLoginLogMapper userLoginLogMapper;
    
    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private StringRedisTemplate stringRedisTemplate;
    
    @Override
    @Transactional
    public LoginResponse wechatLogin(WechatLoginRequest request, String platform) {
        // TODO: 调用微信API获取openid和unionid
        String openId = "mock_openid_" + System.currentTimeMillis();
        String unionId = "mock_unionid_" + System.currentTimeMillis();
        
        // 查询用户是否存在
        UserDTO user = userMapper.selectByOpenIdWechat(openId);
        boolean isNewUser = false;
        
        if (user == null) {
            // 新用户，创建账号
            isNewUser = true;
            user = new UserDTO();
            user.setOpenIdWechat(openId);
            user.setUnionId(unionId);
            user.setNickname("微信用户");
            user.setAvatarUrl("");
            user.setGender(0);
            user.setStatus(1);
            user.setIsVerified(0);
            user.setVipLevel(0);
            user.setPoints(0);
            user.setTotalAnalysisCount(0);
            user.setRegisterTime(LocalDateTime.now());
            user.setLastLoginTime(LocalDateTime.now());
            user.setLastLoginPlatform(platform);
            
            userMapper.insert(user);
            log.info("新用户注册成功，userId: {}", user.getId());
        } else {
            // 老用户，更新登录时间
            user.setLastLoginTime(LocalDateTime.now());
            user.setLastLoginPlatform(platform);
            int addPoint = tryAwardDailyLoginPoints(user.getId(), UserConstants.USER_AWARD_POINT_LOGIN);
            int userPoint = user.getPoints();
            int newPoints = userPoint + addPoint;
            user.setPoints(newPoints);
            userMapper.updateById(user);
            log.info("用户登录成功，user: {}", user);
        }
        
        // 记录登录日志
        recordLoginLog(user.getId(), platform, "wechat");
        
        // 构建响应
        return buildLoginResponse(user, isNewUser, platform);
    }
    
    @Override
    @Transactional
    public LoginResponse phoneLogin(PhoneLoginRequest request, String platform) {
        // TODO: 验证短信验证码
        String phone = request.getPhone();
        
        // 查询用户是否存在
        UserDTO user = userMapper.selectByPhone(phone);
        boolean isNewUser = false;
        
        if (user == null) {
            // 新用户，创建账号
            isNewUser = true;
            user = new UserDTO();
            user.setPhone(phone);
            user.setNickname("手机用户");
            user.setAvatarUrl("");
            user.setGender(0);
            user.setStatus(1);
            user.setIsVerified(0);
            user.setVipLevel(0);
            user.setPoints(0);
            user.setTotalAnalysisCount(0);
            user.setRegisterTime(LocalDateTime.now());
            user.setLastLoginTime(LocalDateTime.now());
            user.setLastLoginPlatform(platform);
            
            userMapper.insert(user);
            log.info("新用户注册成功，userId: {}", user.getId());
        } else {
            // 老用户，更新登录时间
            user.setLastLoginTime(LocalDateTime.now());
            user.setLastLoginPlatform(platform);
            int addPoint = tryAwardDailyLoginPoints(user.getId(), UserConstants.USER_AWARD_POINT_LOGIN);
            int userPoint = user.getPoints();
            int newPoints = userPoint + addPoint;
            user.setPoints(newPoints);
            userMapper.updateById(user);
            log.info("用户登录成功，userId: {}", user.getId());
        }
        
        // 记录登录日志
        recordLoginLog(user.getId(), platform, "phone");
        
        // 构建响应
        return buildLoginResponse(user, isNewUser, platform);
    }
    
    @Override
    @Transactional
    public LoginResponse register(UserRegisterRequest request, String platform) {
        // TODO: 验证短信验证码
        String phone = request.getPhone();
        
        // 检查手机号是否已注册
        UserDTO existingUser = userMapper.selectByPhone(phone);
        if (existingUser != null) {
            log.info("用户已经注册，userId: {}", existingUser.getId());
            return null;
        }
        
        // 创建新用户
        UserDTO user = new UserDTO();
        user.setPhone(phone);
        user.setPasswordHash(hashPassword(request.getPassword()));
        user.setNickname(request.getNickname() != null ? request.getNickname() : "新用户");
        user.setAvatarUrl(request.getAvatarUrl() != null ? request.getAvatarUrl() : "");
        user.setGender(request.getGender() != null ? request.getGender() : 0);
        user.setStatus(1);
        user.setIsVerified(0);
        user.setVipLevel(0);
        user.setPoints(100); // 新用户赠送100积分
        user.setTotalAnalysisCount(0);
        user.setRegisterTime(LocalDateTime.now());
        user.setLastLoginTime(LocalDateTime.now());
        user.setLastLoginPlatform(platform);
        
        userMapper.insert(user);
        log.info("用户注册成功，userId: {}", user.getId());
        
        // 记录登录日志
        recordLoginLog(user.getId(), platform, "register");
        
        // 构建响应
        return buildLoginResponse(user, true, platform);
    }
    
    @Override
    public UserResponse getUserInfo(Long userId) {
        UserDTO user = userMapper.selectById(userId);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }
        
        UserResponse response = new UserResponse();
        BeanUtils.copyProperties(user, response);
        
        return response;
    }
    
    @Override
    @Transactional
    public void updateUser(Long userId, UserUpdateRequest request) {
        UserDTO user = userMapper.selectById(userId);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }
        
        // 更新用户信息
        if (request.getNickname() != null) {
            user.setNickname(request.getNickname());
        }
        if (request.getAvatarUrl() != null) {
            user.setAvatarUrl(request.getAvatarUrl());
        }
        if (request.getGender() != null) {
            user.setGender(request.getGender());
        }
        if (request.getBirthday() != null) {
            user.setBirthday(request.getBirthday());
        }
        if (request.getCountry() != null) {
            user.setCountry(request.getCountry());
        }
        if (request.getProvince() != null) {
            user.setProvince(request.getProvince());
        }
        if (request.getCity() != null) {
            user.setCity(request.getCity());
        }
        if (request.getEmail() != null) {
            user.setEmail(request.getEmail());
        }
        if (request.getPreferences() != null) {
            user.setPreferences(request.getPreferences());
        }
        
        userMapper.updateById(user);
        log.info("用户信息更新成功，userId: {}", userId);
    }
    
    @Override
    public void incrementAnalysisCount(Long userId) {
        userMapper.incrementAnalysisCount(userId);
    }
    
    @Override
    public UserDTO getUserByPhone(String phone) {
        return userMapper.selectByPhone(phone);
    }
    
    @Override
    public UserDTO getUserByOpenIdWechat(String openIdWechat) {
        return userMapper.selectByOpenIdWechat(openIdWechat);
    }
    
    /**
     * 记录登录日志
     */
    private void recordLoginLog(Long userId, String platform, String loginType) {
        UserLoginLogDTO log = new UserLoginLogDTO();
        log.setUserId(userId);
        log.setPlatform(platform);
        log.setLoginType(loginType);
        log.setLoginTime(LocalDateTime.now());
        
        userLoginLogMapper.insert(log);
    }
    
    /**
     * 构建登录响应
     */
    private LoginResponse buildLoginResponse(UserDTO user, boolean isNewUser, String platform) {
        LoginResponse response = new LoginResponse();
        response.setUserId(user.getId());
        response.setNickname(user.getNickname());
        response.setAvatarUrl(user.getAvatarUrl());
        response.setVipLevel(user.getVipLevel());
        response.setPoints(user.getPoints());
        response.setIsNewUser(isNewUser);
        response.setPlatform(platform);
        
        // 生成 JWT Token
        String token = jwtUtil.generateToken(user.getId(), platform);
        response.setToken(token);
        
        return response;
    }

    public int tryAwardDailyLoginPoints(Long userId, int awardType) {
        log.info("tryAwardDailyLoginPoints(userId:{}, awardType:{})", userId, awardType);
        int awardPoints = 0;
        if (awardType == UserConstants.USER_AWARD_POINT_LOGIN) {
            log.info("USER_AWARD_POINT_LOGIN: {}", awardType);
            String key = RedisUtils.generateUserLoginKeyByUserId(userId);
            String redisStr = stringRedisTemplate.opsForValue().get(key);
            if(redisStr == null) {
                stringRedisTemplate.opsForValue().setIfAbsent(key, "1", secondsUntilMidnight(), TimeUnit.SECONDS);
                awardPoints = 1;
            }
        } else if (awardType == UserConstants.USER_AWARD_POINT_UPLOAD_VIDEO) {
            String key = RedisUtils.generateUserUploadKeyByUserId(userId);
            String redisStr = stringRedisTemplate.opsForValue().get(key);
            if(redisStr == null) {
                stringRedisTemplate.opsForValue().setIfAbsent(key, "1", secondsUntilMidnight(), TimeUnit.SECONDS);
                awardPoints = 10;
            }
        }
        return awardPoints;
    }

    
    /**
     * 密码哈希
     */
    private String hashPassword(String password) {
        return DigestUtils.md5DigestAsHex(password.getBytes(StandardCharsets.UTF_8));
    }

    private String getRedisString(Long userId) {
        return RedisConstants.LOGIN + userId;
    }
}
