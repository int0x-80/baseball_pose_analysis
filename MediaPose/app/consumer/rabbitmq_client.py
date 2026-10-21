#!/usr/bin/env python3
"""
RabbitMQ 客户端模块
所有配置从 settings 读取，无硬编码
"""
import pika
import json
import logging
from typing import Callable, Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """RabbitMQ 客户端类，用于连接和管理 RabbitMQ 消息队列"""

    def __init__(self, url: str = None):
        """
        初始化 RabbitMQ 客户端

        Args:
            url: RabbitMQ 连接 URL，默认从 settings 读取
        """
        self.url = url or settings.RABBITMQ_URL
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None

    def connect(self) -> bool:
        """
        连接到 RabbitMQ 服务器

        Returns:
            bool: 连接是否成功
        """
        try:
            self.connection = pika.BlockingConnection(pika.URLParameters(self.url))
            self.channel = self.connection.channel()
            logger.info("RabbitMQ 连接成功")

            exchange = settings.RABBITMQ_EXCHANGE

            # 声明交换机
            self.channel.exchange_declare(
                exchange=exchange,
                exchange_type='direct',
                durable=True
            )

            # 声明队列
            self.channel.queue_declare(settings.RABBITMQ_REQUEST_QUEUE, durable=True)
            self.channel.queue_declare(settings.RABBITMQ_COMPLETED_QUEUE, durable=True)
            self.channel.queue_declare(settings.RABBITMQ_FAILED_QUEUE, durable=True)

            # 绑定队列到交换机
            self.channel.queue_bind(
                queue=settings.RABBITMQ_REQUEST_QUEUE,
                exchange=exchange,
                routing_key=settings.RABBITMQ_ROUTING_KEY_REQUEST
            )
            self.channel.queue_bind(
                queue=settings.RABBITMQ_COMPLETED_QUEUE,
                exchange=exchange,
                routing_key=settings.RABBITMQ_ROUTING_KEY_COMPLETED
            )
            self.channel.queue_bind(
                queue=settings.RABBITMQ_FAILED_QUEUE,
                exchange=exchange,
                routing_key=settings.RABBITMQ_ROUTING_KEY_FAILED
            )

            logger.info("交换机和队列声明并绑定成功")
            return True

        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"RabbitMQ 连接失败: {e}")
            return False
        except Exception as e:
            logger.error(f"初始化 RabbitMQ 时出错: {e}")
            return False

    def publish_message(self, queue: str, message: Dict[str, Any], routing_key: str = None) -> bool:
        """
        发布消息到指定队列

        Args:
            queue: 目标队列名称
            message: 要发送的消息（字典）
            routing_key: 路由键，如果为 None 则使用队列名称

        Returns:
            bool: 消息是否发送成功
        """
        if not self.channel:
            logger.error("未连接到 RabbitMQ")
            return False

        try:
            if routing_key is None:
                routing_key = queue

            self.channel.basic_publish(
                exchange=settings.RABBITMQ_EXCHANGE,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # 消息持久化
                    content_type='application/json'
                )
            )
            logger.info(f"消息已发送到 {queue}")
            return True

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False

    def consume(self, queue: str, callback: Callable, auto_ack: bool = False) -> None:
        """
        开始消费指定队列的消息

        Args:
            queue: 要消费的队列名称
            callback: 消息处理回调函数
            auto_ack: 是否自动确认消息
        """
        if not self.channel:
            logger.error("未连接到 RabbitMQ")
            return

        try:
            # 设置预取数量，确保公平分发
            self.channel.basic_qos(prefetch_count=1)

            self.channel.basic_consume(
                queue=queue,
                on_message_callback=callback,
                auto_ack=auto_ack
            )

            logger.info(f"开始消费队列: {queue}")
            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("收到中断信号，停止消费")
            self.channel.stop_consuming()
        except Exception as e:
            logger.error(f"消费消息时出错: {e}")

    def ack_message(self, ch: pika.channel.Channel, method_frame: pika.spec.Basic.Deliver) -> None:
        """确认消息"""
        ch.basic_ack(delivery_tag=method_frame.delivery_tag)

    def nack_message(self, ch: pika.channel.Channel, method_frame: pika.spec.Basic.Deliver, requeue: bool = False) -> None:
        """拒绝消息"""
        ch.basic_nack(delivery_tag=method_frame.delivery_tag, requeue=requeue)

    def close(self) -> None:
        """关闭 RabbitMQ 连接"""
        if self.connection and self.connection.is_open:
            self.connection.close()
            logger.info("RabbitMQ 连接已关闭")

    def is_connected(self) -> bool:
        """检查是否已连接到 RabbitMQ"""
        return self.connection is not None and self.connection.is_open
