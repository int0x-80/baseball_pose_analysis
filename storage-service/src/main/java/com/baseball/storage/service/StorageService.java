package com.baseball.storage.service;

import io.minio.*;
import io.minio.http.Method;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.InputStream;
import java.util.concurrent.TimeUnit;

/**
 * 文件存储服务
 */
@Slf4j
@Service
public class StorageService {

    @Autowired
    private MinioClient minioClient;

    @Value("${minio.bucket}")
    private String bucket;

    /**
     * 上传文件
     */
    public String uploadFile(String objectName, InputStream stream, long size, String contentType) {
        try {
            // 确保bucket存在
            boolean exists = minioClient.bucketExists(BucketExistsArgs.builder().bucket(bucket).build());
            if (!exists) {
                minioClient.makeBucket(MakeBucketArgs.builder().bucket(bucket).build());
                log.info("创建bucket: {}", bucket);
            }

            // 上传文件
            minioClient.putObject(
                    PutObjectArgs.builder()
                            .bucket(bucket)
                            .object(objectName)
                            .stream(stream, size, -1)
                            .contentType(contentType)
                            .build()
            );

            log.info("文件上传成功: {}", objectName);
            return objectName;

        } catch (Exception e) {
            log.error("文件上传失败: {}", objectName, e);
            throw new RuntimeException("文件上传失败", e);
        }
    }

    /**
     * 上传视频（使用原始文件名，兼容旧接口）
     */
    public String uploadVideo(MultipartFile file) {
        try (InputStream stream = file.getInputStream()) {
            return uploadFile("videos/" + file.getOriginalFilename(), stream, file.getSize(), "video/mp4");
        } catch (Exception e) {
            log.error("视频上传失败", e);
            throw new RuntimeException("视频上传失败", e);
        }
    }

    /**
     * 使用自定义对象名上传文件
     *
     * @param objectName  MinIO 中的对象路径，如 videos/20260710_1_batting.mp4
     * @param file        上传文件
     * @param contentType 文件 MIME 类型
     * @return MinIO 对象名
     */
    public String uploadWithObjectName(String objectName, MultipartFile file, String contentType) {
        try (InputStream stream = file.getInputStream()) {
            return uploadFile(objectName, stream, file.getSize(), contentType);
        } catch (Exception e) {
            log.error("文件上传失败: objectName={}", objectName, e);
            throw new RuntimeException("文件上传失败", e);
        }
    }

    /**
     * 获取文件下载URL
     */
    public String getDownloadUrl(String objectName, int expireMinutes) {
        try {
            return minioClient.getPresignedObjectUrl(
                    GetPresignedObjectUrlArgs.builder()
                            .method(Method.GET)
                            .bucket(bucket)
                            .object(objectName)
                            .expiry(expireMinutes, TimeUnit.MINUTES)
                            .build()
            );
        } catch (Exception e) {
            log.error("获取下载URL失败: {}", objectName, e);
            throw new RuntimeException("获取下载URL失败", e);
        }
    }

    /**
     * 删除文件
     */
    public void deleteFile(String objectName) {
        try {
            minioClient.removeObject(
                    RemoveObjectArgs.builder()
                            .bucket(bucket)
                            .object(objectName)
                            .build()
            );
            log.info("文件删除成功: {}", objectName);
        } catch (Exception e) {
            log.error("文件删除失败: {}", objectName, e);
            throw new RuntimeException("文件删除失败", e);
        }
    }
}