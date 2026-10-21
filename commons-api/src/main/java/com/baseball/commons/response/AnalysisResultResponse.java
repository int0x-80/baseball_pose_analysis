package com.baseball.commons.response;

import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

/**
 * 分析结果响应类
 * 包含视频元数据、基础分析结果和高级分析数据
 */
@Data
public class AnalysisResultResponse {

    // ========== 视频元数据 ==========
    @ApiModelProperty("记录ID")
    private String recordId;

    @ApiModelProperty("用户ID")
    private Long userId;

    @ApiModelProperty("消息ID")
    private String messageId;

    @ApiModelProperty("原始视频URL")
    private String videoUrl;

    @ApiModelProperty("骨架视频URL")
    private String skeletonVideoUrl;

    @ApiModelProperty("视频分析状态: 0-分析中, 1-完成, 2-失败")
    private Integer status;

    @ApiModelProperty("动作类型: batting-击球, pitching-投球 (来自 video_metadata)")
    private String type;

    @ApiModelProperty("骨骼视频文件名")
    private String skeletonVideoName;

    @ApiModelProperty("JSON分析结果文件名")
    private String analysisJsonName;

    @ApiModelProperty("帧率")
    private Integer fps;

    @ApiModelProperty("视频宽度")
    private Integer videoWidth;

    @ApiModelProperty("视频高度")
    private Integer videoHeight;

    @ApiModelProperty("总帧数")
    private Integer totalFrames;

    // ========== 基础分析结果 ==========
    @ApiModelProperty("动作类型: batting-击球, pitching-投球")
    private String actionType;

    // 手臂速度
    @ApiModelProperty("左手速度(m/s)")
    private BigDecimal leftSpeedMs;

    @ApiModelProperty("右手速度(m/s)")
    private BigDecimal rightSpeedMs;

    @ApiModelProperty("左手速度(km/h)")
    private BigDecimal leftSpeedKmH;

    @ApiModelProperty("右手速度(km/h)")
    private BigDecimal rightSpeedKmH;

    // 挥棒速度
    @ApiModelProperty("最大挥棒速度(m/s)")
    private BigDecimal maxBatSpeedMs;

    @ApiModelProperty("最大挥棒速度(km/h)")
    private BigDecimal maxBatSpeedKmH;

    @ApiModelProperty("平均挥棒速度(m/s)")
    private BigDecimal avgBatSpeedMs;

    @ApiModelProperty("平均挥棒速度(km/h)")
    private BigDecimal avgBatSpeedKmH;

    // 挥棒轨迹
    @ApiModelProperty("轨迹点数")
    private Integer trajectoryPoints;

    @ApiModelProperty("轨迹总长度")
    private BigDecimal pathLength;

    @ApiModelProperty("直线距离")
    private BigDecimal directDistance;

    @ApiModelProperty("路径比例")
    private BigDecimal pathRatio;

    @ApiModelProperty("挥棒角度(度)")
    private BigDecimal swingAngleDeg;

    @ApiModelProperty("轨迹类型: arc/slight_curve/straight")
    private String trajectoryType;

    // 腿部分析
    @ApiModelProperty("最大转胯幅度(mm)")
    private BigDecimal maxHipRotationMm;

    @ApiModelProperty("平均转胯幅度(mm)")
    private BigDecimal avgHipRotationMm;

    @ApiModelProperty("髋部稳定性")
    private BigDecimal hipStability;

    // 躯干分析
    @ApiModelProperty("最大扭转角度(度)")
    private BigDecimal maxTwistAngleDeg;

    @ApiModelProperty("平均扭转角度(度)")
    private BigDecimal avgTwistAngleDeg;

    @ApiModelProperty("肩髋角度差(度)")
    private BigDecimal shoulderHipDiffDeg;

    // ========== 高级分析数据 ==========
    
    @ApiModelProperty("速度曲线分析")
    private Map<String, Object> velocityAnalysis;

    @ApiModelProperty("关节角度分析")
    private Map<String, Object> jointAnalysis;

    @ApiModelProperty("身体对称性分析")
    private Map<String, Object> symmetryAnalysis;

    @ApiModelProperty("动作阶段检测")
    private Map<String, Object> actionPhases;

    @ApiModelProperty("轨迹平滑度分析")
    private Map<String, Object> trajectorySmoothness;

    @ApiModelProperty("能量传递效率分析")
    private Map<String, Object> powerTransfer;

    // ========== 错误信息 ==========
    @ApiModelProperty("错误信息")
    private String errorMessage;

    @ApiModelProperty("错误码")
    private String errorCode;
}
