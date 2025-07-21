import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaTimeoutError, KafkaConnectionError

from src.app.services import BackendKafkaProducer, KafkaPublishMessageFailed
from constant import MAX_RETRY, RETRY_DELAY, MESSAGE_TIMEOUT, ACK, RETRY_BACKOFF_MS

logger = logging.getLogger(__name__)


def json_serial(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


class AIOKafkaProducerImplementation(BackendKafkaProducer):
    """Async Kafka producer implementation using aiokafka"""
    
    def __init__(
        self, 
        servers: list, 
        topic: str, 
        ssl_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize Kafka producer
        
        Args:
            servers: List of kafka servers
            topic: Kafka topic name
            ssl_config: Optional SSL configuration
                Example: ssl_config = {
                    "security_protocol": "SASL_SSL",
                    "ssl_check_hostname": True,
                    "ssl_cafile": "/path/to/ca.pem",
                    "sasl_mechanism": "PLAIN",
                    "sasl_plain_username": "username",
                    "sasl_plain_password": "password",
                }
        """
        self.__topic = topic
        self.__max_retry = MAX_RETRY
        self.__delay = RETRY_DELAY
        
        config = {
            "bootstrap_servers": servers,
            "acks": ACK,
            "request_timeout_ms": MESSAGE_TIMEOUT * 1000,
            "retry_backoff_ms": RETRY_BACKOFF_MS,
        }
        
        if ssl_config:
            config.update(ssl_config)
        
        self.__producer = AIOKafkaProducer(**config)
        self.__started = False
    
    async def start(self) -> None:
        """Start the producer"""
        if not self.__started:
            await self.__producer.start()
            self.__started = True
            logger.info("Kafka producer started")
    
    async def stop(self) -> None:
        """Stop the producer"""
        if self.__started:
            await self.__producer.stop()
            self.__started = False
            logger.info("Kafka producer stopped")
    
    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        key: Optional[str] = None,
        issued_at: Optional[datetime] = None,
    ) -> None:
        """
        Publish a message to Kafka with retry logic
        
        Args:
            event_type: Type of the event
            payload: Event payload data
            key: Optional message key for partitioning
            issued_at: Optional timestamp, defaults to current time
            
        Raises:
            KafkaPublishMessageFailed: When message publishing fails after retries
        """
        if not self.__started:
            await self.start()
        
        retry_count = 0
        if not issued_at:
            issued_at = datetime.now(tz=timezone.utc)
        
        while True:
            message = {
                "event_type": event_type or "",
                "payload": payload or {},
                "issued_at": issued_at,
            }
            
            key_formatted = key.encode("utf-8") if key else None
            
            try:
                message_value = json.dumps(message, default=json_serial).encode("utf-8")
                
                # Send message and wait for acknowledgment
                future = await self.__producer.send(
                    topic=self.__topic,
                    value=message_value,
                    key=key_formatted
                )
                
                # Wait for the message to be sent
                record_metadata = await future
                logger.debug(
                    "Message sent to topic %s partition %d offset %d",
                    record_metadata.topic,
                    record_metadata.partition,
                    record_metadata.offset
                )
                break
                
            except (KafkaTimeoutError, KafkaConnectionError, ConnectionResetError) as e:
                if retry_count >= self.__max_retry:
                    logger.exception("Send message failed after %d retries - %s - %s", self.__max_retry, message, e)
                    raise KafkaPublishMessageFailed(f"Failed to send message after {self.__max_retry} retries: {e}") from e
                
                logger.warning("Send message failed - %s - %s", message, e)
                retry_count += 1
                logger.warning(
                    "Retry %d/%d in %d seconds for message - %s",
                    retry_count,
                    self.__max_retry,
                    self.__delay,
                    message,
                )
                await asyncio.sleep(self.__delay)
                
            except Exception as e:
                logger.exception("Send message failed with unexpected error - %s - %s", message, e)
                raise KafkaPublishMessageFailed(f"Unexpected error sending message: {e}") from e 