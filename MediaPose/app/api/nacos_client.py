"""
Nacos 服务注册客户端
所有配置从 settings 读取，无硬编码

心跳使用独立进程（非线程），避免 MediaPipe CPU 密集计算时 GIL 阻塞心跳。
连续心跳失败时自动重新注册，防止 ephemeral 实例被 Nacos 删除后无法恢复。
"""
from ..core.config import settings

# 可选导入
try:
    import nacos
    NACOS_AVAILABLE = True
except ImportError:
    NACOS_AVAILABLE = False
    nacos = None

import socket
import multiprocessing
import time
import logging

logger = logging.getLogger(__name__)

# 心跳连续失败多少次后触发重新注册
RE_REGISTER_THRESHOLD = 3


def _heartbeat_process(stop_event, server_addr, namespace, username, password,
                       service_name, group, ip, port, version):
    """
    独立进程心跳循环 - 不受主进程 GIL 影响。
    连续失败超过阈值时自动重新注册实例。
    """
    if not NACOS_AVAILABLE:
        return

    client = nacos.NacosClient(
        server_addresses=server_addr,
        namespace=namespace,
        username=username or None,
        password=password or None,
    )

    metadata = {"version": version, "preserved_register_source": "SPRING_CLOUD"}
    fail_count = 0

    while not stop_event.is_set():
        try:
            client.send_heartbeat(
                service_name=service_name,
                ip=ip,
                port=port,
                group_name=group,
                cluster_name="DEFAULT",
                weight=1.0,
                metadata=metadata,
            )
            if fail_count > 0:
                print(f"[nacos-heartbeat] 心跳恢复 (之前连续失败 {fail_count} 次)")
            fail_count = 0
        except Exception as e:
            fail_count += 1
            print(f"[nacos-heartbeat] 心跳失败 ({fail_count}/{RE_REGISTER_THRESHOLD}): {e}")

            if fail_count >= RE_REGISTER_THRESHOLD:
                try:
                    print(f"[nacos-heartbeat] 尝试重新注册...")
                    client.add_naming_instance(
                        service_name=service_name,
                        ip=ip,
                        port=port,
                        group_name=group,
                        cluster_name="DEFAULT",
                        weight=1.0,
                        ephemeral=True,
                        healthy=True,
                        metadata=metadata,
                    )
                    print(f"[nacos-heartbeat] 重新注册成功")
                    fail_count = 0
                except Exception as re_reg_err:
                    print(f"[nacos-heartbeat] 重新注册失败: {re_reg_err}")

        stop_event.wait(5)


class NacosRegistry:
    """Nacos 服务注册器"""

    def __init__(self):
        self.client = None
        self.instance_id = None
        self.local_ip = None
        self._stop_event = None
        self._heartbeat_proc = None

    def nacos_available(self):
        """检查 Nacos 是否可用"""
        return NACOS_AVAILABLE and settings.NACOS_SERVER_ADDR

    def init_client(self):
        """初始化 Nacos 客户端"""
        if not self.nacos_available():
            logger.warning("Nacos SDK 未安装，跳过服务注册")
            return False

        if settings.NACOS_SERVER_ADDR:
            try:
                self.client = nacos.NacosClient(
                    server_addresses=settings.NACOS_SERVER_ADDR,
                    namespace=settings.NACOS_NAMESPACE,
                    username=settings.NACOS_USERNAME or None,
                    password=settings.NACOS_PASSWORD or None
                )
                logger.info(f"Nacos 客户端已初始化: {settings.NACOS_SERVER_ADDR}")
                return True
            except Exception as e:
                logger.error(f"Nacos 客户端初始化失败: {e}")
                return False
        return False

    def register_service(self):
        """注册服务到 Nacos"""
        if not self.nacos_available() or not self.client:
            logger.warning("Nacos 不可用，跳过服务注册")
            return False

        try:
            # 获取注册 IP：优先使用配置值，未配置则自动探测
            if settings.NACOS_SERVICE_IP:
                self.local_ip = settings.NACOS_SERVICE_IP
            else:
                hostname = socket.gethostname()
                self.local_ip = socket.gethostbyname(hostname)

            service_name = settings.NACOS_SERVICE_NAME
            group = settings.NACOS_GROUP

            # 注册服务实例
            self.instance_id = f"{self.local_ip}:{settings.PORT}"
            self.client.add_naming_instance(
                service_name=service_name,
                ip=self.local_ip,
                port=settings.PORT,
                group_name=group,
                cluster_name="DEFAULT",
                weight=1.0,
                ephemeral=True,
                healthy=True,
                metadata={
                    "version": settings.APP_VERSION,
                    "preserved_register_source": "SPRING_CLOUD"
                }
            )
            logger.info(f"服务已注册到 Nacos: {service_name} @ {self.local_ip}:{settings.PORT}")

            # 启动心跳进程
            self._start_heartbeat()

            return True
        except Exception as e:
            logger.error(f"服务注册失败: {e}")
            return False

    def _start_heartbeat(self):
        """启动独立心跳进程，不受主进程 GIL 阻塞"""
        if self._heartbeat_proc is not None and self._heartbeat_proc.is_alive():
            return

        self._stop_event = multiprocessing.Event()
        self._heartbeat_proc = multiprocessing.Process(
            target=_heartbeat_process,
            args=(
                self._stop_event,
                settings.NACOS_SERVER_ADDR,
                settings.NACOS_NAMESPACE,
                settings.NACOS_USERNAME or None,
                settings.NACOS_PASSWORD or None,
                settings.NACOS_SERVICE_NAME,
                settings.NACOS_GROUP,
                self.local_ip,
                settings.PORT,
                settings.APP_VERSION,
            ),
            daemon=True,
            name="nacos-heartbeat",
        )
        self._heartbeat_proc.start()
        logger.info(f"Nacos 心跳进程已启动 (pid={self._heartbeat_proc.pid})")

    def deregister_service(self):
        """从 Nacos 注销服务"""
        # 停止心跳进程
        if self._stop_event is not None:
            self._stop_event.set()
        if self._heartbeat_proc is not None and self._heartbeat_proc.is_alive():
            self._heartbeat_proc.join(timeout=3)
            if self._heartbeat_proc.is_alive():
                self._heartbeat_proc.terminate()

        if not self.nacos_available() or not self.client or not self.instance_id:
            return

        try:
            self.client.remove_naming_instance(
                service_name=settings.NACOS_SERVICE_NAME,
                ip=self.local_ip,
                port=settings.PORT,
                group_name=settings.NACOS_GROUP,
                cluster_name="DEFAULT"
            )
            logger.info(f"服务已从 Nacos 注销: {settings.NACOS_SERVICE_NAME}")
        except Exception as e:
            logger.error(f"服务注销失败: {e}")

    def get_service_instance(self, service_name: str) -> str:
        """
        从 Nacos 获取服务实例地址

        Args:
            service_name: 服务名称

        Returns:
            服务地址，格式: http://ip:port
            如果获取失败返回空字符串
        """
        if not self.nacos_available() or not self.client:
            logger.warning(f"Nacos 不可用，无法获取服务: {service_name}")
            return ""

        try:
            # 获取服务实例列表
            result = self.client.list_naming_instance(
                service_name=service_name,
                group_name=settings.NACOS_GROUP,
                healthy_only=True
            )

            hosts = result.get("hosts", [])
            if not hosts:
                logger.warning(f"未找到健康的服务实例: {service_name}")
                return ""

            # 选择第一个健康的实例
            instance = hosts[0]
            ip = instance.get("ip")
            port = instance.get("port")

            if ip and port:
                service_url = f"http://{ip}:{port}"
                logger.info(f"获取服务实例: {service_name} -> {service_url}")
                return service_url

            return ""

        except Exception as e:
            logger.error(f"获取服务实例失败: {service_name}, error: {e}")
            return ""


# 全局 Nacos 注册器
nacos_registry = NacosRegistry()


def setup_nacos_registry(app):
    """设置 Nacos 服务注册（在应用启动时调用）"""
    @app.on_event("startup")
    async def startup_event():
        nacos_registry.init_client()
        nacos_registry.register_service()

    @app.on_event("shutdown")
    async def shutdown_event():
        nacos_registry.deregister_service()
