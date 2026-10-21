package com.baseball.user.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baseball.commons.dto.VideoMetadata;
import com.baseball.commons.response.VideoRecordResponse;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 视频元数据 Mapper
 */
@Mapper
public interface VideoMetadataMapper extends BaseMapper<VideoMetadata> {

    /**
     * 根据记录ID查询视频元数据
     *
     * @param recordId 记录ID
     * @return 视频元数据
     */
    VideoMetadata selectByRecordId(@Param("recordId") String recordId);

    /**
     * 查询用户的视频记录（分页）
     *
     * @param userId 用户ID
     * @param startDate 开始时间
     * @param endDate 结束时间
     * @param actionType 动作类型
     * @param status 状态
     * @param offset 偏移量
     * @param limit 限制数量
     * @param sortBy 排序字段
     * @param sortOrder 排序方向
     * @return 视频记录列表
     */
    List<VideoRecordResponse> selectUserVideoRecords(
            @Param("userId") Long userId,
            @Param("startDate") LocalDateTime startDate,
            @Param("endDate") LocalDateTime endDate,
            @Param("actionType") String actionType,
            @Param("status") Integer status,
            @Param("offset") Integer offset,
            @Param("limit") Integer limit,
            @Param("sortBy") String sortBy,
            @Param("sortOrder") String sortOrder
    );

    /**
     * 统计用户的视频记录总数
     *
     * @param userId 用户ID
     * @param startDate 开始时间
     * @param endDate 结束时间
     * @param actionType 动作类型
     * @param status 状态
     * @return 记录总数
     */
    Long countUserVideoRecords(
            @Param("userId") Long userId,
            @Param("startDate") LocalDateTime startDate,
            @Param("endDate") LocalDateTime endDate,
            @Param("actionType") String actionType,
            @Param("status") Integer status
    );

    /**
     * 查询用户某个月的每日记录数（用于日历展示）
     *
     * @param userId 用户ID
     * @param year 年份
     * @param month 月份
     * @return 每日记录数列表
     */
    List<DailyRecordCount> selectDailyRecordCount(
            @Param("userId") Long userId,
            @Param("year") Integer year,
            @Param("month") Integer month
    );

    /**
     * 每日记录数 DTO
     */
    class DailyRecordCount {
        private Integer day;
        private Integer count;

        public Integer getDay() {
            return day;
        }

        public void setDay(Integer day) {
            this.day = day;
        }

        public Integer getCount() {
            return count;
        }

        public void setCount(Integer count) {
            this.count = count;
        }
    }
}
