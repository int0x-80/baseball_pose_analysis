package com.baseball.user.client;

import com.baseball.commons.domain.BaseResponse;
import com.baseball.commons.response.VideoResponse;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

/**
 * 存储服务客户端
 */
@FeignClient(name = "storage-service")
public interface StorageClient {

    @PostMapping(value = "/storage/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    BaseResponse<VideoResponse> uploadFile(
            @RequestPart("file") MultipartFile file,
            @RequestParam(value = "objectName", required = false) String objectName);

    @GetMapping("/storage/download")
    BaseResponse<VideoResponse> getDownloadUrl(@RequestParam("objectName") String objectName);
}