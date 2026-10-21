package com.baseball.user.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baseball.commons.dto.UserVipLogDTO;
import org.apache.ibatis.annotations.Mapper;

/**
 * 用户VIP记录表 Mapper
 */
@Mapper
public interface UserVipLogMapper extends BaseMapper<UserVipLogDTO> {
}
