package com.baseball.user.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baseball.commons.dto.UserLoginLogDTO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 用户登录记录表 Mapper
 */
@Mapper
public interface UserLoginLogMapper extends BaseMapper<UserLoginLogDTO> {
}
