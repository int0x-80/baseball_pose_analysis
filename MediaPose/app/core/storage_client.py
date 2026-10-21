"""
Storage Service 客户端
通过 Nacos 服务发现调用 storage-service 上传文件到 MinIO
服务名从 settings 读取，无硬编码
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any

import requests

from app.core.config import settings
from app.api.nacos_client import nacos_registry

logger = logging.getLogger(__name__)


class StorageClient:
    """Storage Service 客户端"""

    def __init__(self):
        self._cached_url: Optional[str] = None

    def _get_service_url(self) -> str:
        """
        获取 storage-service 地址

        优先从 Nacos 获取，失败则使用配置的默认地址
        """
        # 尝试从 Nacos 获取服务地址
        service_url = nacos_registry.get_service_instance(settings.NACOS_STORAGE_SERVICE_NAME)

        if service_url:
            self._cached_url = service_url
            return service_url

        # Nacos 不可用，使用配置的默认地址
        fallback_url = settings.STORAGE_SERVICE_URL
        if fallback_url:
            logger.warning(f"使用配置的 storage-service 地址: {fallback_url}")
            return fallback_url

        logger.error("无法获取 storage-service 地址")
        return ""

    def upload_video(self, file_path: Path, object_name: str = None) -> Optional[Dict[str, Any]]:
        """
        上传视频文件到 storage-service

        Args:
            file_path: 视频文件路径
            object_name: MinIO 中的自定义对象路径

        Returns:
            成功返回 {"objectName": "...", "fileName": "...", "downloadUrl": "...", "fileSize": ...}
            失败返回 None
        """
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return None

        base_url = self._get_service_url()
        if not base_url:
            logger.error("无法获取 storage-service 地址")
            return None

        url = f"{base_url}/storage/upload"

        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "video/mp4")}
                data = {"type": "video"}
                if object_name:
                    data["objectName"] = object_name
                response = requests.post(url, files=files, data=data, timeout=300)

            if response.status_code == 200:
                result = response.json()
                if str(result.get("code")) == "200":
                    logger.info(f"视频上传成功: {file_path.name} -> {result['data']['objectName']}")
                    return result["data"]
                else:
                    logger.error(f"视频上传失败: {result.get('message')}")
                    return None
            else:
                logger.error(f"视频上传请求失败: HTTP {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"视频上传异常: {e}")
            return None

    def upload_json(self, file_path: Path, object_name: str = None) -> Optional[Dict[str, Any]]:
        """
        上传 JSON 文件到 storage-service

        Args:
            file_path: JSON 文件路径
            object_name: MinIO 中的自定义对象路径

        Returns:
            成功返回 {"objectName": "...", ...}, 失败返回 None
        """
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return None

        base_url = self._get_service_url()
        if not base_url:
            logger.error("无法获取 storage-service 地址")
            return None

        url = f"{base_url}/storage/upload"

        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "application/json")}
                data = {"type": "json"}
                if object_name:
                    data["objectName"] = object_name
                response = requests.post(url, files=files, data=data, timeout=60)

            if response.status_code == 200:
                result = response.json()
                if str(result.get("code")) == "200":
                    logger.info(f"JSON 上传成功: {file_path.name} -> {result['data']['objectName']}")
                    return result["data"]
                else:
                    logger.error(f"JSON 上传失败: {result.get('message')}")
                    return None
            else:
                logger.error(f"JSON 上传请求失败: HTTP {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"JSON 上传异常: {e}")
            return None

    def upload_image(self, file_path: Path, object_name: str = None) -> Optional[Dict[str, Any]]:
        """
        上传图片文件到 storage-service

        Args:
            file_path: 图片文件路径
            object_name: MinIO 中的自定义对象路径

        Returns:
            成功返回 {"objectName": "...", ...}, 失败返回 None
        """
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return None

        base_url = self._get_service_url()
        if not base_url:
            logger.error("无法获取 storage-service 地址")
            return None

        url = f"{base_url}/storage/upload"

        try:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.name, f, "image/png")}
                data = {"type": "image"}
                if object_name:
                    data["objectName"] = object_name
                response = requests.post(url, files=files, data=data, timeout=60)

            if response.status_code == 200:
                result = response.json()
                if str(result.get("code")) == "200":
                    logger.info(f"图片上传成功: {file_path.name} -> {result['data']['objectName']}")
                    return result["data"]
                else:
                    logger.error(f"图片上传失败: {result.get('message')}")
                    return None
            else:
                logger.error(f"图片上传请求失败: HTTP {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"图片上传异常: {e}")
            return None


storage_client = StorageClient()
