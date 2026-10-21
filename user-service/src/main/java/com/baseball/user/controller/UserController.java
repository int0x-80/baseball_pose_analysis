package com.baseball.user.controller;

import com.baseball.commons.domain.BaseResponse;
import com.baseball.commons.dto.UserPointsLogDTO;
import com.baseball.commons.request.PhoneLoginRequest;
import com.baseball.commons.request.UserRegisterRequest;
import com.baseball.commons.request.UserUpdateRequest;
import com.baseball.commons.request.WechatLoginRequest;
import com.baseball.commons.response.LoginResponse;
import com.baseball.commons.response.UserResponse;
import com.baseball.user.config.UserContext;
import com.baseball.user.service.UserPointsService;
import com.baseball.user.service.UserService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import javax.validation.Valid;
import java.util.List;

/**
 * 用户控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/user")
@Api(tags = "用户管理")
public class UserController {

    @Autowired
    private UserService userService;

    @Autowired
    private UserPointsService userPointsService;

    @PostMapping("/login/wechat")
    @ApiOperation("微信登录")
    public BaseResponse<LoginResponse> wechatLogin(
            @Valid @RequestBody WechatLoginRequest request,
            @RequestParam(defaultValue = "wechat") String platform) {
        log.info("微信登录请求，platform: {}", platform);

        LoginResponse response = userService.wechatLogin(request, platform);
        return BaseResponse.success(response);
    }

    @PostMapping("/login/phone")
    @ApiOperation("手机号登录")
    public BaseResponse<LoginResponse> phoneLogin(
            @Valid @RequestBody PhoneLoginRequest request,
            @RequestParam(defaultValue = "app") String platform) {
        log.info("手机号登录请求，platform: {}", platform);

        LoginResponse response = userService.phoneLogin(request, platform);
        return BaseResponse.success(response);
    }

    @PostMapping("/register")
    @ApiOperation("用户注册")
    public BaseResponse<LoginResponse> register(
            @Valid @RequestBody UserRegisterRequest request,
            @RequestParam(defaultValue = "app") String platform) {
        log.info("用户注册请求，platform: {}", platform);

        LoginResponse response = userService.register(request, platform);
        if (response == null) {
            return BaseResponse.fail("用户已经注册");
        }

        return BaseResponse.success(response);
    }

    @GetMapping("/info")
    @ApiOperation("获取用户信息")
    public BaseResponse<UserResponse> getUserInfo() {
        Long userId = UserContext.getCurrentUserId();
        log.info("获取用户信息，userId: {}", userId);

        UserResponse response = userService.getUserInfo(userId);
        return BaseResponse.success(response);
    }

    @PutMapping("/update")
    @ApiOperation("更新用户信息")
    public BaseResponse<String> updateUser(@Valid @RequestBody UserUpdateRequest request) {
        Long userId = UserContext.getCurrentUserId();
        log.info("更新用户信息，userId: {}", userId);

        userService.updateUser(userId, request);
        return BaseResponse.success("更新成功");
    }

    @GetMapping("/points")
    @ApiOperation("获取用户积分")
    public BaseResponse<Integer> getUserPoints() {
        Long userId = UserContext.getCurrentUserId();
        log.info("获取用户积分，userId: {}", userId);

        Integer points = userPointsService.getUserPoints(userId);
        return BaseResponse.success(points);
    }

    @GetMapping("/points/log")
    @ApiOperation("获取积分记录")
    public BaseResponse<List<UserPointsLogDTO>> getPointsLog(
            @RequestParam(defaultValue = "1") Integer page,
            @RequestParam(defaultValue = "10") Integer size) {
        Long userId = UserContext.getCurrentUserId();
        log.info("获取积分记录，userId: {}, page: {}, size: {}", userId, page, size);

        List<UserPointsLogDTO> logs = userPointsService.getPointsLog(userId, page, size);
        return BaseResponse.success(logs);
    }
}
