package com.baseball.commons.dto;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 分析结果DTO - Python 服务输出的原始分析数据（仅包含运动分析数据）
 */
@Data
@ApiModel("分析结果")
@TableName("video_analysis_result")
public class VideoAnalysisResult {

    @TableId(type = IdType.AUTO)
    @ApiModelProperty("主键ID")
    private Long id;

    @ApiModelProperty("记录ID")
    private String recordId;

    @ApiModelProperty("用户ID")
    private Long userId;

    @ApiModelProperty("动作类型: batting-击球, pitching-投球")
    private String actionType;

    @ApiModelProperty("总评分(0-100)")
    private BigDecimal overallScore;

    @ApiModelProperty("等级(A/B/C/D/E)")
    private String grade;

    // ========== 手臂速度 ==========
    @ApiModelProperty("左手速度(m/s)")
    private BigDecimal leftSpeedMs;

    @ApiModelProperty("右手速度(m/s)")
    private BigDecimal rightSpeedMs;

    @ApiModelProperty("左手速度(km/h)")
    private BigDecimal leftSpeedKmH;

    @ApiModelProperty("右手速度(km/h)")
    private BigDecimal rightSpeedKmH;

    // ========== 挥棒速度 ==========
    @ApiModelProperty("最大挥棒速度(m/s)")
    private BigDecimal maxBatSpeedMs;

    @ApiModelProperty("最大挥棒速度(km/h)")
    private BigDecimal maxBatSpeedKmH;

    @ApiModelProperty("平均挥棒速度(m/s)")
    private BigDecimal avgBatSpeedMs;

    @ApiModelProperty("平均挥棒速度(km/h)")
    private BigDecimal avgBatSpeedKmH;

    // ========== 挥棒轨迹 ==========
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

    // ========== 腿部分析 ==========
    @ApiModelProperty("最大转胯幅度(mm)")
    private BigDecimal maxHipRotationMm;

    @ApiModelProperty("平均转胯幅度(mm)")
    private BigDecimal avgHipRotationMm;

    @ApiModelProperty("髋部稳定性")
    private BigDecimal hipStability;

    // ========== 躯干分析 ==========
    @ApiModelProperty("最大扭转角度(度)")
    private BigDecimal maxTwistAngleDeg;

    @ApiModelProperty("平均扭转角度(度)")
    private BigDecimal avgTwistAngleDeg;

    @ApiModelProperty("肩髋角度差(度)")
    private BigDecimal shoulderHipDiffDeg;

    // ========== 高级分析数据（JSON 存储） ==========
    
    @ApiModelProperty("速度曲线分析(JSON)")
    private String velocityAnalysis;

    @ApiModelProperty("关节角度分析(JSON)")
    private String jointAnalysis;

    @ApiModelProperty("身体对称性分析(JSON)")
    private String symmetryAnalysis;

    @ApiModelProperty("动作阶段检测(JSON)")
    private String actionPhases;

    @ApiModelProperty("轨迹平滑度分析(JSON)")
    private String trajectorySmoothness;

    @ApiModelProperty("能量传递效率分析(JSON)")
    private String powerTransfer;

    @ApiModelProperty("原始数据JSON")
    private String rawData;

    @ApiModelProperty("创建时间")
    private LocalDateTime createTime;

    @ApiModelProperty("更新时间")
    private LocalDateTime updateTime;
}
