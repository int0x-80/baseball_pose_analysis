package com.baseball.commons.dto;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 用户VIP记录表 DTO
 */
@Data
@TableName("user_vip_log")
public class UserVipLogDTO {
    
    @TableId(type = IdType.AUTO)
    private Long id;
    
    private Long userId;
    private Integer vipLevel;
    private String action;
    private Integer durationDays;
    private BigDecimal price;
    private String orderId;
    private LocalDateTime expireTime;
    private LocalDateTime createTime;
}
