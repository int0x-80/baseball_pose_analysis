package com.baseball.commons.response;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

/**
 * 视频元数据DTO - 视频文件相关信息
 */
@Data
@ApiModel("视频元数据")
public class VideoMetadataResponse {
    @ApiModelProperty("用户ID")
    private Long userId;

    @ApiModelProperty("记录ID")
    private String recordId;

    @ApiModelProperty("原始视频URL")
    private String videoUrl;

    @ApiModelProperty("视频分析状态")
    private int status;

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
}
