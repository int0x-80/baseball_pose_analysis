package com.baseball.user.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.baseball.commons.dto.UserDTO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

/**
 * 用户表 Mapper
 */
@Mapper
public interface UserMapper extends BaseMapper<UserDTO> {
    
    /**
     * 根据手机号查询用户
     */
    @Select("SELECT * FROM user WHERE phone = #{phone} AND status = 1")
    UserDTO selectByPhone(@Param("phone") String phone);
    
    /**
     * 根据微信OpenID查询用户
     */
    @Select("SELECT * FROM user WHERE open_id_wechat = #{openIdWechat} AND status = 1")
    UserDTO selectByOpenIdWechat(@Param("openIdWechat") String openIdWechat);
    
    /**
     * 根据UnionID查询用户
     */
    @Select("SELECT * FROM user WHERE union_id = #{unionId} AND status = 1")
    UserDTO selectByUnionId(@Param("unionId") String unionId);
    
    /**
     * 增加分析次数
     */
    void incrementAnalysisCount(@Param("userId") Long userId);
}
