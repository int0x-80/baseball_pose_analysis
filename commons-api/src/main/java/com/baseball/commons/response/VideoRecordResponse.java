package com.baseball.commons.response;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 视频分析记录响应
 */
@Data
public class VideoRecordResponse {
    
    /**
     * 记录ID
     */
    private String recordId;
    
    /**
     * 动作类型：batting-击球, pitching-投球
     */
    private String actionType;
    
    /**
     * 状态：0-分析中, 1-已完成, 2-失败
     */
    private Integer status;
    
    /**
     * 评分（仅已完成时有值）
     */
    private Double overallScore;
    
    /**
     * 等级（仅已完成时有值）
     */
    private String grade;
    
    /**
     * 视频文件名
     */
    private String skeletonVideoName;
    
    /**
     * 创建时间
     */
    private LocalDateTime createTime;
    
    /**
     * 更新时间
     */
    private LocalDateTime updateTime;

    /**
     * 挥棒最大速度 (km/h)
     */
    private Double maxBatSpeedKmH;

    /**
     * 左手最大速度 (km/h)
     */
    private Double leftSpeedKmH;

    /**
     * 右手最大速度 (km/h)
     */
    private Double rightSpeedKmH;
}
