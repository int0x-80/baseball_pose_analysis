-- 视频元数据表
CREATE TABLE IF NOT EXISTS `video_metadata` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` BIGINT DEFAULT NULL COMMENT '用户ID',
  `record_id` VARCHAR(64) NOT NULL COMMENT '记录ID',
  `message_id` VARCHAR(64) DEFAULT NULL COMMENT '消息ID',
  `video_url` VARCHAR(512) DEFAULT NULL COMMENT '原始视频URL',
  `skeleton_video_url` VARCHAR(512) DEFAULT NULL COMMENT '骨架视频URL',
  `status` INT DEFAULT 0 COMMENT '视频分析状态: 0-分析中, 1-完成, 2-失败',
  `skeleton_video_name` VARCHAR(255) DEFAULT NULL COMMENT '骨骼视频文件名',
  `analysis_json_name` VARCHAR(255) DEFAULT NULL COMMENT 'JSON分析结果文件名',
  `fps` INT DEFAULT NULL COMMENT '帧率',
  `video_width` INT DEFAULT NULL COMMENT '视频宽度',
  `video_height` INT DEFAULT NULL COMMENT '视频高度',
  `total_frames` INT DEFAULT NULL COMMENT '总帧数',
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_record_id` (`record_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_status` (`status`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视频元数据表';

-- 视频分析结果表
CREATE TABLE IF NOT EXISTS `video_analysis_result` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `record_id` VARCHAR(64) NOT NULL COMMENT '记录ID',
  `user_id` BIGINT DEFAULT NULL COMMENT '用户ID',
  `action_type` VARCHAR(32) DEFAULT NULL COMMENT '动作类型: batting/pitching',
  
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
  
  -- 腿部分析
  `max_hip_rotation_mm` DECIMAL(8,2) DEFAULT NULL COMMENT '最大转胯幅度(mm)',
  `avg_hip_rotation_mm` DECIMAL(8,2) DEFAULT NULL COMMENT '平均转胯幅度(mm)',
  `hip_stability` DECIMAL(5,2) DEFAULT NULL COMMENT '髋部稳定性',
  
  -- 躯干分析
  `max_twist_angle_deg` DECIMAL(8,2) DEFAULT NULL COMMENT '最大扭转角度(度)',
  `avg_twist_angle_deg` DECIMAL(8,2) DEFAULT NULL COMMENT '平均扭转角度(度)',
  `shoulder_hip_diff_deg` DECIMAL(8,2) DEFAULT NULL COMMENT '肩髋角度差(度)',

  -- 高级分析数据（JSON 存储）
  `velocity_analysis` JSON DEFAULT NULL COMMENT '速度曲线分析',
  `joint_analysis` JSON DEFAULT NULL COMMENT '关节角度分析',
  `symmetry_analysis` JSON DEFAULT NULL COMMENT '身体对称性分析',
  `action_phases` JSON DEFAULT NULL COMMENT '动作阶段检测',
  `trajectory_smoothness` JSON DEFAULT NULL COMMENT '轨迹平滑度分析',
  `power_transfer` JSON DEFAULT NULL COMMENT '能量传递效率分析',

  -- 原始数据（使用 MEDIUMTEXT，分析数据通常超过 64KB TEXT 上限）
  `raw_data` MEDIUMTEXT DEFAULT NULL COMMENT '原始数据JSON',
  
  `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_record_id` (`record_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='视频分析结果表';
