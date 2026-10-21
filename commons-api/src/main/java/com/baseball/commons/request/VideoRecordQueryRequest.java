package com.baseball.commons.request;

import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import javax.validation.constraints.Max;
import javax.validation.constraints.Min;
import java.time.LocalDate;

/**
 * 视频分析记录查询请求
 */
@Data
public class VideoRecordQueryRequest {
    
    /**
     * 开始日期（包含）
     */
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate startDate;
    
    /**
     * 结束日期（包含）
     */
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate endDate;
    
    /**
     * 动作类型筛选：batting-击球, pitching-投球，null表示全部
     */
    private String actionType;
    
    /**
     * 状态筛选：0-分析中, 1-已完成, 2-失败，null表示全部
     */
    private Integer status;
    
    /**
     * 页码，从1开始
     */
    @Min(value = 1, message = "页码必须大于0")
    private Integer pageNum = 1;
    
    /**
     * 每页大小
     */
    @Min(value = 1, message = "每页大小必须大于0")
    @Max(value = 100, message = "每页大小不能超过100")
    private Integer pageSize = 10;
    
    /**
     * 排序字段：createTime-创建时间, updateTime-更新时间
     */
    private String sortBy = "createTime";
    
    /**
     * 排序方向：asc-升序, desc-降序
     */
    private String sortOrder = "desc";
}
