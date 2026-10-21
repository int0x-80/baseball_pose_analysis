package com.baseball.commons.response;

import lombok.Data;

import java.util.List;

/**
 * 分页响应包装类
 */
@Data
public class PageResponse<T> {
    
    /**
     * 数据列表
     */
    private List<T> records;
    
    /**
     * 总记录数
     */
    private Long total;
    
    /**
     * 当前页码
     */
    private Integer pageNum;
    
    /**
     * 每页大小
     */
    private Integer pageSize;
    
    /**
     * 总页数
     */
    private Integer totalPages;
    
    /**
     * 是否有下一页
     */
    private Boolean hasNext;
    
    /**
     * 是否有上一页
     */
    private Boolean hasPrevious;
    
    public static <T> PageResponse<T> of(List<T> records, Long total, Integer pageNum, Integer pageSize) {
        PageResponse<T> response = new PageResponse<>();
        response.setRecords(records);
        response.setTotal(total);
        response.setPageNum(pageNum);
        response.setPageSize(pageSize);
        
        int totalPages = (int) Math.ceil((double) total / pageSize);
        response.setTotalPages(totalPages);
        response.setHasNext(pageNum < totalPages);
        response.setHasPrevious(pageNum > 1);
        
        return response;
    }
}
