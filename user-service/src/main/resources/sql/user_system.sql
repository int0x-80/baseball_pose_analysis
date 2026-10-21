-- 用户系统数据库表结构
-- 支持多平台：微信小程序、独立APP等

-- 1. 用户主表
CREATE TABLE IF NOT EXISTS `user` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  
  -- 核心身份
  `union_id` VARCHAR(64) DEFAULT NULL COMMENT '跨平台统一标识',
  `open_id_wechat` VARCHAR(64) DEFAULT NULL COMMENT '微信小程序OpenID',
  `open_id_app` VARCHAR(64) DEFAULT NULL COMMENT 'APP OpenID',
  `phone` VARCHAR(255) DEFAULT NULL COMMENT '手机号（加密）',
  `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
  `password_hash` VARCHAR(255) DEFAULT NULL COMMENT '密码哈希',
  
  -- 基础信息
  `nickname` VARCHAR(50) DEFAULT NULL COMMENT '昵称',
  `avatar_url` VARCHAR(500) DEFAULT NULL COMMENT '头像URL',
  `gender` TINYINT DEFAULT 0 COMMENT '性别：0-未知,1-男,2-女',
  `birthday` DATE DEFAULT NULL COMMENT '生日',
  `country` VARCHAR(50) DEFAULT NULL COMMENT '国家',
  `province` VARCHAR(50) DEFAULT NULL COMMENT '省份',
  `city` VARCHAR(50) DEFAULT NULL COMMENT '城市',
  `language` VARCHAR(20) DEFAULT 'zh-CN' COMMENT '语言偏好',
  
  -- 平台特定
  `wechat_session_key` VARCHAR(100) DEFAULT NULL COMMENT '微信会话密钥',
  `wechat_union_id` VARCHAR(64) DEFAULT NULL COMMENT '微信UnionID',
  `apple_id` VARCHAR(100) DEFAULT NULL COMMENT 'Apple ID',
  `google_id` VARCHAR(100) DEFAULT NULL COMMENT 'Google ID',
  `last_login_platform` VARCHAR(20) DEFAULT NULL COMMENT '最后登录平台',
  `device_info` JSON DEFAULT NULL COMMENT '设备信息',
  
  -- 状态与统计
  `status` TINYINT DEFAULT 1 COMMENT '账号状态：0-禁用,1-正常',
  `is_verified` TINYINT DEFAULT 0 COMMENT '是否实名认证',
  `vip_level` INT DEFAULT 0 COMMENT 'VIP等级',
  `vip_expire_time` DATETIME DEFAULT NULL COMMENT 'VIP到期时间',
  `points` INT DEFAULT 0 COMMENT '积分',
  `total_analysis_count` INT DEFAULT 0 COMMENT '总分析次数',
  `last_login_time` DATETIME DEFAULT NULL COMMENT '最后登录时间',
  `register_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
  
  -- 扩展字段
  `preferences` JSON DEFAULT NULL COMMENT '用户偏好设置',
  `tags` JSON DEFAULT NULL COMMENT '用户标签',
  `extra_data` JSON DEFAULT NULL COMMENT '扩展数据',
  
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_union_id` (`union_id`),
  UNIQUE KEY `uk_phone` (`phone`),
  UNIQUE KEY `uk_email` (`email`),
  UNIQUE KEY `uk_open_id_wechat` (`open_id_wechat`),
  KEY `idx_status` (`status`),
  KEY `idx_vip_level` (`vip_level`),
  KEY `idx_register_time` (`register_time`),
  KEY `idx_last_login_time` (`last_login_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 2. 用户登录记录表
CREATE TABLE IF NOT EXISTS `user_login_log` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `platform` VARCHAR(20) NOT NULL COMMENT '登录平台：wechat,app,web',
  `login_type` VARCHAR(20) NOT NULL COMMENT '登录方式：wechat,phone,email,apple,google',
  `ip_address` VARCHAR(50) DEFAULT NULL COMMENT 'IP地址',
  `user_agent` VARCHAR(500) DEFAULT NULL COMMENT 'User-Agent',
  `device_info` JSON DEFAULT NULL COMMENT '设备信息',
  `login_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
  
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_login_time` (`login_time`),
  KEY `idx_platform` (`platform`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户登录记录表';

-- 3. 第三方账号绑定表
CREATE TABLE IF NOT EXISTS `user_third_party` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `platform` VARCHAR(20) NOT NULL COMMENT '平台：wechat,apple,google',
  `third_party_id` VARCHAR(100) NOT NULL COMMENT '第三方ID',
  `union_id` VARCHAR(64) DEFAULT NULL COMMENT '第三方UnionID',
  `access_token` VARCHAR(500) DEFAULT NULL COMMENT '访问令牌',
  `refresh_token` VARCHAR(500) DEFAULT NULL COMMENT '刷新令牌',
  `token_expire_time` DATETIME DEFAULT NULL COMMENT '令牌过期时间',
  `bind_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
  `unbind_time` DATETIME DEFAULT NULL COMMENT '解绑时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_platform_third_party` (`platform`, `third_party_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_union_id` (`union_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='第三方账号绑定表';

-- 4. 用户积分记录表
CREATE TABLE IF NOT EXISTS `user_points_log` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `points` INT NOT NULL COMMENT '积分变动（正数增加，负数减少）',
  `type` VARCHAR(20) NOT NULL COMMENT '类型：earn-获得,spend-消费,expire-过期',
  `reason` VARCHAR(100) DEFAULT NULL COMMENT '原因',
  `reference_id` VARCHAR(64) DEFAULT NULL COMMENT '关联记录ID',
  `balance_before` INT DEFAULT 0 COMMENT '变动前余额',
  `balance_after` INT DEFAULT 0 COMMENT '变动后余额',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_create_time` (`create_time`),
  KEY `idx_type` (`type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户积分记录表';

-- 5. 用户VIP记录表
CREATE TABLE IF NOT EXISTS `user_vip_log` (
  `id` BIGINT NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT NOT NULL COMMENT '用户ID',
  `vip_level` INT NOT NULL COMMENT 'VIP等级',
  `action` VARCHAR(20) NOT NULL COMMENT '操作：upgrade-升级,renew-续费,expire-过期',
  `duration_days` INT DEFAULT NULL COMMENT '时长（天）',
  `price` DECIMAL(10,2) DEFAULT NULL COMMENT '价格',
  `order_id` VARCHAR(64) DEFAULT NULL COMMENT '订单ID',
  `expire_time` DATETIME DEFAULT NULL COMMENT '到期时间',
  `create_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_create_time` (`create_time`),
  KEY `idx_action` (`action`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户VIP记录表';
