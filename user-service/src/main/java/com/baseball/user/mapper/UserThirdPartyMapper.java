package com.baseball.user.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baseball.commons.dto.UserThirdPartyDTO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

/**
 * 第三方账号绑定表 Mapper
 */
@Mapper
public interface UserThirdPartyMapper extends BaseMapper<UserThirdPartyDTO> {
    
    /**
     * 根据平台和第三方ID查询
     */
    @Select("SELECT * FROM user_third_party WHERE platform = #{platform} AND third_party_id = #{thirdPartyId}")
    UserThirdPartyDTO selectByPlatformAndId(@Param("platform") String platform, @Param("thirdPartyId") String thirdPartyId);
}
