package com.baseball.commons.dto;

import lombok.Data;

import java.time.LocalDateTime;

/**
 * @ author: Wang Yinuo
 * @ date: 2026-06-29:18:19
 */

@Data
public class BaseInfo {

    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
