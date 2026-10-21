package com.baseball.commons.domain;
/*
 *  @Author: wangyinuo
 *  @Date:   2024/6/19
 */

import java.io.Serializable;

import static com.baseball.commons.domain.ResultCode.ERROR;
import static com.baseball.commons.domain.ResultCode.SUCCESS;

public class BaseResponse<T> implements Serializable {

    private static final long serialVersionUID = 1901152752394073986L;
    /**
     * 响应状态码
     */
    private String code;
    /**
     * 响应结果描述
     */
    private String message;
    /**
     * 返回的数据
     */
    private T data;
    /**
     * 成功返回
     */
    public static <T> BaseResponse<T> success(T data) {
        BaseResponse<T> response = new BaseResponse<>();
        response.setCode(SUCCESS.getCode());
        response.setMessage(SUCCESS.getMessage());
        response.setData(data);
        return response;
    }

    /**
     * 失败返回
     */
    public static <T> BaseResponse<T> fail(String message) {
        BaseResponse<T> response = new BaseResponse<>();
        response.setCode(ERROR.getCode());
        response.setMessage(message);
        return response;
    }

    /**
     * 失败返回
     */
    public static <T> BaseResponse<T> fail(String code, String msg, T data) {

        BaseResponse<T> response = new BaseResponse<>();
        response.setCode(code);
        response.setMessage(msg);
        response.setData(data);
        return response;
    }

    public String getCode() {
        return code;
    }

    public void setCode(String code) {
        this.code = code;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public T getData() {
        return data;
    }

    public void setData(T data) {
        this.data = data;
    }
}
