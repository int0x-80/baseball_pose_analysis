package com.baseball.commons.response;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * 积分记录响应
 */
@Data
public class PointsLogResponse {
    
    private Long id;
    
    private Integer points;
    
    private String type;
    
    private String reason;
    
    private String referenceId;
    
    private Integer balanceBefore;
    
    private Integer balanceAfter;
    
    private LocalDateTime createTime;
}
