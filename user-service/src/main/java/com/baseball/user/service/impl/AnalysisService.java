package com.baseball.user.service.impl;

import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baseball.commons.constants.VideoAnalysisConstant;
import com.baseball.commons.domain.BaseResponse;
import com.baseball.commons.dto.VideoAnalysisResult;
import com.baseball.commons.dto.VideoMetadata;
import com.baseball.commons.response.VideoMetadataResponse;
import com.baseball.commons.response.VideoResponse;
import com.baseball.user.client.StorageClient;
import com.baseball.user.client.VideoAnalysisClient;
import com.baseball.commons.response.AnalysisResultResponse;
import com.baseball.user.mapper.VideoAnalysisResultMapper;
import com.baseball.user.mapper.VideoMetadataMapper;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.log4j.Log4j2;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import com.baseball.commons.request.VideoRecordQueryRequest;
import com.baseball.commons.response.PageResponse;
import com.baseball.commons.response.VideoRecordResponse;
import com.baseball.user.mapper.VideoMetadataMapper.DailyRecordCount;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * 分析业务服务
 * 流程:
 * 1. 上传视频到 MinIO (storage-service)
 * 2. 通过 Feign 调用 Python 服务进行异步分析 (Nacos 服务发现)
 * 3. Python 分析完成后通过 RabbitMQ 返回结果，存入 Redis 和数据库
 * 4. 前端通过轮询接口从数据库查询结果
 */
@Log4j2
@Service
public class AnalysisService {

    @Autowired
    private VideoAnalysisClient videoAnalysisClient;
    @Autowired
    private StorageClient storageClient;
    @Autowired
    private VideoMetadataMapper videoMetadataMapper;
    @Autowired
    private VideoAnalysisResultMapper videoAnalysisResultMapper;
    /**
     * 上传并异步分析视频
     */
    public VideoMetadataResponse submitAnalysis(MultipartFile video, Long userId, String actionType) {
        // 1. 生成文件命名: videos/{yyyyMMdd}_{userId}_{actionType}.{ext}
        String fileExtension = getFileExtension(video.getOriginalFilename());
        String objectName = generateObjectName(userId, actionType, fileExtension);
        log.info("生成存储路径: {}", objectName);

        // 2. 上传视频到存储（使用自定义命名）
        BaseResponse<VideoResponse> videoResponseBaseResponse = storageClient.uploadFile(video, objectName);
        String downloadUrl = videoResponseBaseResponse.getData().getDownloadUrl();
        log.info("视频已上传到存储: {}", downloadUrl);

        // 3. 生成记录ID
        String recordId = generateRecordId();
        log.info("生成记录ID: {}", recordId);

        // 4. 创建初始分析记录到数据库
        initialViewRecord(recordId, userId, downloadUrl, actionType);

        // 5. 通过 Feign 调用 Python 服务 (Nacos 服务发现)，传递 recordId
        String messageId = callPythonAnalysis(video, userId, actionType, recordId);
        log.info("已调用 Python 分析服务: messageId={}, recordId={}", messageId, recordId);

        // 6. 更新 messageId 到数据库
        updateMessageId(recordId, messageId);

        VideoMetadataResponse  videoMetadataResponse = new VideoMetadataResponse();
        videoMetadataResponse.setUserId(userId);
        videoMetadataResponse.setVideoUrl(downloadUrl);
        videoMetadataResponse.setRecordId(recordId);
        videoMetadataResponse.setStatus(VideoAnalysisConstant.VIDEO_ANALYSIS_STATUS_ANALYSING);

        return videoMetadataResponse;
    }

    /**
     * 创建初始分析记录
     */
    private void initialViewRecord(String recordId, Long userId, String downloadUrl, String actionType) {
        VideoMetadata videoMetadataDTO = new VideoMetadata();
        videoMetadataDTO.setUserId(userId);
        videoMetadataDTO.setRecordId(recordId);
        videoMetadataDTO.setVideoUrl(downloadUrl);
        videoMetadataDTO.setType(actionType);
        videoMetadataDTO.setStatus(VideoAnalysisConstant.VIDEO_ANALYSIS_STATUS_ANALYSING);
        videoMetadataDTO.setCreateTime(LocalDateTime.now());
        videoMetadataDTO.setUpdateTime(LocalDateTime.now());

        videoMetadataMapper.insert(videoMetadataDTO);
    }

    /**
     * 更新 messageId
     */
    private void updateMessageId(String recordId, String messageId) {
        try {
            VideoMetadata record = videoMetadataMapper.selectOne(
                new LambdaQueryWrapper<VideoMetadata>()
                    .eq(VideoMetadata::getRecordId, recordId)
            );
            if (record != null) {
                record.setMessageId(messageId);
                record.setUpdateTime(LocalDateTime.now());
                videoMetadataMapper.updateById(record);
            }
        } catch (Exception e) {
            log.error("更新 messageId 失败: recordId={}", recordId, e);
        }
    }

    /**
     * 查询分析状态（从数据库）
     */
    public VideoMetadataResponse getAnalysisStatus(String recordId) {
        VideoMetadataResponse videoMetadataResponse = new VideoMetadataResponse();
        try {
            VideoMetadata record = videoMetadataMapper.selectOne(
                new LambdaQueryWrapper<VideoMetadata>()
                    .eq(VideoMetadata::getRecordId, recordId)
            );
            videoMetadataResponse.setUserId(record.getUserId());
            videoMetadataResponse.setVideoUrl(record.getVideoUrl());
            videoMetadataResponse.setStatus(record.getStatus());

            return videoMetadataResponse;

        } catch (Exception e) {
            log.error("查询分析状态失败: recordId={}", recordId, e);
        }
        return null;
    }




    /**
     * 获取分析结果（从数据库查询）
     */
    public AnalysisResultResponse getAnalysisResult(String recordId) {
        AnalysisResultResponse response = new AnalysisResultResponse();
        try {
            // 查询视频元数据
            VideoMetadata metadata = videoMetadataMapper.selectByRecordId(recordId);
            if (metadata != null) {
                BeanUtils.copyProperties(metadata, response);
            }

            // 查询分析结果
            QueryWrapper<VideoAnalysisResult> queryWrapper = new QueryWrapper<>();
            queryWrapper.eq("record_id", recordId);
            VideoAnalysisResult analysisResult = videoAnalysisResultMapper.selectOne(queryWrapper);
            if (analysisResult != null) {
                // 复制基础字段
                BeanUtils.copyProperties(analysisResult, response);
                
                // 手动转换高级分析数据（JSON 字符串 -> Map）
                ObjectMapper objectMapper = new ObjectMapper();
                if (analysisResult.getVelocityAnalysis() != null) {
                    response.setVelocityAnalysis(objectMapper.readValue(analysisResult.getVelocityAnalysis(), Map.class));
                }
                if (analysisResult.getJointAnalysis() != null) {
                    response.setJointAnalysis(objectMapper.readValue(analysisResult.getJointAnalysis(), Map.class));
                }
                if (analysisResult.getSymmetryAnalysis() != null) {
                    response.setSymmetryAnalysis(objectMapper.readValue(analysisResult.getSymmetryAnalysis(), Map.class));
                }
                if (analysisResult.getActionPhases() != null) {
                    response.setActionPhases(objectMapper.readValue(analysisResult.getActionPhases(), Map.class));
                }
                if (analysisResult.getTrajectorySmoothness() != null) {
                    response.setTrajectorySmoothness(objectMapper.readValue(analysisResult.getTrajectorySmoothness(), Map.class));
                }
                if (analysisResult.getPowerTransfer() != null) {
                    response.setPowerTransfer(objectMapper.readValue(analysisResult.getPowerTransfer(), Map.class));
                }
            }

            log.info("查询分析结果成功: recordId={}", recordId);
            return response;

        } catch (Exception e) {
            log.error("查询分析结果失败: recordId={}", recordId, e);
        }

        return response;
    }
    /**
     * 调用 Python 分析服务
     * Python 服务接收后立即返回 messageId，后台异步分析，
     * 分析完成后通过 RabbitMQ 返回结果
     */
    private String callPythonAnalysis(MultipartFile video, Long userId, String actionType, String recordId) {
        BaseResponse<VideoMetadata> response = videoAnalysisClient.analyzeVideo(video, userId, actionType, recordId);
        return response.getData().getMessageId();
    }

    /**
     * 生成 MinIO 对象名: videos/{yyyyMMdd}_{userId}_{actionType}.{ext}
     */
    private String generateObjectName(Long userId, String actionType, String fileExtension) {
        String date = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        return String.format("videos/%s_%d_%s.%s", date, userId, actionType, fileExtension);
    }

    /**
     * 提取文件扩展名
     */
    private String getFileExtension(String filename) {
        if (filename == null || !filename.contains(".")) {
            return "mp4";
        }
        return filename.substring(filename.lastIndexOf('.') + 1);
    }

    /**
     * 生成记录ID
     */
    private String generateRecordId() {
        return LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss")) + UUID.randomUUID().toString().substring(0, 10);
    }

    /**
     * 查询用户的视频记录（分页）
     * 
     * @param userId 用户ID
     * @param request 查询请求
     * @return 分页响应
     */
    public PageResponse<VideoRecordResponse> getUserVideoRecords(Long userId, VideoRecordQueryRequest request) {
        try {
            // 计算分页偏移量
            Integer offset = (request.getPageNum() - 1) * request.getPageSize();
            
            // 转换日期范围
            LocalDateTime startDate = null;
            LocalDateTime endDate = null;
            if (request.getStartDate() != null) {
                startDate = request.getStartDate().atStartOfDay();
            }
            if (request.getEndDate() != null) {
                endDate = request.getEndDate().atTime(23, 59, 59);
            }
            
            // 查询记录列表
            List<VideoRecordResponse> records = videoMetadataMapper.selectUserVideoRecords(
                    userId,
                    startDate,
                    endDate,
                    request.getActionType(),
                    request.getStatus(),
                    offset,
                    request.getPageSize(),
                    request.getSortBy(),
                    request.getSortOrder()
            );
            
            // 查询总数
            Long total = videoMetadataMapper.countUserVideoRecords(
                    userId,
                    startDate,
                    endDate,
                    request.getActionType(),
                    request.getStatus()
            );
            
            log.info("查询用户视频记录成功: userId={}, total={}, pageNum={}, pageSize={}", 
                    userId, total, request.getPageNum(), request.getPageSize());
            
            return PageResponse.of(records, total, request.getPageNum(), request.getPageSize());
            
        } catch (Exception e) {
            log.error("查询用户视频记录失败: userId={}", userId, e);
            throw new RuntimeException("查询用户视频记录失败", e);
        }
    }

    /**
     * 查询用户某个月的每日记录数（用于日历展示）
     * 
     * @param userId 用户ID
     * @param year 年份
     * @param month 月份
     * @return 每日记录数 Map，key 为日期（1-31），value 为记录数
     */
    public Map<Integer, Integer> getDailyRecordCount(Long userId, Integer year, Integer month) {
        try {
            List<DailyRecordCount> dailyCounts = videoMetadataMapper.selectDailyRecordCount(userId, year, month);
            
            Map<Integer, Integer> resultMap = new HashMap<>();
            for (DailyRecordCount dailyCount : dailyCounts) {
                resultMap.put(dailyCount.getDay(), dailyCount.getCount());
            }
            
            log.info("查询每日记录数成功: userId={}, year={}, month={}, days={}", 
                    userId, year, month, resultMap.size());
            
            return resultMap;
            
        } catch (Exception e) {
            log.error("查询每日记录数失败: userId={}, year={}, month={}", userId, year, month, e);
            throw new RuntimeException("查询每日记录数失败", e);
        }
    }

    /**
     * 查询用户在某个日期下的所有记录
     *
     * @param userId 用户ID
     * @param date 日期
     * @return 该日期下的所有分析记录列表
     */
    public List<AnalysisResultResponse> getRecordsByDate(Long userId, LocalDate date) {
        List<AnalysisResultResponse> resultList = new ArrayList<>();
        
        try {
            
            // 计算当天的开始时间和结束时间
            LocalDateTime startOfDay = date.atStartOfDay();
            LocalDateTime endOfDay = date.atTime(23, 59, 59);
            
            log.info("查询用户日期记录: userId={}, date={}, startOfDay={}, endOfDay={}", 
                    userId, date, startOfDay, endOfDay);
            
            // 查询该用户在该日期范围内的所有视频元数据
            LambdaQueryWrapper<VideoMetadata> queryWrapper = new LambdaQueryWrapper<>();
            queryWrapper.eq(VideoMetadata::getUserId, userId)
                       .ge(VideoMetadata::getCreateTime, startOfDay)
                       .le(VideoMetadata::getCreateTime, endOfDay)
                       .orderByDesc(VideoMetadata::getCreateTime);
            
            List<VideoMetadata> metadataList = videoMetadataMapper.selectList(queryWrapper);
            
            log.info("查询到 {} 条视频元数据记录", metadataList.size());
            
            // 对于每个视频元数据，查询对应的分析结果
            for (VideoMetadata metadata : metadataList) {
                AnalysisResultResponse response = getAnalysisResult(metadata.getRecordId());
                if (response != null) {
                    resultList.add(response);
                }
            }
            
            log.info("成功返回 {} 条分析记录", resultList.size());
            
        } catch (NumberFormatException e) {
            log.error("用户ID格式错误: userId={}", userId, e);
            throw new RuntimeException("用户ID格式错误", e);
        } catch (Exception e) {
            log.error("查询用户日期记录失败: userId={}, date={}", userId, date, e);
            throw new RuntimeException("查询用户日期记录失败", e);
        }
        
        return resultList;
    }
}
