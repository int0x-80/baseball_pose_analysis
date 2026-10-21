package com.baseball.commons.dto;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.util.List;
import java.util.Map;

/**
 * 评估结果DTO - Java 评估服务生成的评估数据
 */
@Data
@ApiModel("评估结果")
public class VideoEvaluationResult {

    @ApiModelProperty("记录ID")
    private String recordId;

    @ApiModelProperty("用户ID")
    private Long userId;

    @ApiModelProperty("动作类型: batting-击球, pitching-投球")
    private String actionType;

    // ========== 评分 ==========
    @ApiModelProperty("总评分(0-100)")
    private Double overallScore;

    @ApiModelProperty("等级: A/B/C/D/E")
    private String grade;

    @ApiModelProperty("各项得分")
    private Map<String, Double> scores;

    // ========== 问题诊断 ==========
    @ApiModelProperty("问题列表")
    private List<IssueDTO> issues;

    @ApiModelProperty("建议总结")
    private String summary;

    // ========== 积分 ==========
    @ApiModelProperty("获得积分")
    private Integer pointsEarned;

    @Data
    @ApiModel("问题")
    public static class IssueDTO {
        @ApiModelProperty("问题类型")
        private String type;

        @ApiModelProperty("严重程度")
        private String severity;

        @ApiModelProperty("描述")
        private String description;

        @ApiModelProperty("建议")
        private String suggestion;
    }
}
