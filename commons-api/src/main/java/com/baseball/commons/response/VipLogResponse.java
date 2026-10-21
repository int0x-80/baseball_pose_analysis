package com.baseball.commons.response;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * VIP记录响应
 */
@Data
public class VipLogResponse {
    
    private Long id;
    
    private Integer vipLevel;
    
    private String action;
    
    private Integer durationDays;
    
    private BigDecimal price;
    
    private String orderId;
    
    private LocalDateTime expireTime;
    
    private LocalDateTime createTime;
}
