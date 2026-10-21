package com.baseball.user.service;

import com.baseball.commons.dto.UserPointsLogDTO;

import java.util.List;

/**
 * 用户积分服务接口
 */
public interface UserPointsService {
    
    /**
     * 增加积分
     */
    void addPoints(Long userId, Integer points, String reason, String referenceId);
    
    /**
     * 消费积分
     */
    void spendPoints(Long userId, Integer points, String reason, String referenceId);
    
    /**
     * 获取用户积分记录
     */
    List<UserPointsLogDTO> getPointsLog(Long userId, Integer page, Integer size);
    
    /**
     * 获取用户当前积分
     */
    Integer getUserPoints(Long userId);
}
