package com.baseball.user.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.baseball.commons.dto.UserDTO;
import com.baseball.commons.dto.UserPointsLogDTO;
import com.baseball.user.mapper.UserMapper;
import com.baseball.user.mapper.UserPointsLogMapper;
import com.baseball.user.service.UserPointsService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 用户积分服务实现类
 */
@Slf4j
@Service
public class UserPointsServiceImpl extends ServiceImpl<UserPointsLogMapper, UserPointsLogDTO> implements UserPointsService {
    
    @Autowired
    private UserPointsLogMapper userPointsLogMapper;
    
    @Autowired
    private UserMapper userMapper;
    
    @Override
    @Transactional
    public void addPoints(Long userId, Integer points, String reason, String referenceId) {
        UserDTO user = userMapper.selectById(userId);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }
        
        Integer balanceBefore = user.getPoints();
        Integer balanceAfter = balanceBefore + points;
        
        // 更新用户积分
        user.setPoints(balanceAfter);
        userMapper.updateById(user);
        
        // 记录积分日志
        UserPointsLogDTO pointsLog = new UserPointsLogDTO();
        pointsLog.setUserId(userId);
        pointsLog.setPoints(points);
        pointsLog.setType("earn");
        pointsLog.setReason(reason);
        pointsLog.setReferenceId(referenceId);
        pointsLog.setBalanceBefore(balanceBefore);
        pointsLog.setBalanceAfter(balanceAfter);
        pointsLog.setCreateTime(LocalDateTime.now());
        
        userPointsLogMapper.insert(pointsLog);
        
        log.info("用户积分增加成功，userId: {}, points: {}, reason: {}", userId, points, reason);
    }
    
    @Override
    @Transactional
    public void spendPoints(Long userId, Integer points, String reason, String referenceId) {
        UserDTO user = userMapper.selectById(userId);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }
        
        Integer balanceBefore = user.getPoints();
        if (balanceBefore < points) {
            throw new RuntimeException("积分不足");
        }
        
        Integer balanceAfter = balanceBefore - points;
        
        // 更新用户积分
        user.setPoints(balanceAfter);
        userMapper.updateById(user);
        
        // 记录积分日志
        UserPointsLogDTO pointsLog = new UserPointsLogDTO();
        pointsLog.setUserId(userId);
        pointsLog.setPoints(-points);
        pointsLog.setType("spend");
        pointsLog.setReason(reason);
        pointsLog.setReferenceId(referenceId);
        pointsLog.setBalanceBefore(balanceBefore);
        pointsLog.setBalanceAfter(balanceAfter);
        pointsLog.setCreateTime(LocalDateTime.now());
        
        userPointsLogMapper.insert(pointsLog);
        
        log.info("用户积分消费成功，userId: {}, points: {}, reason: {}", userId, points, reason);
    }
    
    @Override
    public List<UserPointsLogDTO> getPointsLog(Long userId, Integer page, Integer size) {
        QueryWrapper<UserPointsLogDTO> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId)
                   .orderByDesc("create_time")
                   .last("LIMIT " + (page - 1) * size + ", " + size);
        
        return userPointsLogMapper.selectList(queryWrapper);
    }
    
    @Override
    public Integer getUserPoints(Long userId) {
        UserDTO user = userMapper.selectById(userId);
        if (user == null) {
            throw new RuntimeException("用户不存在");
        }
        return user.getPoints();
    }
}
