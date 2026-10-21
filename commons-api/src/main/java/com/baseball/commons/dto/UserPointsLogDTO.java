package com.baseball.commons.dto;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 用户积分记录表 DTO
 */
@Data
@TableName("user_points_log")
public class UserPointsLogDTO {
    
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private Long userId;
    private Integer points;
    private String type;
    private String reason;
    private String referenceId;
    private Integer balanceBefore;
    private Integer balanceAfter;
    private LocalDateTime createTime;
}
