-- 先删除旧表（如有）
DROP TABLE IF EXISTS `analysis_record`;

-- 创建分析记录表
CREATE TABLE `analysis_record` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `record_id` VARCHAR(64) NOT NULL COMMENT '记录ID',
  `message_id` VARCHAR(64) DEFAULT NULL COMMENT '消息ID',
  `user_id` BIGINT DEFAULT NULL COMMENT '用户ID',
  `action_type` VARCHAR(32) DEFAULT NULL COMMENT '动作类型: batting/pitching',
  `video_url` VARCHAR(512) DEFAULT NULL COMMENT '原始视频URL',
  `skeleton_video_name` VARCHAR(255) DEFAULT NULL COMMENT '骨骼视频文件名',
  `analysis_json_name` VARCHAR(255) DEFAULT NULL COMMENT 'JSON分析结果文件名',
  `status` VARCHAR(32) NOT NULL DEFAULT 'ANALYZING' COMMENT '状态: ANALYZING/COMPLETED/FAILED',
  
  -- 原始数据（Python 服务输出的完整 JSON）
  `raw_data` JSON DEFAULT NULL COMMENT '原始分析数据JSON',
  
  -- 视频元数据
  `fps` INT DEFAULT NULL COMMENT '帧率',
  `video_width` INT DEFAULT NULL COMMENT '视频宽度',
  `video_height` INT DEFAULT NULL COMMENT '视频高度',
  `total_frames` INT DEFAULT NULL COMMENT '总帧数',
  
  -- 手臂速度
  `left_speed_ms` DECIMAL(8,2) DEFAULT NULL COMMENT '左手速度(m/s)',
  `right_speed_ms` DECIMAL(8,2) DEFAULT NULL COMMENT '右手速度(m/s)',
  `left_speed_km_h` DECIMAL(8,2) DEFAULT NULL COMMENT '左手速度(km/h)',
  `right_speed_km_h` DECIMAL(8,2) DEFAULT NULL COMMENT '右手速度(km/h)',
  
  -- 挥棒速度
  `max_bat_speed_ms` DECIMAL(8,2) DEFAULT NULL COMMENT '最大挥棒速度(m/s)',
  `max_bat_speed_km_h` DECIMAL(8,2) DEFAULT NULL COMMENT '最大挥棒速度(km/h)',
  `avg_bat_speed_ms` DECIMAL(8,2) DEFAULT NULL COMMENT '平均挥棒速度(m/s)',
  `avg_bat_speed_km_h` DECIMAL(8,2) DEFAULT NULL COMMENT '平均挥棒速度(km/h)',
  
  -- 挥棒轨迹
  `trajectory_points` INT DEFAULT NULL COMMENT '轨迹点数',
  `path_length` DECIMAL(10,2) DEFAULT NULL COMMENT '轨迹总长度',
  `direct_distance` DECIMAL(10,2) DEFAULT NULL COMMENT '直线距离',
  `path_ratio` DECIMAL(5,2) DEFAULT NULL COMMENT '路径比例',
  `swing_angle_deg` DECIMAL(8,2) DEFAULT NULL COMMENT '挥棒角度(度)',
  `trajectory_type` VARCHAR(32) DEFAULT NULL COMMENT '轨迹类型: arc/slight_curve/straight',
  `trajectory_data` JSON DEFAULT NULL COMMENT '轨迹点数据JSON',
  
  -- 腿部分析
  `max_hip_rotation_mm` DECIMAL(8,2) DEFAULT NULL COMMENT '最大转胯幅度(mm)',
  `avg_hip_rotation_mm` DECIMAL(8,2) DEFAULT NULL COMMENT '平均转胯幅度(mm)',
  `hip_stability` DECIMAL(5,2) DEFAULT NULL COMMENT '髋部稳定性',
  
  -- 躯干分析
  `max_twist_angle_deg` DECIMAL(8,2) DEFAULT NULL COMMENT '最大扭转角度(度)',
  `avg_twist_angle_deg` DECIMAL(8,2) DEFAULT NULL COMMENT '平均扭转角度(度)',
  `shoulder_hip_diff_deg` DECIMAL(8,2) DEFAULT NULL COMMENT '肩髋角度差(度)',
  
  -- 评估结果（Java 评估服务生成）
  `overall_score` DECIMAL(5,2) DEFAULT NULL COMMENT '总评分(0-100)',
  `grade` VARCHAR(8) DEFAULT NULL COMMENT '等级: A/B/C/D/E',
  `scores` JSON DEFAULT NULL COMMENT '各项得分JSON',
  `issues` JSON DEFAULT NULL COMMENT '问题列表JSON',
  `summary` TEXT DEFAULT NULL COMMENT '建议总结',
  
  -- 错误信息
  `error_message` VARCHAR(1024) DEFAULT NULL COMMENT '错误信息',
  `error_code` VARCHAR(64) DEFAULT NULL COMMENT '错误码',
  
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_record_id` (`record_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视频分析记录表';
