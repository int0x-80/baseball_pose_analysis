-- 为 video_analysis_result 表添加高级分析字段
ALTER TABLE video_analysis_result
ADD COLUMN velocity_analysis JSON DEFAULT NULL COMMENT '速度曲线分析' AFTER shoulder_hip_diff_deg,
ADD COLUMN joint_analysis JSON DEFAULT NULL COMMENT '关节角度分析' AFTER velocity_analysis,
ADD COLUMN symmetry_analysis JSON DEFAULT NULL COMMENT '身体对称性分析' AFTER joint_analysis,
ADD COLUMN action_phases JSON DEFAULT NULL COMMENT '动作阶段检测' AFTER symmetry_analysis,
ADD COLUMN trajectory_smoothness JSON DEFAULT NULL COMMENT '轨迹平滑度分析' AFTER action_phases,
ADD COLUMN power_transfer JSON DEFAULT NULL COMMENT '能量传递效率分析' AFTER trajectory_smoothness;
