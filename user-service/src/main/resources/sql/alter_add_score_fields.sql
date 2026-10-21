-- 为 video_analysis_result 表添加评分和等级字段
ALTER TABLE video_analysis_result
ADD COLUMN overall_score DECIMAL(5,2) DEFAULT NULL COMMENT '总评分(0-100)' AFTER action_type,
ADD COLUMN grade VARCHAR(10) DEFAULT NULL COMMENT '等级(A/B/C/D/E)' AFTER overall_score;

-- 为 video_metadata 表添加复合索引以优化查询性能
ALTER TABLE video_metadata
ADD INDEX idx_user_create_time (user_id, create_time);
