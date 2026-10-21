"""
MediaPose - 统一配置加载
所有配置从 config.yaml 读取
"""
import yaml
from pathlib import Path
from types import SimpleNamespace

BASE_DIR = Path(__file__).parent.parent.parent

# 默认配置
_DEFAULTS = {
    "server": {
        "app_name": "MediaPose",
        "app_version": "1.0.0",
        "host": "0.0.0.0",
        "port": 8009,
    },
    "nacos": {
        "server_addr": "127.0.0.1:8848",
        "namespace": "",
        "group": "DEFAULT_GROUP",
        "username": "",
        "password": "",
        "service_name": "baseball-pose-analyst",
        "storage_service_name": "storage-service",
        "service_ip": "",
    },
    "storage": {
        "fallback_url": "http://localhost:8004",
    },
    "rabbitmq": {
        "url": "amqp://guest:guest@localhost:5672/",
        "exchange": "analysis-exchange",
        "request_queue": "analysis-request",
        "completed_queue": "analysis-completed",
        "failed_queue": "analysis-failed",
        "routing_key_request": "request",
        "routing_key_completed": "completed",
        "routing_key_failed": "failed",
    },
    "mediapipe": {
        "model_complexity": 1,
        "min_detection_confidence": 0.5,
        "min_tracking_confidence": 0.5,
        "static_image_mode": False,
    },
    "analysis": {
        "fps": 30,
        "smoothing_window": 5,
        "swing_threshold": 0.3,
        "twist_threshold": 15.0,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并两个字典，override 覆盖 base"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_config() -> dict:
    """加载 config.yaml，与默认配置合并"""
    config_path = BASE_DIR / "config.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
        return _deep_merge(_DEFAULTS, user_config)
    return _DEFAULTS.copy()


_cfg = _load_config()

# ===== 扁平化访问接口（保持与旧 settings 兼容） =====
settings = SimpleNamespace(
    # 服务
    APP_NAME=_cfg["server"]["app_name"],
    APP_VERSION=_cfg["server"]["app_version"],
    HOST=_cfg["server"]["host"],
    PORT=_cfg["server"]["port"],

    # Nacos
    NACOS_SERVER_ADDR=_cfg["nacos"]["server_addr"],
    NACOS_NAMESPACE=_cfg["nacos"]["namespace"],
    NACOS_GROUP=_cfg["nacos"]["group"],
    NACOS_USERNAME=_cfg["nacos"]["username"],
    NACOS_PASSWORD=_cfg["nacos"]["password"],
    NACOS_SERVICE_NAME=_cfg["nacos"]["service_name"],
    NACOS_STORAGE_SERVICE_NAME=_cfg["nacos"]["storage_service_name"],
    NACOS_SERVICE_IP=_cfg["nacos"]["service_ip"],

    # Storage
    STORAGE_SERVICE_URL=_cfg["storage"]["fallback_url"],

    # RabbitMQ
    RABBITMQ_URL=_cfg["rabbitmq"]["url"],
    RABBITMQ_EXCHANGE=_cfg["rabbitmq"]["exchange"],
    RABBITMQ_REQUEST_QUEUE=_cfg["rabbitmq"]["request_queue"],
    RABBITMQ_COMPLETED_QUEUE=_cfg["rabbitmq"]["completed_queue"],
    RABBITMQ_FAILED_QUEUE=_cfg["rabbitmq"]["failed_queue"],
    RABBITMQ_ROUTING_KEY_REQUEST=_cfg["rabbitmq"]["routing_key_request"],
    RABBITMQ_ROUTING_KEY_COMPLETED=_cfg["rabbitmq"]["routing_key_completed"],
    RABBITMQ_ROUTING_KEY_FAILED=_cfg["rabbitmq"]["routing_key_failed"],

    # MediaPipe
    MODEL_COMPLEXITY=_cfg["mediapipe"]["model_complexity"],
    MIN_DETECTION_CONFIDENCE=_cfg["mediapipe"]["min_detection_confidence"],
    MIN_TRACKING_CONFIDENCE=_cfg["mediapipe"]["min_tracking_confidence"],
    STATIC_IMAGE_MODE=_cfg["mediapipe"]["static_image_mode"],

    # 分析
    FPS=_cfg["analysis"]["fps"],
    SMOOTHING_WINDOW=_cfg["analysis"]["smoothing_window"],
    SWING_THRESHOLD=_cfg["analysis"]["swing_threshold"],
    TWIST_THRESHOLD=_cfg["analysis"]["twist_threshold"],

    # 路径
    BASE_DIR=BASE_DIR,
    UPLOAD_DIR=BASE_DIR / "temp" / "uploads",
    TEMP_DIR=BASE_DIR / "temp",
    OUTPUT_DIR=BASE_DIR / "temp" / "outputs",
)

# 创建必要的目录
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.TEMP_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
