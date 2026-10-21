package com.baseball.user.controller;

import com.baseball.commons.domain.BaseResponse;
import com.baseball.commons.request.VideoRecordQueryRequest;
import com.baseball.commons.response.PageResponse;
import com.baseball.commons.response.VideoMetadataResponse;
import com.baseball.commons.response.VideoRecordResponse;
import com.baseball.commons.response.VideoResponse;
import com.baseball.commons.util.UserContext;
import com.baseball.user.client.StorageClient;
import com.baseball.commons.response.AnalysisResultResponse;
import com.baseball.user.service.impl.AnalysisService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import javax.validation.Valid;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

/**
 * 视频分析Controller（RabbitMQ 异步版）
 */
@Slf4j
@RestController
@RequestMapping("/api/video")
@Api(tags = "视频分析")
public class VideoAnalysisController {

    @Autowired
    private AnalysisService analysisService;

    @Autowired
    private StorageClient storageClient;

    @PostMapping("/analyze")
    @ApiOperation("上传并异步分析视频")
    public BaseResponse<VideoMetadataResponse> analyzeVideo(
            @RequestParam("video") MultipartFile video,
            @RequestParam(value = "userId", defaultValue = "1") Long userId,
            @RequestParam(value = "actionType", defaultValue = "batting") String actionType
    ) {
        log.info("收到视频分析请求: userId={}, actionType={}, file={}", userId, actionType, video.getOriginalFilename());

        VideoMetadataResponse videoMetadataDTO = analysisService.submitAnalysis(video, userId, actionType);
        return BaseResponse.success(videoMetadataDTO);
    }

    @GetMapping("/status/{recordId}")
    @ApiOperation("查询分析状态")
    public BaseResponse<VideoMetadataResponse> getStatus(@PathVariable String recordId) {
        log.info("查询分析状态: recordId={}", recordId);

        VideoMetadataResponse result = analysisService.getAnalysisStatus(recordId);
        if (result == null) {
            return BaseResponse.fail("recordId " +  recordId + " not exist");
        }

        return BaseResponse.success(result);
    }

    @GetMapping("/result/{recordId}")
    @ApiOperation("获取分析结果（从 Redis 查询）")
    public BaseResponse<AnalysisResultResponse> getResult(@PathVariable String recordId) {
        log.info("获取分析结果: recordId={}", recordId);

        AnalysisResultResponse record = analysisService.getAnalysisResult(recordId);
        if (record == null) {
            return BaseResponse.fail("Record not found:" + recordId);
        }
        return BaseResponse.success(record);
    }

    @GetMapping("/download")
    @ApiOperation("下载视频文件（通过文件名）")
    public BaseResponse<VideoResponse> downloadVideo(@RequestParam("fileName") String fileName) {
        log.info("下载视频: fileName={}", fileName);
        return  storageClient.getDownloadUrl(fileName);
    }

    @PostMapping("/records")
    @ApiOperation("查询用户的视频记录（分页）")
    public BaseResponse<PageResponse<VideoRecordResponse>> getUserVideoRecords(
            @Valid @RequestBody VideoRecordQueryRequest request
    ) {
        Long userId = UserContext.getCurrentUserId();
        log.info("查询用户视频记录: userId={}, pageNum={}, pageSize={}", 
                userId, request.getPageNum(), request.getPageSize());

        PageResponse<VideoRecordResponse> response = analysisService.getUserVideoRecords(userId, request);
        return BaseResponse.success(response);
    }

    @GetMapping("/records/daily-count")
    @ApiOperation("查询用户某月的每日记录数（用于日历展示）")
    public BaseResponse<Map<Integer, Integer>> getDailyRecordCount(
            @RequestParam("year") Integer year,
            @RequestParam("month") Integer month
    ) {
        Long userId = UserContext.getCurrentUserId();
        log.info("查询每日记录数: userId={}, year={}, month={}", userId, year, month);

        Map<Integer, Integer> result = analysisService.getDailyRecordCount(userId, year, month);
        return BaseResponse.success(result);
    }

    @GetMapping("/records/daily-records")
    @ApiOperation("查询用户某天的所有记录")
    public BaseResponse<List<AnalysisResultResponse>> getDailyRecordByDate(
            @RequestParam("date") @DateTimeFormat(pattern = "yyyy-MM-dd") LocalDate date
            ) {
        Long userId = UserContext.getCurrentUserId();
        log.info("查询每日记录数: userId={}, date={}", userId, date);

        List<AnalysisResultResponse> result = analysisService.getRecordsByDate(userId, date);
        return BaseResponse.success(result);
    }
}