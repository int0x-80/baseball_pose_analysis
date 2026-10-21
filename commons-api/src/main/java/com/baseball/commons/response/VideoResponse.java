package com.baseball.commons.response;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * @ author: Wang Yinuo
 * @ date: 2026-06-04:19:03
 */

@NoArgsConstructor
@AllArgsConstructor
@Data
public class VideoResponse {
    String objectName;
    String downloadUrl;
    String fileName;
    String expireMinutes;
    long fileSize;
}
