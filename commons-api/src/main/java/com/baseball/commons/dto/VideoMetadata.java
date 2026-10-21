package com.baseball.commons.dto;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 视频元数据DTO - 视频文件相关信息
 */
@Data
@ApiModel("视频元数据")
@TableName("video_metadata")
public class VideoMetadata {

    @TableId(type = IdType.AUTO)
    @ApiModelProperty("主键ID")
    private Long id;

    @ApiModelProperty("用户ID")
    private Long userId;

    @ApiModelProperty("记录ID")
    private String recordId;

    @ApiModelProperty("MessageId")
    private String messageId;

    @ApiModelProperty("原始视频URL")
    private String videoUrl;

    @ApiModelProperty("骨架视频")
    private String skeletonVideoUrl;

    @ApiModelProperty("视频分析状态: 0-分析中, 1-完成, 2-失败")
    private Integer status;

    @ApiModelProperty("动作类型: batting-击球, pitching-投球")
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

    @ApiModelProperty("创建时间")
    private LocalDateTime createTime;

    @ApiModelProperty("更新时间")
    private LocalDateTime updateTime;
}
