package com.baseball.commons.domain;
/*
 *  @Author: wangyinuo
 *  @Date:   2024/6/19
 */
public enum ResultCode {

    /**操作成功**/
    SUCCESS("200","success"),

    /**操作失败**/
    ERROR("-1","error"),;

    /**
     * 自定义状态码
     **/
    private String code;


    /**自定义描述**/
    private String message;

    ResultCode(String code, String message) {
        this.code = code;
        this.message = message;
    }

    public String getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }
}
