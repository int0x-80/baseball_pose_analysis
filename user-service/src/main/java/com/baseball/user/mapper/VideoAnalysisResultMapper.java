package com.baseball.user.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baseball.commons.dto.VideoAnalysisResult;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

/**
 * 视频分析结果 Mapper
 */
@Mapper
public interface VideoAnalysisResultMapper extends BaseMapper<VideoAnalysisResult> {

    /**
     * 根据记录ID查询分析结果
     *
     * @param recordId 记录ID
     * @return 分析结果
     */
    @Select("SELECT * FROM video_analysis_result WHERE record_id = #{recordId}")
    VideoAnalysisResult selectByRecordId(@Param("recordId") String recordId);
}
