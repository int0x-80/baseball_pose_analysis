package com.baseball.storage.controller;

import com.baseball.commons.domain.BaseResponse;
import com.baseball.commons.response.VideoResponse;
import com.baseball.storage.service.StorageService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;


/**
 * 存储服务Controller
 */
@Slf4j
@RestController
@RequestMapping("/storage")
@Api(tags = "存储服务")
public class StorageController {

    @Autowired
    private StorageService storageService;

    @PostMapping("/upload")
    @ApiOperation("上传文件")
    public BaseResponse<VideoResponse> uploadFile(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "type", defaultValue = "video") String type,
            @RequestParam(value = "objectName", required = false) String objectName) {

        String resultObjectName;
        String contentType;

        if ("json".equals(type)) {
            // JSON 分析文件
            contentType = "application/json";
            if (objectName != null && !objectName.isEmpty()) {
                resultObjectName = storageService.uploadWithObjectName(objectName, file, contentType);
            } else {
                resultObjectName = storageService.uploadVideo(file);
            }
        } else if ("video".equals(type)) {
            // 视频文件
            contentType = "video/mp4";
            if (objectName != null && !objectName.isEmpty()) {
                resultObjectName = storageService.uploadWithObjectName(objectName, file, contentType);
            } else {
                resultObjectName = storageService.uploadVideo(file);
            }
        } else if ("image".equals(type)) {
            // 图片文件（关键帧截图等）
            contentType = "image/png";
            if (objectName != null && !objectName.isEmpty()) {
                resultObjectName = storageService.uploadWithObjectName(objectName, file, contentType);
            } else {
                // 没有指定 objectName 时，按日期生成图片路径
                String ext = getFileExtension(file.getOriginalFilename());
                String defaultName = "images/" + System.currentTimeMillis() + "." + ext;
                resultObjectName = storageService.uploadWithObjectName(defaultName, file, contentType);
            }
        } else {
            return BaseResponse.fail("无效文件格式");
        }

        VideoResponse response = new VideoResponse();
        response.setObjectName(resultObjectName);
        response.setFileName(file.getOriginalFilename());
        response.setDownloadUrl(storageService.getDownloadUrl(resultObjectName, 60));
        response.setFileSize(file.getSize());

        return BaseResponse.success(response);
    }

    @GetMapping("/download")
    @ApiOperation("获取下载链接")
    public BaseResponse<VideoResponse> getDownloadUrl(
            @RequestParam("objectName") String objectName,
            @RequestParam(value = "expire", defaultValue = "60") int expireMinutes
    ) {
        String url = storageService.getDownloadUrl(objectName, expireMinutes);
        VideoResponse  response = new VideoResponse();
        if (url == null) {
            response.setDownloadUrl("");
            return BaseResponse.fail("-1", "Video not found", response);
        }

        response.setObjectName(objectName);
        response.setDownloadUrl(url);
        response.setExpireMinutes(String.valueOf(expireMinutes));
        return BaseResponse.success(response);
    }

    @DeleteMapping("/{objectName}")
    @ApiOperation("删除文件")
    public BaseResponse<VideoResponse> deleteFile(@PathVariable String objectName) {
        storageService.deleteFile(objectName);
        VideoResponse  response = new VideoResponse();
        response.setObjectName(objectName);
        return BaseResponse.success(response);
    }

    private String getFileExtension(String filename) {
        if (filename == null || !filename.contains(".")) {
            return "png";
        }
        return filename.substring(filename.lastIndexOf('.') + 1);
    }
}