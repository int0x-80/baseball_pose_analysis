package com.baseball.user.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baseball.commons.dto.UserPointsLogDTO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 用户积分记录表 Mapper
 */
@Mapper
public interface UserPointsLogMapper extends BaseMapper<UserPointsLogDTO> {
}
