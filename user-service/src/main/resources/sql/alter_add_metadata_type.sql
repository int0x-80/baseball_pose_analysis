-- video_metadata 表新增 type 字段（动作类型）
-- 上传时即写入，不依赖分析结果
ALTER TABLE video_metadata ADD COLUMN type VARCHAR(20) DEFAULT NULL COMMENT '动作类型: batting-击球, pitching-投球' AFTER status;

-- 回填已有数据：从 video_analysis_result 复制 action_type
UPDATE video_metadata vm
INNER JOIN video_analysis_result var ON vm.record_id = var.record_id
SET vm.type = var.action_type
WHERE vm.type IS NULL;
