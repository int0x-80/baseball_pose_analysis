package com.baseball.commons.util;

import java.time.Duration;
import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * @ author: Wang Yinuo
 * @ date: 2026-07-09:18:13
 */
public class RedisUtils {


    public static String BLACK_DEVICE_PREFIX = "black-device-";

    public static String generateUserLoginKeyByUserId(Long userId) {
        return "login:reward:" + userId + ":" + LocalDate.now();
    }

    public static String generateUserUploadKeyByUserId(Long userId) {
        return "upload:reward:" + userId + ":" + LocalDate.now();
    }

    public static String generateTokenKey(String phoneNumber, String identity, String tokenType) {
        String tokenCodePrefix = "token-";
        return tokenCodePrefix + phoneNumber + "-" + identity + "-" + tokenType;
    }

    public static long secondsUntilMidnight() {
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime midnight = now.toLocalDate().plusDays(1).atStartOfDay();
        return Duration.between(now, midnight).getSeconds();
    }
}
